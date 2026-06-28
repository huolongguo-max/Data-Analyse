# reserve_processor/filename_parser.py

from __future__ import annotations

import re
from pathlib import Path

from .constants import FILENAME_PATTERN
from .models import FileMeta


def parse_filename(path: str | Path) -> FileMeta:
    """
    示例：
    【0612】2026年6月全国储备摸底.xlsx

    提取：
    date_code = 0612
    year = 2026
    month = 6
    """
    filename = Path(path).name
    match = re.search(FILENAME_PATTERN, filename)

    if not match:
        return FileMeta(
            filename=filename,
            year=None,
            month=None,
            version=None,
            file_date_code=None,
        )

    return FileMeta(
        filename=filename,
        year=int(match.group("year")),
        month=int(match.group("month")),
        version=None,
        file_date_code=match.group("date_code"),
    )