from __future__ import annotations

from pydantic import Field
from pydantic import BaseModel


class CompletedTableResponse(BaseModel):
    table_type: str
    columns: list[str]
    total: int
    rows: list[dict]
    meta: dict = Field(default_factory=dict)
