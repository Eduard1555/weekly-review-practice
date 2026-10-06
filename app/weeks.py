from dataclasses import dataclass
from datetime import date, timedelta


@dataclass(frozen=True)
class Week:
    start: date
    end: date

    def previous(self) -> "Week":
        return week_containing(self.start - timedelta(days=7))

    def next(self) -> "Week":
        return week_containing(self.start + timedelta(days=7))

    def contains(self, day: date) -> bool:
        return self.start <= day <= self.end


def week_containing(day: date) -> Week:
    start = day - timedelta(days=day.weekday())
    return Week(start=start, end=start + timedelta(days=6))


def parse_week_of(value: str | None, today: date | None = None) -> Week:
    """Return the Monday-to-Sunday week containing the given ISO date.

    With no value, the week containing ``today`` is used.
    Raises ValueError for anything that is not a YYYY-MM-DD date.
    """
    if not value:
        return week_containing(today or date.today())
    return week_containing(date.fromisoformat(value))
