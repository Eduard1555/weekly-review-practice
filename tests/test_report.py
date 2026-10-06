from datetime import date

from app.report import build_review, hours_by_lawyer, hours_by_matter, idle_matters
from app.weeks import week_containing

WEEK = week_containing(date(2026, 10, 7))


def test_empty_week(conn):
    review = build_review(conn, WEEK)
    assert review["week_start"] == "2026-10-05"
    assert review["week_end"] == "2026-10-11"
    assert review["totals"] == {"hours": 0.0, "billable_hours": 0.0, "non_billable_hours": 0.0}
    assert review["hours_by_lawyer"] == []
    assert review["hours_by_matter"] == {}


def test_hours_per_lawyer_split_by_billable(conn, make):
    ana = make.lawyer("Ana Ortiz")
    ben = make.lawyer("Ben Cho")
    acme = make.client("Acme Ltd")
    contract = make.matter(acme, "Supply Contract")

    make.entry(ana, contract, "2026-10-05", 2.0)
    make.entry(ana, contract, "2026-10-06", 1.5, billable=False)
    make.entry(ben, contract, "2026-10-08", 3.25)

    rows = {row["lawyer"]: row for row in hours_by_lawyer(conn, WEEK)}
    assert rows["Ana Ortiz"]["hours"] == 3.5
    assert rows["Ana Ortiz"]["billable_hours"] == 2.0
    assert rows["Ana Ortiz"]["non_billable_hours"] == 1.5
    assert rows["Ben Cho"]["hours"] == 3.25
    assert rows["Ben Cho"]["non_billable_hours"] == 0.0


def test_entries_outside_week_are_ignored(conn, make):
    ana = make.lawyer("Ana Ortiz")
    acme = make.client("Acme Ltd")
    contract = make.matter(acme, "Supply Contract")

    make.entry(ana, contract, "2026-10-02", 4.0)
    make.entry(ana, contract, "2026-10-07", 1.0)
    make.entry(ana, contract, "2026-10-12", 4.0)

    review = build_review(conn, WEEK)
    assert review["totals"]["hours"] == 1.0


def test_saturday_counts_toward_the_week(conn, make):
    ana = make.lawyer("Ana Ortiz")
    acme = make.client("Acme Ltd")
    contract = make.matter(acme, "Supply Contract")

    make.entry(ana, contract, "2026-10-10", 2.0)

    assert build_review(conn, WEEK)["totals"]["hours"] == 2.0


def test_totals_add_up(conn, make):
    ana = make.lawyer("Ana Ortiz")
    ben = make.lawyer("Ben Cho")
    acme = make.client("Acme Ltd")
    contract = make.matter(acme, "Supply Contract")

    make.entry(ana, contract, "2026-10-05", 0.1)
    make.entry(ana, contract, "2026-10-05", 0.2, billable=False)
    make.entry(ben, contract, "2026-10-06", 0.4)

    totals = build_review(conn, WEEK)["totals"]
    assert totals["hours"] == 0.7
    assert totals["billable_hours"] == 0.5
    assert totals["non_billable_hours"] == 0.2


def test_hours_per_matter(conn, make):
    ana = make.lawyer("Ana Ortiz")
    acme = make.client("Acme Ltd")
    bolt = make.client("Bolt Inc")
    contract = make.matter(acme, "Supply Contract")
    dispute = make.matter(bolt, "Patent Dispute")

    make.entry(ana, contract, "2026-10-05", 2.0)
    make.entry(ana, contract, "2026-10-06", 1.0, billable=False)
    make.entry(ana, dispute, "2026-10-07", 4.5)

    matters = hours_by_matter(conn, WEEK)
    assert matters["Supply Contract"] == {"client": "Acme Ltd", "hours": 3.0, "billable_hours": 2.0}
    assert matters["Patent Dispute"] == {"client": "Bolt Inc", "hours": 4.5, "billable_hours": 4.5}


def test_internal_time_counts_for_lawyer_but_not_matters(conn, make):
    ana = make.lawyer("Ana Ortiz")
    make.entry(ana, None, "2026-10-06", 3.0, billable=False, description="CLE seminar")

    review = build_review(conn, WEEK)
    assert review["hours_by_lawyer"][0]["non_billable_hours"] == 3.0
    assert review["totals"]["non_billable_hours"] == 3.0
    assert review["hours_by_matter"] == {}


def test_idle_matters_lists_open_matters_without_time(conn, make):
    ana = make.lawyer("Ana Ortiz")
    acme = make.client("Acme Ltd")
    busy = make.matter(acme, "Supply Contract")
    quiet = make.matter(acme, "Trademark Filing")

    make.entry(ana, busy, "2026-10-06", 1.0)
    make.entry(ana, quiet, "2026-09-30", 1.0)

    idle = idle_matters(conn, WEEK)
    assert [m["matter_id"] for m in idle] == [quiet]
    assert idle[0]["client"] == "Acme Ltd"


def test_idle_matters_skips_closed_matters(conn, make):
    acme = make.client("Acme Ltd")
    make.matter(acme, "Old Litigation", status="closed")
    open_id = make.matter(acme, "Trademark Filing")

    idle = idle_matters(conn, WEEK)
    assert [m["matter_id"] for m in idle] == [open_id]


def test_previous_and_next_week_links(conn):
    review = build_review(conn, WEEK)
    assert review["previous_week"] == "2026-09-28"
    assert review["next_week"] == "2026-10-12"
