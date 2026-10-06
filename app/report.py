import sqlite3

from app.weeks import Week


def _round(value: float | None) -> float:
    return round(value or 0.0, 2)


def hours_by_lawyer(conn: sqlite3.Connection, week: Week) -> list[dict]:
    rows = conn.execute(
        """
        SELECT l.id AS lawyer_id,
               l.name AS lawyer,
               SUM(e.hours) AS hours,
               SUM(CASE WHEN e.billable = 1 THEN e.hours ELSE 0 END) AS billable_hours
        FROM time_entries e
        JOIN lawyers l ON l.id = e.lawyer_id
        WHERE e.entry_date >= ? AND e.entry_date < ?
        GROUP BY l.id
        ORDER BY l.name
        """,
        (week.start.isoformat(), week.end.isoformat()),
    ).fetchall()

    result = []
    for row in rows:
        hours = _round(row["hours"])
        billable = _round(row["billable_hours"])
        result.append(
            {
                "lawyer_id": row["lawyer_id"],
                "lawyer": row["lawyer"],
                "hours": hours,
                "billable_hours": billable,
                "non_billable_hours": _round(hours - billable),
            }
        )
    return result


def hours_by_matter(conn: sqlite3.Connection, week: Week) -> dict[str, dict]:
    rows = conn.execute(
        """
        SELECT m.id AS matter_id,
               m.name AS matter,
               c.name AS client,
               SUM(e.hours) AS hours,
               SUM(CASE WHEN e.billable = 1 THEN e.hours ELSE 0 END) AS billable_hours
        FROM time_entries e
        JOIN matters m ON m.id = e.matter_id
        JOIN clients c ON c.id = m.client_id
        WHERE e.entry_date >= ? AND e.entry_date < ?
        GROUP BY m.id
        ORDER BY c.name, m.name
        """,
        (week.start.isoformat(), week.end.isoformat()),
    ).fetchall()

    result = {}
    for row in rows:
        result[row["matter"]] = {
            "client": row["client"],
            "hours": _round(row["hours"]),
            "billable_hours": _round(row["billable_hours"]),
        }
    return result


def idle_matters(conn: sqlite3.Connection, week: Week) -> list[dict]:
    rows = conn.execute(
        """
        SELECT m.id AS matter_id, m.name AS matter, c.name AS client
        FROM matters m
        JOIN clients c ON c.id = m.client_id
        WHERE m.status = 'open'
          AND m.id NOT IN (
              SELECT matter_id FROM time_entries
              WHERE entry_date >= ? AND entry_date < ?
          )
        ORDER BY c.name, m.name
        """,
        (week.start.isoformat(), week.end.isoformat()),
    ).fetchall()
    return [dict(row) for row in rows]


def build_review(conn: sqlite3.Connection, week: Week) -> dict:
    lawyers = hours_by_lawyer(conn, week)
    total = _round(sum(row["hours"] for row in lawyers))
    billable = _round(sum(row["billable_hours"] for row in lawyers))

    return {
        "week_start": week.start.isoformat(),
        "week_end": week.end.isoformat(),
        "previous_week": week.previous().start.isoformat(),
        "next_week": week.next().start.isoformat(),
        "totals": {
            "hours": total,
            "billable_hours": billable,
            "non_billable_hours": _round(total - billable),
        },
        "hours_by_lawyer": lawyers,
        "hours_by_matter": hours_by_matter(conn, week),
        "idle_matters": idle_matters(conn, week),
    }
