# reserve_processor/models.py

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd


@dataclass
class FileMeta:
    filename: str
    year: int | None
    month: int | None
    version: int | None
    file_date_code: str | None


@dataclass
class WorkbookData:
    meta: FileMeta
    detail: pd.DataFrame
    schedule: pd.DataFrame
    target: pd.DataFrame


@dataclass
class ProcessResult:
    meta: FileMeta
    detail: pd.DataFrame
    schedule: pd.DataFrame
    target: pd.DataFrame
    warnings: list[str]
    output_path: Path | None = None
