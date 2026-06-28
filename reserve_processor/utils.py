# reserve_processor/utils.py

from __future__ import annotations

import numbers
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path
import re

import pandas as pd

from .constants import BASE_METRICS, COMPLETED_FILE_SUFFIX

CALC_QUANT = Decimal("0.000001")
DATE_HEADER_PATTERN = re.compile(r"^(?:\d{4}年)?\d{1,2}月\d{1,2}日$")


def round_number(value, quant: Decimal = CALC_QUANT) -> float | None:
    if is_blank(value):
        return None

    try:
        decimal_value = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return None

    return float(decimal_value.quantize(quant, rounding=ROUND_HALF_UP))


def is_blank(value) -> bool:
    if value is None:
        return True

    try:
        if pd.isna(value):
            return True
    except Exception:
        pass

    if isinstance(value, str) and value.strip() == "":
        return True

    return False


def to_number(value) -> float | None:
    return round_number(value)


def to_number_zero(value) -> float:
    num = to_number(value)
    return 0.0 if num is None else num


def add_optional(*values: float | None) -> float | None:
    if any(value is None for value in values):
        return None

    total = sum((Decimal(str(value)) for value in values), Decimal("0"))
    return float(total.quantize(CALC_QUANT, rounding=ROUND_HALF_UP))


def to_date(value) -> pd.Timestamp | None:
    """
    兼容：
    1. datetime / Timestamp
    2. Excel 日期序列号
    3. 字符串日期
    """
    if is_blank(value):
        return None

    if isinstance(value, numbers.Number) and value > 20000:
        try:
            return pd.to_datetime(value, unit="D", origin="1899-12-30").normalize()
        except Exception:
            return None

    try:
        dt = pd.to_datetime(value, errors="coerce")
        if pd.isna(dt):
            return None
        return pd.Timestamp(dt).normalize()
    except Exception:
        return None


def inclusive_days(start: pd.Timestamp, end: pd.Timestamp) -> int:
    return int((end - start).days) + 1


def date_range_inclusive(start: pd.Timestamp, end: pd.Timestamp) -> list[pd.Timestamp]:
    return list(pd.date_range(start, end, freq="D"))


def format_cn_date(date: pd.Timestamp, include_year: bool = False) -> str:
    if include_year:
        return f"{date.year}年{date.month}月{date.day}日"
    return f"{date.month}月{date.day}日"


def metric_date_col(metric: str, date: pd.Timestamp, include_year: bool = False) -> str:
    return f"{metric}-{format_cn_date(date, include_year=include_year)}"


def get_first_existing(row: pd.Series, candidates: list[str], default=""):
    for col in candidates:
        if col in row.index:
            value = row.get(col)
            if not is_blank(value):
                return value
    return default


def ensure_columns(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    out = df.copy()
    for col in columns:
        if col not in out.columns:
            out[col] = ""
    return out


def safe_rate(numerator, denominator):
    n = to_number(numerator)
    d = to_number(denominator)

    if n is None or d is None or d == 0:
        return ""

    return float((Decimal(str(n)) / Decimal(str(d))).quantize(CALC_QUANT, rounding=ROUND_HALF_UP))


def remove_existing_date_metric_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    防止重复计算时反复追加：
    保底储备量-3月1日
    冲高储备量-3月1日
    ...
    """
    prefixes = tuple(f"{metric}-" for metric in BASE_METRICS)
    keep_cols = [
        col
        for col in df.columns
        if not str(col).startswith(prefixes)
        and not DATE_HEADER_PATTERN.match(str(col).strip())
    ]
    return df[keep_cols].copy()


def build_completed_output_path(
    input_path: str | Path,
    output_path: str | Path | None = None,
) -> Path:
    input_path = Path(input_path)
    stem = input_path.stem

    if not stem.endswith(COMPLETED_FILE_SUFFIX):
        stem = f"{stem}{COMPLETED_FILE_SUFFIX}"

    filename = f"{stem}{input_path.suffix or '.xlsx'}"

    if output_path is None:
        return input_path.with_name(filename)

    output_path = Path(output_path)
    if output_path.suffix:
        return output_path

    return output_path / filename
