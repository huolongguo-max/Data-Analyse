# reserve_processor/detail_calculator.py

from __future__ import annotations

import pandas as pd

from .constants import BASE_METRICS
from .utils import (
    date_range_inclusive,
    inclusive_days,
    is_blank,
    metric_date_col,
    remove_existing_date_metric_columns,
    to_date,
    to_number,
    to_number_zero,
    get_first_existing,
)


def build_detail_date_axis(detail: pd.DataFrame) -> list[pd.Timestamp]:
    start_dates = detail["启动日期"].map(to_date)
    end_dates = detail["停止日期"].map(to_date)

    min_start = min([d for d in start_dates if d is not None], default=None)
    max_end = max([d for d in end_dates if d is not None], default=None)

    if min_start is None or max_end is None:
        raise ValueError("储备明细表无法识别有效的启动日期/停止日期")

    if max_end < min_start:
        raise ValueError("储备明细表存在停止日期早于启动日期的情况")

    return date_range_inclusive(min_start, max_end)


def calculate_base_reserve_for_row(
    row: pd.Series,
    date_axis: list[pd.Timestamp],
) -> dict[pd.Timestamp, float | None]:
    """
    保底储备量特殊计算逻辑：

    若存在下周储备：
    1. 下周区间内：
       下周保底储备量 / 下周天数
    2. 启动-停止区间内，且不属于下周区间：
       (保底储备量 - 下周保底储备量) / (总天数 - 下周天数)

    若不存在下周储备：
    保底储备量 / 总天数
    """
    values = {d: None for d in date_axis}

    start = to_date(row.get("启动日期"))
    end = to_date(row.get("停止日期"))

    if start is None or end is None or end < start:
        return values

    values = {d: 0.0 for d in date_axis}

    total_days = inclusive_days(start, end)
    if total_days <= 0:
        return values

    total_base = to_number_zero(row.get("保底储备量"))

    # 实际表里通常叫“下周储备量”，这里兼容其他可能命名
    weekly_trigger = get_first_existing(
        row,
        ["下周冲高储备量", "下周储备量", "下周保底储备量"],
        default="",
    )

    next_start = to_date(row.get("下周启动日期"))
    next_end = to_date(row.get("下周停止日期"))
    next_base = to_number(row.get("下周保底储备量"))

    has_weekly = (
        not is_blank(weekly_trigger)
        and next_start is not None
        and next_end is not None
        and next_base is not None
    )

    if not has_weekly:
        avg = total_base / total_days
        for d in date_axis:
            if start <= d <= end:
                values[d] = avg
        return values

    # 下周区间必须裁剪到启动-停止区间内
    next_start = max(start, next_start)
    next_end = min(end, next_end)

    if next_end < next_start:
        avg = total_base / total_days
        for d in date_axis:
            if start <= d <= end:
                values[d] = avg
        return values

    weekly_days = inclusive_days(next_start, next_end)
    remaining_days = total_days - weekly_days

    weekly_avg = next_base / weekly_days if weekly_days > 0 else 0.0
    remaining_avg = (
        (total_base - next_base) / remaining_days
        if remaining_days > 0
        else 0.0
    )

    for d in date_axis:
        if start <= d <= end:
            if next_start <= d <= next_end:
                values[d] = weekly_avg
            else:
                values[d] = remaining_avg

    return values


def calculate_simple_average_for_row(
    row: pd.Series,
    metric: str,
    date_axis: list[pd.Timestamp],
) -> dict[pd.Timestamp, float | None]:
    """
    适用于：
    1. 冲高储备量
    2. 保底预测业绩
    3. 冲高预测业绩

    逻辑：
    指标总量 / 启动日期至停止日期天数
    """
    values = {d: None for d in date_axis}

    start = to_date(row.get("启动日期"))
    end = to_date(row.get("停止日期"))

    if start is None or end is None or end < start:
        return values

    values = {d: 0.0 for d in date_axis}

    days = inclusive_days(start, end)
    if days <= 0:
        return values

    total_value = to_number_zero(row.get(metric))
    avg = total_value / days

    for d in date_axis:
        if start <= d <= end:
            values[d] = avg

    return values


def calculate_detail_sheet(
    detail: pd.DataFrame,
) -> tuple[pd.DataFrame, list[pd.Timestamp]]:
    """
    计算储备明细表：

    1. 根据全表最早启动日期、最晚停止日期构建日期轴
    2. 为四个变量分别创建 n 个日期列
    3. 每一行独立计算
    """
    base_detail = remove_existing_date_metric_columns(detail).reset_index(drop=True)
    date_axis = build_detail_date_axis(base_detail)

    include_year = date_axis[0].year != date_axis[-1].year

    new_data: dict[str, list[float | None]] = {}

    for metric in BASE_METRICS:
        for d in date_axis:
            col = metric_date_col(metric, d, include_year=include_year)
            new_data[col] = [None] * len(base_detail)

    for pos, (_, row) in enumerate(base_detail.iterrows()):
        base_values = calculate_base_reserve_for_row(row, date_axis)

        for d, value in base_values.items():
            col = metric_date_col("保底储备量", d, include_year=include_year)
            new_data[col][pos] = value

        for metric in ["冲高储备量", "保底预测业绩", "冲高预测业绩"]:
            metric_values = calculate_simple_average_for_row(row, metric, date_axis)

            for d, value in metric_values.items():
                col = metric_date_col(metric, d, include_year=include_year)
                new_data[col][pos] = value

    date_columns_df = pd.DataFrame(new_data)

    result = pd.concat(
        [base_detail, date_columns_df],
        axis=1,
    )

    return result, date_axis
