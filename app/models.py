from datetime import date

from pydantic import BaseModel, Field


class EntryIn(BaseModel):
    lawyer_id: int
    matter_id: int | None = None
    entry_date: date
    hours: float = Field(gt=0, le=24)
    billable: bool = True
    description: str = Field(default="", max_length=500)


class Entry(BaseModel):
    id: int
    lawyer_id: int
    matter_id: int | None
    entry_date: date
    hours: float
    billable: bool
    description: str


class Lawyer(BaseModel):
    id: int
    name: str


class Matter(BaseModel):
    id: int
    name: str
    client: str
    status: str


class Totals(BaseModel):
    hours: float
    billable_hours: float
    non_billable_hours: float


class LawyerHours(BaseModel):
    lawyer_id: int
    lawyer: str
    hours: float
    billable_hours: float
    non_billable_hours: float


class MatterHours(BaseModel):
    client: str
    hours: float
    billable_hours: float


class IdleMatter(BaseModel):
    matter_id: int
    matter: str
    client: str


class WeeklyReview(BaseModel):
    week_start: date
    week_end: date
    previous_week: date
    next_week: date
    totals: Totals
    hours_by_lawyer: list[LawyerHours]
    hours_by_matter: dict[str, MatterHours]
    idle_matters: list[IdleMatter]
