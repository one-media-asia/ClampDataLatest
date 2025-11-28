#!/usr/bin/env python3
"""
One-time migration script: add `registration` column to `clamp_data` table

Usage:
    python migrate_db.py

This script is safe to run multiple times: it checks whether the column
already exists before altering the table.
"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'instance', 'clamping_business.db')

def column_exists(conn, table, column):
    cur = conn.execute(f"PRAGMA table_info('{table}')")
    cols = [row[1] for row in cur.fetchall()]
    return column in cols

def add_registration_column(conn):
    if column_exists(conn, 'clamp_data', 'registration'):
        print('Column `registration` already exists on clamp_data — nothing to do.')
        return

    print('Adding `registration` column to clamp_data...')
    conn.execute("ALTER TABLE clamp_data ADD COLUMN registration TEXT")
    conn.commit()
    print('Done.')

def main():
    if not os.path.exists(DB_PATH):
        print(f"Database file not found at {DB_PATH}. Are you in the right folder?")
        return

    conn = sqlite3.connect(DB_PATH)
    try:
        add_registration_column(conn)
    finally:
        conn.close()

if __name__ == '__main__':
    main()
