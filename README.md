# Weekly Review

A small web app for the firm's Friday review. Lawyers log time entries against
client matters; a partner opens the review page to see the week at a glance:

- total, billable and non-billable hours for the week
- hours per lawyer (total / billable / non-billable)
- hours per matter (total / billable)
- open matters with no time logged that week

Stack: Python, FastAPI, SQLite, a plain HTML/JS page, pytest.

## Project layout

```
app/
  db.py        SQLite connection and schema
  weeks.py     week calculations
  report.py    the weekly summary queries
  models.py    request/response models
  main.py      FastAPI app and routes
  seed.py      demo data loader
static/
  index.html   review page
  review.js    fetches /api/review and renders it
  style.css
tests/         pytest suite
```

## Setup (Windows)

Requires Python 3.10 or newer. In PowerShell, from the `weekly-review` folder:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

If PowerShell refuses to run the activation script, run this once and try again:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

(In `cmd.exe`, activate with `.venv\Scripts\activate.bat` instead.)

## Load demo data

```powershell
python -m app.seed
```

This **wipes** the database and loads four lawyers, five clients, seven matters
and time entries for the current week and the previous week. Dates are relative
to today, so the review page always has data to show.

The database file is `weekly_review.db` in the project folder. Set the
`WEEKLY_REVIEW_DB` environment variable to use a different file:

```powershell
$env:WEEKLY_REVIEW_DB = "C:\temp\review.db"
```

## Run

```powershell
uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000 for the review page. Use the *Previous week* /
*Next week* buttons to move around, or link straight to a week with
`http://127.0.0.1:8000/?week_of=2026-10-05` (any date inside the week works).

Interactive API docs are at http://127.0.0.1:8000/docs.

## Run the tests

```powershell
pytest
```

## How the review works

### Weeks

A review week runs **Monday through Sunday**, inclusive. Weekend work counts
toward the week it falls in, so Saturday and Sunday entries appear in the
review for the Monday before them.

### Billable vs non-billable

Each time entry has a `billable` flag. Non-billable hours are time spent on a
matter that will not be invoiced (internal reviews, write-offs, team calls).

Time can also be logged **without a matter** (training, firm admin, business
development). This is internal time: it is always stored as non-billable, it
counts toward the lawyer's totals and the weekly totals, and it does not appear
in the hours-per-matter table. Because of this, the matter table does not have
to add up to the weekly total.

### Matters with no activity

This list shows every **open** matter that has no time logged during the
selected week. **Closed matters are never listed**, no matter how long ago they
were last worked on: once a matter is closed it drops out of the weekly review
entirely. Time cannot be logged to a closed matter. To bring a matter back into
the review, reopen it (set its status back to `open`).

## API

| Method | Path              | Description                                              |
|--------|-------------------|----------------------------------------------------------|
| GET    | `/api/review`     | Weekly summary. Optional `week_of=YYYY-MM-DD`; defaults to the current week. |
| GET    | `/api/lawyers`    | All lawyers.                                             |
| GET    | `/api/matters`    | All matters with client and status.                      |
| GET    | `/api/entries`    | Raw time entries for a week (`week_of` as above).        |
| POST   | `/api/entries`    | Log time. Body: `lawyer_id`, `matter_id` (optional), `entry_date`, `hours` (0–24], `billable`, `description`. |

Example (PowerShell):

```powershell
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/api/entries `
  -ContentType "application/json" `
  -Body '{"lawyer_id": 1, "matter_id": 1, "entry_date": "2026-10-06", "hours": 1.5, "billable": true, "description": "Client call"}'
```
