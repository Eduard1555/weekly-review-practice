from datetime import date

import pytest

from app.weeks import parse_week_of, week_containing


def test_week_starts_on_monday():
    week = week_containing(date(2026, 10, 7))
    assert week.start == date(2026, 10, 5)
    assert week.end == date(2026, 10, 11)


def test_monday_is_its_own_week_start():
    assert week_containing(date(2026, 10, 5)).start == date(2026, 10, 5)


def test_sunday_belongs_to_the_week_before_it():
    assert week_containing(date(2026, 10, 11)).start == date(2026, 10, 5)


def test_week_crosses_year_boundary():
    week = week_containing(date(2027, 1, 1))
    assert week.start == date(2026, 12, 28)
    assert week.end == date(2027, 1, 3)


def test_previous_and_next():
    week = week_containing(date(2026, 10, 7))
    assert week.previous().start == date(2026, 9, 28)
    assert week.next().start == date(2026, 10, 12)


def test_contains():
    week = week_containing(date(2026, 10, 7))
    assert week.contains(date(2026, 10, 5))
    assert week.contains(date(2026, 10, 11))
    assert not week.contains(date(2026, 10, 12))
    assert not week.contains(date(2026, 10, 4))


def test_parse_week_of_defaults_to_today():
    assert parse_week_of(None, today=date(2026, 10, 9)).start == date(2026, 10, 5)
    assert parse_week_of("", today=date(2026, 10, 9)).start == date(2026, 10, 5)


def test_parse_week_of_any_day_in_week():
    assert parse_week_of("2026-10-08").start == date(2026, 10, 5)


def test_parse_week_of_rejects_garbage():
    with pytest.raises(ValueError):
        parse_week_of("next friday")
