from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class DashboardSingleResponse(BaseModel):
    period_code: str
    upload_seq: int
    dimension_level: str
    scenario: str
    total: int
    rows: list[dict[str, Any]]


class DashboardCompareResponse(BaseModel):
    show_compare: bool
    period_code: str | None = None
    current_upload_seq: int | None = None
    previous_upload_seq: int | None = None
    dimension_level: str | None = None
    scenario: str | None = None
    message: str | None = None
    total: int = 0
    rows: list[dict[str, Any]] = Field(default_factory=list)
