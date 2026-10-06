from datetime import date

from app.seed import seed


def test_index_page(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "Weekly Review" in response.text


def test_review_requires_valid_date(client):
    response = client.get("/api/review", params={"week_of": "not-a-date"})
    assert response.status_code == 400


def test_review_for_specific_week(client, make):
    ana = make.lawyer("Ana Ortiz")
    acme = make.client("Acme Ltd")
    contract = make.matter(acme, "Supply Contract")
    make.entry(ana, contract, "2026-10-06", 2.5)

    response = client.get("/api/review", params={"week_of": "2026-10-09"})
    assert response.status_code == 200
    body = response.json()
    assert body["week_start"] == "2026-10-05"
    assert body["week_end"] == "2026-10-11"
    assert body["totals"]["billable_hours"] == 2.5
    assert body["hours_by_lawyer"][0]["lawyer"] == "Ana Ortiz"
    assert body["hours_by_matter"]["Supply Contract"]["hours"] == 2.5


def test_create_entry_shows_up_in_review(client, make):
    ana = make.lawyer("Ana Ortiz")
    acme = make.client("Acme Ltd")
    contract = make.matter(acme, "Supply Contract")

    response = client.post(
        "/api/entries",
        json={
            "lawyer_id": ana,
            "matter_id": contract,
            "entry_date": "2026-10-07",
            "hours": 1.75,
            "billable": False,
            "description": "Internal strategy call",
        },
    )
    assert response.status_code == 201
    assert response.json()["billable"] is False

    review = client.get("/api/review", params={"week_of": "2026-10-07"}).json()
    assert review["totals"]["non_billable_hours"] == 1.75


def test_internal_entry_is_always_non_billable(client, make):
    ana = make.lawyer("Ana Ortiz")
    response = client.post(
        "/api/entries",
        json={"lawyer_id": ana, "entry_date": "2026-10-07", "hours": 2, "billable": True},
    )
    assert response.status_code == 201
    assert response.json()["matter_id"] is None
    assert response.json()["billable"] is False


def test_cannot_log_to_closed_matter(client, make):
    ana = make.lawyer("Ana Ortiz")
    acme = make.client("Acme Ltd")
    closed = make.matter(acme, "Old Litigation", status="closed")

    response = client.post(
        "/api/entries",
        json={"lawyer_id": ana, "matter_id": closed, "entry_date": "2026-10-07", "hours": 1},
    )
    assert response.status_code == 400


def test_unknown_lawyer_or_matter(client, make):
    ana = make.lawyer("Ana Ortiz")
    response = client.post(
        "/api/entries", json={"lawyer_id": 999, "entry_date": "2026-10-07", "hours": 1}
    )
    assert response.status_code == 404

    response = client.post(
        "/api/entries",
        json={"lawyer_id": ana, "matter_id": 999, "entry_date": "2026-10-07", "hours": 1},
    )
    assert response.status_code == 404


def test_hours_must_be_reasonable(client, make):
    ana = make.lawyer("Ana Ortiz")
    for hours in (0, -1, 25):
        response = client.post(
            "/api/entries", json={"lawyer_id": ana, "entry_date": "2026-10-07", "hours": hours}
        )
        assert response.status_code == 422


def test_list_entries_for_week(client, make):
    ana = make.lawyer("Ana Ortiz")
    acme = make.client("Acme Ltd")
    contract = make.matter(acme, "Supply Contract")
    make.entry(ana, contract, "2026-10-05", 1.0)
    make.entry(ana, contract, "2026-10-13", 1.0)

    entries = client.get("/api/entries", params={"week_of": "2026-10-05"}).json()
    assert [e["entry_date"] for e in entries] == ["2026-10-05"]


def test_seed_data_loads(client, conn):
    seed(conn, today=date(2026, 10, 7))

    lawyers = client.get("/api/lawyers").json()
    assert len(lawyers) == 4

    matters = client.get("/api/matters").json()
    assert any(m["status"] == "closed" for m in matters)

    review = client.get("/api/review", params={"week_of": "2026-10-07"}).json()
    assert review["totals"]["hours"] > 0
    idle = {m["matter"] for m in review["idle_matters"]}
    assert "Estate Plan Update" in idle
    assert "Customs Dispute" not in idle
