#!/usr/bin/env python3


import asyncio
import datetime
import sys

import webuntis_api as webuntis


def init_db(conn):
    conn.executescript("""--sql
            CREATE TABLE IF NOT EXISTS classes (
                id INTEGER PRIMARY KEY,
                short_name TEXT NOT NULL,
                long_name TEXT,
                external_key TEXT,
                fetched_at TEXT NOT NULL DEFAULT (datetime('now'))
            );
            CREATE TABLE IF NOT EXISTS subjects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                short_name TEXT NOT NULL,
                long_name TEXT
            );
            CREATE TABLE IF NOT EXISTS teachers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                short_name TEXT NOT NULL,
                long_name TEXT
            );
            CREATE TABLE IF NOT EXISTS rooms (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                short_name TEXT NOT NULL,
                long_name TEXT
            );
            CREATE TABLE IF NOT EXISTS timetable_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                class_id INTEGER NOT NULL,
                date TEXT NOT NULL,
                period_start TEXT NOT NULL,
                period_end TEXT NOT NULL,
                type TEXT NOT NULL,
                status TEXT NOT NULL,
                status_detail TEXT,
                subject INTEGER,
                teacher INTEGER,
                room INTEGER,
                fetched_at TEXT NOT NULL DEFAULT (datetime('now')),
                FOREIGN KEY (subject) REFERENCES subjects(id),
                FOREIGN KEY (teacher) REFERENCES teachers(id),
                FOREIGN KEY (room) REFERENCES rooms(id),
                FOREIGN KEY (class_id) REFERENCES classes(id)
            );
            CREATE TABLE IF NOT EXISTS timetable_changes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lesson_id INTEGER NOT NULL,
                change_type TEXT NOT NULL,
                change_time TIMESTAMP NOT NULL,
                old_type TEXT,
                old_status TEXT,
                old_status_detail TEXT,
                old_subject INTEGER,
                old_teacher INTEGER,
                old_room INTEGER,
                new_type TEXT,
                new_status TEXT,
                new_status_detail TEXT,
                new_subject INTEGER,
                new_teacher INTEGER,
                new_room INTEGER,
                FOREIGN KEY (lesson_id) REFERENCES timetable_entries(id)
            );
            CREATE TABLE IF NOT EXISTS last_update (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                last_update_timestamp TEXT NOT NULL,
                checked_at TEXT NOT NULL DEFAULT (datetime('now'))
            );

            CREATE INDEX IF NOT EXISTS idx_timetable_class_date
                ON timetable_entries(class_id, date);
            CREATE INDEX IF NOT EXISTS idx_timetable_fetched
                ON timetable_entries(fetched_at);
        """)
    conn.commit()


def store_classes(conn, classes):
        for c in classes:
            # TODO: insert in db
            continue


def store_timetable_entries(conn, class_id, entries):
        for e in entries:
            # TODO: insert in db
            continue


def get_stored_last_update(conn):
    row = conn.execute(
        "SELECT last_update_timestamp FROM last_update WHERE id = 1"
    ).fetchone()
    return datetime.datetime.fromisoformat(row[0]) if row else None


def set_stored_last_update(conn, dt):
    conn.execute(
        "INSERT OR REPLACE INTO last_update (id, last_update_timestamp) VALUES (1, ?)",
        (dt.isoformat(),),
    )
    conn.commit()


async def main():
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
