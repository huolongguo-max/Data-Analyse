# -*- coding: utf-8 -*-
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


SHEET_NAME_TO_TABLE_TYPE = {
    "\u50a8\u5907\u660e\u7ec6\u8868": "reserve_detail",
    "\u6bcf\u6708\u73ed\u671f\u8868": "monthly_class",
    "\u5df2\u8fdb\u7ebf\u8868": "inbound",
    "\u6bcf\u6708\u76ee\u6807\u8868": "monthly_target",
}

REQUIRED_SHEET_NAMES = tuple(SHEET_NAME_TO_TABLE_TYPE.keys())

# New format: \u30100612\u30112026\u5e746\u6708\u5168\u56fd\u50a8\u5907\u6478\u5e95.xlsx
WORKBOOK_FILENAME_PATTERN = re.compile(
    r"^\u3010(?P<record_mmdd>\d{4})\u3011(?P<period_year>\d{4})\u5e74(?P<period_month>[1-9]|1[0-2])\u6708\u5168\u56fd\u50a8\u5907\u6478\u5e95\.xlsx$"
)


@dataclass(frozen=True)
class ParsedWorkbookFilename:
    original_filename: str
    period_year: int
    source_period_month: int
    upload_seq: int
    source_record_mmdd: str

    @property
    def source_period_label(self) -> str:
        return f"{self.source_period_month}\u6708\u73ed\u671f"

    @property
    def period_code(self) -> str:
        return f"{self.period_year:04d}-{self.source_period_month:02d}"


def build_workbook_filename(record_mmdd: str, period_year: int, source_period_month: int) -> str:
    if re.fullmatch(r"\d{4}", str(record_mmdd).strip()) is None:
        raise ValueError("record_mmdd must be a 4-digit MMDD string")

    year = int(period_year)
    month = int(source_period_month)
    if year < 1000 or year > 9999:
        raise ValueError("period_year must be a 4-digit year")
    if month < 1 or month > 12:
        raise ValueError("source_period_month must be between 1 and 12")

    return f"【{str(record_mmdd).strip()}】{year}年{month}月全国储备摸底.xlsx"


def parse_workbook_filename(filename: str, upload_seq: int = 1) -> ParsedWorkbookFilename:
    base_name = Path(filename).name
    match = WORKBOOK_FILENAME_PATTERN.fullmatch(base_name)
    if match is None:
        raise ValueError(
            "File name must follow the format [MMDD]YYYYyMmonth.xlsx, e.g. [0612]2026y6month.xlsx"
        )

    return ParsedWorkbookFilename(
        original_filename=base_name,
        period_year=int(match.group("period_year")),
        source_period_month=int(match.group("period_month")),
        upload_seq=upload_seq,
        source_record_mmdd=match.group("record_mmdd"),
    )


def parse_sheet_name(sheet_name: str) -> str:
    if sheet_name not in SHEET_NAME_TO_TABLE_TYPE:
        raise ValueError(
            f"sheet name must be one of {', '.join(REQUIRED_SHEET_NAMES)}, got '{sheet_name}'"
        )
    return SHEET_NAME_TO_TABLE_TYPE[sheet_name]


def validate_required_sheet_names(sheet_names: Iterable[str]) -> tuple[str, ...]:
    actual_names = tuple(sheet_names)
    actual_set = set(actual_names)
    required_set = set(REQUIRED_SHEET_NAMES)

    missing = [name for name in REQUIRED_SHEET_NAMES if name not in actual_set]
    unexpected = [name for name in actual_names if name not in required_set]

    if missing or unexpected:
        problems: list[str] = []
        if missing:
            problems.append(f"missing sheets: {', '.join(missing)}")
        if unexpected:
            problems.append(f"unexpected sheets: {', '.join(unexpected)}")
        raise ValueError("; ".join(problems))

    return actual_names
