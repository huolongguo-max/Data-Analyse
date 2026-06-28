# reserve_processor/validators.py

from __future__ import annotations

import pandas as pd

from .constants import (
    DETAIL_REQUIRED_COLUMNS,
    SCHEDULE_REQUIRED_COLUMNS,
    TARGET_REQUIRED_COLUMNS,
)


def validate_required_columns(
    df: pd.DataFrame,
    required_columns: list[str],
    sheet_name: str,
) -> list[str]:
    warnings: list[str] = []

    missing = [col for col in required_columns if col not in df.columns]
    if missing:
        raise ValueError(f"{sheet_name} 缺少必要字段: {missing}")

    duplicated = df.columns[df.columns.duplicated()].tolist()
    if duplicated:
        raise ValueError(f"{sheet_name} 存在重复字段: {duplicated}")

    if df.empty:
        warnings.append(f"{sheet_name} 是空表")

    return warnings


def validate_workbook(
    detail: pd.DataFrame,
    schedule: pd.DataFrame,
    target: pd.DataFrame,
) -> list[str]:
    warnings: list[str] = []

    warnings.extend(
        validate_required_columns(
            detail,
            DETAIL_REQUIRED_COLUMNS,
            "储备明细表",
        )
    )

    warnings.extend(
        validate_required_columns(
            schedule,
            SCHEDULE_REQUIRED_COLUMNS,
            "每月班期表",
        )
    )

    warnings.extend(
        validate_required_columns(
            target,
            TARGET_REQUIRED_COLUMNS,
            "已进线表",
        )
    )

    return warnings