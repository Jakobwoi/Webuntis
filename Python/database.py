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
                    "INSERT INTO teachers (short_name, long_name) VALUES (%s, %s) ON DUPLICATE SELECT id FROM teachers WHERE short_name = %s",
                    (e['teacher'], e.get('teacherLong'), e['teacher'])
                )
                if corser.lastrowid:
                    teacher_id = corser.lastrowid
                else:
                    teacher_id =  corser.fetchone()[0]
            if e.get('subject'):
                corser.execute(
                    "INSERT INTO subjects (short_name, long_name) VALUES (%s, %s) ON DUPLICATE SELECT id FROM subjects WHERE short_name = %s",
                    (e['subject'], e.get('subjectLong'), e['subject'])
                )
                if corser.lastrowid:
                    subject_id = corser.lastrowid
                else:
                    subject_id =  corser.fetchone()[0]
            if e.get('room'):
                corser.execute(
                    "INSERT INTO rooms (short_name, long_name) VALUES (%s, %s) ON DUPLICATE SELECT id FROM rooms WHERE short_name = %s",
                    (e['room'], e.get('roomLong'), e['room'])
                )
                if corser.lastrowid:
                    room_id = corser.lastrowid
                else:
                    room_id =  corser.fetchone()[0]
            sql = """-- sql\n INSERT INTO timetable_entries (class_id, date, period_start, period_end, type, status, status_detail, subject, teacher, room) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            corser.execute(sql, (
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


async def main():
    conn = mysql.connector.connect(
        host=config.DB_HOST,
        user=config.DB_USER,
        password=config.DB_PASSWORD,
        database=config.DB_NAME
    )
    corser = conn.cursor()
    init_db(corser)
    print(corser)
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
