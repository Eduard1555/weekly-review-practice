import pytest
from fastapi.testclient import TestClient

from app import db


@pytest.fixture
def db_path(tmp_path, monkeypatch):
    path = tmp_path / "test.db"
    monkeypatch.setenv("WEEKLY_REVIEW_DB", str(path))
    return path


@pytest.fixture
def conn(db_path):
    connection = db.connect(db_path)
    db.init_db(connection)
    yield connection
    connection.close()


@pytest.fixture
def client(conn):
    from app.main import app

    with TestClient(app) as test_client:
        yield test_client


class Factory:
    def __init__(self, conn):
        self.conn = conn

    def lawyer(self, name):
        cur = self.conn.execute("INSERT INTO lawyers (name) VALUES (?)", (name,))
        self.conn.commit()
        return cur.lastrowid

    def client(self, name):
        cur = self.conn.execute("INSERT INTO clients (name) VALUES (?)", (name,))
        self.conn.commit()
        return cur.lastrowid

    def matter(self, client_id, name, status="open", opened_on="2026-01-01"):
        cur = self.conn.execute(
            "INSERT INTO matters (client_id, name, status, opened_on) VALUES (?, ?, ?, ?)",
            (client_id, name, status, opened_on),
        )
        self.conn.commit()
        return cur.lastrowid

    def entry(self, lawyer_id, matter_id, entry_date, hours, billable=True, description=""):
        cur = self.conn.execute(
            """
            INSERT INTO time_entries (lawyer_id, matter_id, entry_date, hours, billable, description)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (lawyer_id, matter_id, entry_date, hours, int(billable), description),
        )
        self.conn.commit()
        return cur.lastrowid


@pytest.fixture
def make(conn):
    return Factory(conn)
