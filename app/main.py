import sqlite3
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app import db
from app.models import Entry, EntryIn, Lawyer, Matter, WeeklyReview
from app.report import build_review
from app.weeks import parse_week_of

STATIC_DIR = Path(__file__).resolve().parent.parent / "static"


@asynccontextmanager
async def lifespan(_: FastAPI):
    conn = db.connect()
    db.init_db(conn)
    conn.close()
    yield


app = FastAPI(title="Weekly Review", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


def get_conn():
    conn = db.connect()
    try:
        yield conn
    finally:
        conn.close()


def _week_or_400(week_of: str | None):
    try:
        return parse_week_of(week_of)
    except ValueError:
        raise HTTPException(status_code=400, detail="week_of must be a date in YYYY-MM-DD format")


@app.get("/", include_in_schema=False)
def index():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/review", response_model=WeeklyReview)
def weekly_review(
    week_of: str | None = Query(default=None, description="Any date inside the week, YYYY-MM-DD"),
    conn: sqlite3.Connection = Depends(get_conn),
):
    return build_review(conn, _week_or_400(week_of))


@app.get("/api/lawyers", response_model=list[Lawyer])
def list_lawyers(conn: sqlite3.Connection = Depends(get_conn)):
    rows = conn.execute("SELECT id, name FROM lawyers ORDER BY name").fetchall()
    return [dict(row) for row in rows]


@app.get("/api/matters", response_model=list[Matter])
def list_matters(conn: sqlite3.Connection = Depends(get_conn)):
    rows = conn.execute(
        """
        SELECT m.id, m.name, c.name AS client, m.status
        FROM matters m JOIN clients c ON c.id = m.client_id
        ORDER BY c.name, m.name
        """
    ).fetchall()
    return [dict(row) for row in rows]


@app.get("/api/entries", response_model=list[Entry])
def list_entries(
    week_of: str | None = Query(default=None),
    conn: sqlite3.Connection = Depends(get_conn),
):
    week = _week_or_400(week_of)
    rows = conn.execute(
        """
        SELECT id, lawyer_id, matter_id, entry_date, hours, billable, description
        FROM time_entries
        WHERE entry_date BETWEEN ? AND ?
        ORDER BY entry_date, id
        """,
        (week.start.isoformat(), week.end.isoformat()),
    ).fetchall()
    return [dict(row) for row in rows]


@app.post("/api/entries", response_model=Entry, status_code=201)
def create_entry(entry: EntryIn, conn: sqlite3.Connection = Depends(get_conn)):
    lawyer = conn.execute("SELECT id FROM lawyers WHERE id = ?", (entry.lawyer_id,)).fetchone()
    if lawyer is None:
        raise HTTPException(status_code=404, detail="Lawyer not found")

    billable = entry.billable
    if entry.matter_id is None:
        billable = False
    else:
        matter = conn.execute(
            "SELECT status FROM matters WHERE id = ?", (entry.matter_id,)
        ).fetchone()
        if matter is None:
            raise HTTPException(status_code=404, detail="Matter not found")
        if matter["status"] != "open":
            raise HTTPException(status_code=400, detail="Time cannot be logged to a closed matter")

    cur = conn.execute(
        """
        INSERT INTO time_entries (lawyer_id, matter_id, entry_date, hours, billable, description)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            entry.lawyer_id,
            entry.matter_id,
            entry.entry_date.isoformat(),
            entry.hours,
            int(billable),
            entry.description,
        ),
    )
    conn.commit()
    return {
        "id": cur.lastrowid,
        "lawyer_id": entry.lawyer_id,
        "matter_id": entry.matter_id,
        "entry_date": entry.entry_date,
        "hours": entry.hours,
        "billable": billable,
        "description": entry.description,
    }
