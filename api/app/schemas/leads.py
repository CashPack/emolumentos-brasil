from __future__ import annotations

from pydantic import BaseModel, Field


class LeadCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    email: str | None = None
    phone: str | None = None
    profile: str | None = None
    uf: str | None = Field(default=None, min_length=2, max_length=2)
    property_value: float | None = None
    message: str | None = Field(default=None, max_length=2000)
    consent: bool = True
