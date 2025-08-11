import os
import sqlite3
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
DB_PATH = "quotes.db"

try:
    # Step 1: Delete the old DB (optional)
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
        logging.info(f"Deleted old database: {DB_PATH}")

    # Step 2: Create new DB and schema
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")  # Enforce FK constraints

    # Step 3: Create sessions table with correct schema
    conn.execute("""
    CREATE TABLE IF NOT EXISTS sessions (
        session_id TEXT PRIMARY KEY,
        broker TEXT NOT NULL,
        symbol TEXT NOT NULL,
        archive_name TEXT NOT NULL,
        start_time INTEGER NOT NULL,
        end_time INTEGER NOT NULL
    );
    """)

    # Step 4: Create quotes table with FK to session_id
    conn.execute("""
    CREATE TABLE IF NOT EXISTS quotes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT NOT NULL,
        timestamp INTEGER NOT NULL,
        bid REAL NOT NULL,
        ask REAL NOT NULL,
        FOREIGN KEY(session_id) REFERENCES sessions(session_id),
        UNIQUE(session_id, timestamp) ON CONFLICT REPLACE
    );
    """)

    conn.commit()
    logging.info(f"Fresh database created: {DB_PATH}")
except Exception as e:
    logging.error(f"Error resetting database: {e}", exc_info=True)
finally:
    if 'conn' in locals():
        conn.close()
