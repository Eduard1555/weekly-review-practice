import os
import sqlite3
from pathlib import Path

DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent / "weekly_review.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS lawyers (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS clients (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS matters (
    id INTEGER PRIMARY KEY,
    client_id INTEGER NOT NULL REFERENCES clients(id),
    name TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'open' CHECK (status IN ('open', 'closed')),
    opened_on TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS time_entries (
    id INTEGER PRIMARY KEY,
    lawyer_id INTEGER NOT NULL REFERENCES lawyers(id),
    matter_id INTEGER REFERENCES matters(id),
    entry_date TEXT NOT NULL,
    hours REAL NOT NULL CHECK (hours > 0),
    billable INTEGER NOT NULL DEFAULT 1,
    description TEXT NOT NULL DEFAULT ''
);

CREATE INDEX IF NOT EXISTS idx_entries_date ON time_entries(entry_date);
"""


def get_db_path() -> Path:
    return Path(os.environ.get("WEEKLY_REVIEW_DB", DEFAULT_DB_PATH))


def connect(path: Path | str | None = None) -> sqlite3.Connection:
    conn = sqlite3.connect(path or get_db_path(), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA)
    conn.commit()


def reset_db(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        DROP TABLE IF EXISTS time_entries;
        DROP TABLE IF EXISTS matters;
        DROP TABLE IF EXISTS clients;
        DROP TABLE IF EXISTS lawyers;
        """
    )
    init_db(conn)
