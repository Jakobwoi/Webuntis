#!/usr/bin/env python3

import login_config as config

import asyncio
import datetime
import sys
import mysql.connector 
from webuntis_api import WebUntisClient



def init_db(corser):
    corser.execute("""-- sql
            CREATE DATABASE IF NOT EXISTS webuntis;
            USE webuntis;
        """)
    corser.execute("""-- sql
            CREATE TABLE IF NOT EXISTS classes (
                id INT AUTO_INCREMENT PRIMARY KEY,
                short_name VARCHAR(255) NOT NULL,
                long_name VARCHAR(255),
                external_key VARCHAR(255),
                fetched_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            ) WITH SYSTEM VERSIONING;
            CREATE TABLE IF NOT EXISTS subjects (
                id INT AUTO_INCREMENT PRIMARY KEY,
                short_name VARCHAR(255) NOT NULL,
                long_name VARCHAR(255)
            ) WITH SYSTEM VERSIONING;
            CREATE TABLE IF NOT EXISTS teachers (
                id INT AUTO_INCREMENT PRIMARY KEY,
                short_name VARCHAR(255) NOT NULL,
                long_name VARCHAR(255)
            ) WITH SYSTEM VERSIONING;
            CREATE TABLE IF NOT EXISTS rooms (
                id INT AUTO_INCREMENT PRIMARY KEY,
                short_name VARCHAR(255) NOT NULL,
                long_name VARCHAR(255)
            ) WITH SYSTEM VERSIONING;
            CREATE TABLE IF NOT EXISTS timetable_entries (
                id INT AUTO_INCREMENT PRIMARY KEY,
                upstream_id INT NOT NULL,
                class_id INT NOT NULL,
                date DATE NOT NULL,
                period_start TIME NOT NULL,
                period_end TIME NOT NULL,
                type VARCHAR(255) NOT NULL,
                status VARCHAR(255) NOT NULL,
                status_detail VARCHAR(255),
                subject INT,
                teacher INT,
                room INT,
                fetched_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (subject) REFERENCES subjects(id),
                FOREIGN KEY (teacher) REFERENCES teachers(id),
                FOREIGN KEY (room) REFERENCES rooms(id),
                FOREIGN KEY (class_id) REFERENCES classes(id)
            ) WITH SYSTEM VERSIONING;
            CREATE TABLE IF NOT EXISTS last_update (
                id INT PRIMARY KEY CHECK (id = 1),
                last_update_timestamp TIMESTAMP NOT NULL,
                checked_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            ) WITH SYSTEM VERSIONING;

            CREATE INDEX IF NOT EXISTS idx_timetable_class_date
                ON timetable_entries(class_id, date);
            CREATE INDEX IF NOT EXISTS idx_timetable_fetched
                ON timetable_entries(fetched_at) WITH SYSTEM VERSIONING;
        """)

def store_timetable_entries(corser, class_id, entries):
        for e in entries:
            # TODO: insert in db
            teacher_id = None
            subject_id = None
            room_id = None
            if e.get('teacher'):
                corser.execute(
                    "INSERT INTO teachers (short_name, long_name) VALUES (%s, %s) ON DUPLICATE KEY UPDATE id = LAST_INSERT_ID(id)",
                    (e.get('teacher'), e.get('teacherLong'))
                )
                teacher_id = corser.lastrowid
            if e.get('subject'):
                corser.execute(
                    "INSERT INTO subjects (short_name, long_name) VALUES (%s, %s) ON DUPLICATE KEY UPDATE id = LAST_INSERT_ID(id)",
                    (e.get('subject'), e.get('subjectLong'))
                )
                subject_id = corser.lastrowid
            if e.get('room'):
                corser.execute(
                    "INSERT INTO rooms (short_name, long_name) VALUES (%s, %s) ON DUPLICATE KEY UPDATE id = LAST_INSERT_ID(id)",
                    (e.get('room'), e.get('roomLong'))
                )
                room_id = corser.lastrowid
            corser.execute(
                "SELECT id FROM timetable_entries WHERE upstream_id = %s AND class_id = %s",
                (e.get('upstreamId'), class_id)
            )
            if corser.fetchone():
                sql = """-- sql\n UPDATE timetable_entries SET date = %s, period_start = %s, period_end = %s, type = %s, status = %s, status_detail = %s, subject = %s, teacher = %s, room = %s WHERE upstream_id = %s AND class_id = %s
                """
            else:
                sql = """-- sql\n INSERT INTO timetable_entries (upstream_id, class_id, date, period_start, period_end, type, status, status_detail, subject, teacher, room) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
            corser.execute(sql, (
                e.get('upstreamId'),
                class_id,
                e['date'],
                e['startTime'],
                e['endTime'],
                e['type'],
                e['status'],
                e.get('statusDetail'),
                subject_id,
                teacher_id,
                room_id
            ))
            continue

def get_stored_last_update(corser):
    row = corser.execute(
        "SELECT last_update_timestamp FROM last_update WHERE id = 1"
    ).fetchone()
    return datetime.datetime.fromisoformat(row[0]) if row else None

def set_stored_last_update(corser, dt):
    corser.execute(
        "INSERT OR REPLACE INTO last_update (id, last_update_timestamp) VALUES (1, ?)",
        (dt.isoformat(),),
    )

def fetch_and_store_class_timetable(corser, untis_client, class_id, start_date, end_date):
    # Fetch timetable from WebUntis API
    raw_data = untis_client.get_raw_timetable_rest_class(class_id, start_date, end_date)
    
    flat_entries = []
    for day in raw_data.get('days', []):
        for entry in day.get('gridEntries', []):
            parsed = {}
            for pos_num in range(1, 8):
                untis_client.parse_positionx(entry.get(f'position{pos_num}', []), parsed)
            dur = entry.get('duration', {})
            flat_entries.append({
                'upstreamId': (entry.get('ids') or [None])[0],
                'date': day['date'],
                'startTime': dur.get('start'),
                'endTime': dur.get('end'),
                'type': entry.get('type'),
                'status': entry.get('status'),
                'statusDetail': entry.get('statusDetail'),
                'teacher': (parsed.get('teacherShort') or [None])[0],
                'teacherLong': (parsed.get('teacher') or [None])[0],
                'subject': parsed.get('subject'),
                'subjectLong': parsed.get('subjectLong'),
                'room': parsed.get('room'),
                'roomLong': parsed.get('roomLong'),
            })
    
    store_timetable_entries(corser, class_id, flat_entries)
def fetch_and_store_timetable(corser, untis_client, start_date, end_date):
    classes = untis_client.get_classes()
    for class_info in classes.get("result", []):
        class_id = class_info['id']
        fetch_and_store_class_timetable(corser, untis_client, class_id, start_date, end_date)

async def main():
    conn = mysql.connector.connect(
        host=config.DB_HOST,
        user=config.DB_USER,
        password=config.DB_PASSWORD
    )
    untis_client = WebUntisClient(config.SCHOOL, config.SERVER_URL, config.USERNAME, config.KEY)
    corser = conn.cursor()
    today = datetime.date.today()
    monday = today - datetime.timedelta(days=today.weekday())
    friday = monday + datetime.timedelta(days=4)
    init_db(corser)
    fetch_and_store_timetable(corser, untis_client, monday, friday)
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
