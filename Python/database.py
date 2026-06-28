#!/usr/bin/env python3

import login_config as config

import asyncio
import datetime
import sys
import mysql.connector 
import webuntis_api as webuntis



def init_db(corser):
    corser.execute("""-- sql
            CREATE TABLE IF NOT EXISTS classes (
                id INT AUTO_INCREMENT PRIMARY KEY,
                short_name VARCHAR(255) NOT NULL,
                long_name VARCHAR(255),
                external_key VARCHAR(255),
                fetched_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS subjects (
                id INT AUTO_INCREMENT PRIMARY KEY,
                short_name VARCHAR(255) NOT NULL,
                long_name VARCHAR(255)
            );
            CREATE TABLE IF NOT EXISTS teachers (
                id INT AUTO_INCREMENT PRIMARY KEY,
                short_name VARCHAR(255) NOT NULL,
                long_name VARCHAR(255)
            );
            CREATE TABLE IF NOT EXISTS rooms (
                id INT AUTO_INCREMENT PRIMARY KEY,
                short_name VARCHAR(255) NOT NULL,
                long_name VARCHAR(255)
            );
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
            );
            CREATE TABLE IF NOT EXISTS timetable_changes (
                id INT AUTO_INCREMENT PRIMARY KEY,
                lesson_id INT NOT NULL,
                change_type VARCHAR(255) NOT NULL,
                change_time TIMESTAMP NOT NULL,
                old_type VARCHAR(255),
                old_status VARCHAR(255),
                old_status_detail VARCHAR(255),
                old_subject INT,
                old_teacher INT,
                old_room INT,
                new_type VARCHAR(255),
                new_status VARCHAR(255),
                new_status_detail VARCHAR(255),
                new_subject INT,
                new_teacher INT,
                new_room INT,
                FOREIGN KEY (lesson_id) REFERENCES timetable_entries(id)
            );
            CREATE TABLE IF NOT EXISTS last_update (
                id INT PRIMARY KEY CHECK (id = 1),
                last_update_timestamp TIMESTAMP NOT NULL,
                checked_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE INDEX IF NOT EXISTS idx_timetable_class_date
                ON timetable_entries(class_id, date);
            CREATE INDEX IF NOT EXISTS idx_timetable_fetched
                ON timetable_entries(fetched_at);
        """)


def store_lessons(corser, lessons):
        for c in lessons:
            # TODO: insert in db
            continue


def store_timetable_entries(corser, class_id, entries):
        for e in entries:
            # TODO: insert in db
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
