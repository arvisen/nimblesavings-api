"""
Lightweight persistence for the watchlist feature.

Uses stdlib sqlite3 rather than a full ORM/Postgres setup — this is the
"Stage 2" database mentioned in the README, kept intentionally simple.
A single file (babyprice.db) is created next to wherever the app runs.
Swap this out for Postgres later without changing the calling code much
(the query shapes stay the same, just the connection/driver changes).
"""

import sqlite3
from contextlib import contextmanager
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent.parent / "babyprice.db"


def init_db() -> None:
    with get_conn() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS watchlist (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL,
                product_id TEXT NOT NULL,
                title TEXT NOT NULL,
                target_price REAL,               -- optional; NULL means "alert on any drop"
                last_seen_price REAL,             -- updated each time the scheduler checks
                last_notified_price REAL,          -- avoids spamming the same drop repeatedly
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.commit()


@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()
