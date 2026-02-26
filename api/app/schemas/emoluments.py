from __future__ import annotations

from datetime import date, datetime
from pydantic import BaseModel, Field


class EmolumentTableCreate(BaseModel):
    uf: str = Field(min_length=2, max_length=2)
    year: int = Field(ge=2000, le=2100)
    valid_from: date | None = None
    valid_to: date | None = None
    source_name: str | None = None


class EmolumentTableOut(BaseModel):
    id: str
    uf: str
    year: int
    status: str
    source_name: str | None = None
    source_hash: str | None = None
    created_at: datetime


class EmolumentBracketCreate(BaseModel):
    range_from: float
    range_to: float
    amount: float
    sort_order: int | None = None


class EmolumentBracketOut(BaseModel):
    id: str
    table_id: str
    range_from: float
    range_to: float
    amount: float
    sort_order: int | None = None
    active: bool


class EmolumentTableWithBrackets(EmolumentTableOut):
    brackets: list[EmolumentBracketOut]
