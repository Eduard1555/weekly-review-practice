"""Load demo data. Run with: python -m app.seed

Entries are placed relative to the current week so the review page
always has something to show: the current week and the one before it,
plus some older history on a closed matter.
"""

import sqlite3
from datetime import date, timedelta

from app import db
from app.weeks import week_containing

LAWYERS = ["Dana Kowalski", "Marcus Bell", "Priya Shah", "Tom Reyes"]

CLIENTS = [
    "Delgado Family",
    "Hargrove Holdings",
    "Linden Medical Group",
    "Petrov Imports",
    "Whitfield Partners",
]

# key: (client, matter name, status, opened days before this Monday)
MATTERS = {
    "hargrove_lease": ("Hargrove Holdings", "Office Lease Renewal", "open", 90),
    "hargrove_general": ("Hargrove Holdings", "General Advisory", "open", 400),
    "whitfield_series_b": ("Whitfield Partners", "Series B Financing", "open", 45),
    "delgado_estate": ("Delgado Family", "Estate Plan Update", "open", 120),
    "linden_general": ("Linden Medical Group", "General Advisory", "open", 300),
    "linden_ruiz": ("Linden Medical Group", "Employment Claim - Ruiz", "open", 60),
    "petrov_customs": ("Petrov Imports", "Customs Dispute", "closed", 200),
}

# (lawyer, matter key, day offset from this Monday, hours, billable, description)
ENTRIES = [
    # Current week
    ("Dana Kowalski", "hargrove_lease", 0, 2.5, True, "Review landlord redline"),
    ("Dana Kowalski", "linden_general", 1, 1.0, True, "Board question on vendor contract"),
    ("Dana Kowalski", "hargrove_lease", 2, 3.0, True, "Draft response to landlord"),
    ("Dana Kowalski", "whitfield_series_b", 3, 1.5, False, "Internal review of disclosure schedule"),
    ("Dana Kowalski", "hargrove_lease", 4, 2.0, True, "Call with client re: renewal terms"),
    ("Marcus Bell", "whitfield_series_b", 0, 4.0, True, "Term sheet markup"),
    ("Marcus Bell", "whitfield_series_b", 1, 3.5, True, "Investor rights agreement"),
    ("Marcus Bell", "whitfield_series_b", 2, 1.0, False, "Team sync"),
    ("Marcus Bell", "whitfield_series_b", 5, 2.0, True, "Closing checklist"),
    ("Marcus Bell", "whitfield_series_b", 6, 3.0, True, "Signature pages and closing set"),
    ("Priya Shah", "hargrove_general", 1, 1.5, True, "Advice on director indemnities"),
    ("Priya Shah", "hargrove_lease", 2, 1.0, False, "Precedent research"),
    ("Priya Shah", "hargrove_general", 3, 1.0, True, "Follow-up memo"),
    ("Tom Reyes", "linden_general", 0, 2.0, True, "HIPAA vendor review"),
    ("Tom Reyes", "linden_general", 2, 1.0, True, "Call with GC"),
    ("Tom Reyes", "whitfield_series_b", 4, 2.5, True, "Cap table diligence"),
    # Previous week
    ("Dana Kowalski", "delgado_estate", -7, 2.0, True, "Trust amendment draft"),
    ("Dana Kowalski", "hargrove_lease", -5, 1.5, True, "Lease abstract"),
    ("Marcus Bell", "whitfield_series_b", -6, 5.0, True, "Stock purchase agreement"),
    ("Marcus Bell", "whitfield_series_b", -4, 2.5, True, "Diligence calls"),
    ("Priya Shah", "hargrove_general", -6, 2.0, True, "Shareholder letter review"),
    ("Priya Shah", "hargrove_lease", -1, 1.5, True, "Weekend markup of renewal notice"),
    ("Tom Reyes", "linden_ruiz", -5, 3.0, True, "Position statement draft"),
    ("Tom Reyes", "linden_general", -3, 1.0, False, "Conflict check"),
    # Older history on the closed matter
    ("Tom Reyes", "petrov_customs", -70, 4.0, True, "Hearing preparation"),
    ("Dana Kowalski", "petrov_customs", -68, 2.0, True, "Settlement agreement"),
]


def seed(conn: sqlite3.Connection, today: date | None = None) -> None:
    db.reset_db(conn)
    monday = week_containing(today or date.today()).start

    lawyer_ids = {}
    for name in LAWYERS:
        lawyer_ids[name] = conn.execute("INSERT INTO lawyers (name) VALUES (?)", (name,)).lastrowid

    client_ids = {}
    for name in CLIENTS:
        client_ids[name] = conn.execute("INSERT INTO clients (name) VALUES (?)", (name,)).lastrowid

    matter_ids = {}
    for key, (client, name, status, opened_days_ago) in MATTERS.items():
        opened_on = (monday - timedelta(days=opened_days_ago)).isoformat()
        matter_ids[key] = conn.execute(
            "INSERT INTO matters (client_id, name, status, opened_on) VALUES (?, ?, ?, ?)",
            (client_ids[client], name, status, opened_on),
        ).lastrowid

    for lawyer, matter, offset, hours, billable, description in ENTRIES:
        conn.execute(
            """
            INSERT INTO time_entries (lawyer_id, matter_id, entry_date, hours, billable, description)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                lawyer_ids[lawyer],
                matter_ids[matter],
                (monday + timedelta(days=offset)).isoformat(),
                hours,
                int(billable),
                description,
            ),
        )
    conn.commit()


def main() -> None:
    conn = db.connect()
    seed(conn)
    conn.close()
    print(f"Seeded demo data into {db.get_db_path()}")


if __name__ == "__main__":
    main()
