#!/usr/bin/env python3
"""
Simple migration script for SQLite: add `force_password_change` column to `user` table if missing.
Run from project root (or this folder) with the same working dir as the app.
"""
import sqlite3
import os
import sys

DB_PATH = os.environ.get('CLAMPING_DB_PATH', 'clamping_business.db')

def column_exists(conn, table, column):
    cur = conn.execute(f"PRAGMA table_info('{table}')")
    cols = [r[1] for r in cur.fetchall()]
    return column in cols


def main():
    if not os.path.exists(DB_PATH):
        print(f"Database file not found: {DB_PATH}")
        sys.exit(1)
    conn = sqlite3.connect(DB_PATH)
    try:
        if column_exists(conn, 'user', 'force_password_change'):
            print('Column `force_password_change` already exists on table `user`. No action taken.')
            return
        print('Adding column `force_password_change` to table `user`...')
        # SQLite supports ADD COLUMN with a default value
        conn.execute("ALTER TABLE user ADD COLUMN force_password_change INTEGER DEFAULT 0")
        conn.commit()
        print('Column added successfully.')
    except sqlite3.OperationalError as e:
        print('SQLite OperationalError:', e)
        print('You may need to inspect the database schema or run a more complex migration.')
        raise
    finally:
        conn.close()

if __name__ == '__main__':
    main()
