# reserve_processor/schedule_calculator.py

from __future__ import annotations

import pandas as pd

from .constants import BASE_METRICS, TOTAL_METRICS
from .utils import (
    add_optional,
    ensure_columns,
    get_first_existing,
    metric_date_col,
    round_number,
    to_date,
    to_number,
)


def sum_detail_metric_by_project_and_period(
    detail: pd.DataFrame,
    project,
    start: pd.Timestamp | None,
    end: pd.Timestamp | None,
    metric: str,
    date_axis: list[pd.Timestamp],
) -> float | None:
    if start is None or end is None or end < start:
        return None

    include_year = date_axis[0].year != date_axis[-1].year
    valid_dates = [day for day in date_axis if start <= day <= end]
    metric_cols = [metric_date_col(metric, day, include_year=include_year) for day in valid_dates]
    metric_cols = [col for col in metric_cols if col in detail.columns]

    if not metric_cols:
        return 0.0

    project_mask = detail["课线项目"].astype(str).str.strip() == str(project).strip()
    if not project_mask.any():
        return 0.0

    matched = detail.loc[project_mask, metric_cols]
    numeric_values = pd.to_numeric(pd.Series(matched.to_numpy().ravel()), errors="coerce").fillna(0)
    return round_number(numeric_values.sum())


def get_schedule_entered_and_achieved(raw_row: pd.Series) -> tuple[float | None, float | None]:
    entered = get_first_existing(
        raw_row,
        ["已进线量", "已进线"],
        default=raw_row.get("保底总储备量", ""),
    )
    achieved = get_first_existing(
        raw_row,
        ["已达成预测业绩"],
        default=raw_row.get("保底总预测业绩", ""),
    )
    return to_number(entered), to_number(achieved)


def calculate_schedule_sheet(
    schedule: pd.DataFrame,
    detail: pd.DataFrame,
    date_axis: list[pd.Timestamp],
) -> pd.DataFrame:
    original_schedule = schedule.copy().reset_index(drop=True)
    out = ensure_columns(schedule.reset_index(drop=True), BASE_METRICS + TOTAL_METRICS)

    for idx, row in out.iterrows():
        raw_row = original_schedule.loc[idx]
        project = row.get("课线项目")
        start = to_date(row.get("进线开始时间"))
        end = to_date(row.get("进线截止时间"))

        for metric in BASE_METRICS:
            out.at[idx, metric] = sum_detail_metric_by_project_and_period(
                detail=detail,
                project=project,
                start=start,
                end=end,
                metric=metric,
                date_axis=date_axis,
            )

        status = str(row.get("招生进度", "")).strip()
        entered, achieved = get_schedule_entered_and_achieved(raw_row)

        base_reserve = to_number(out.at[idx, "保底储备量"])
        base_perf = to_number(out.at[idx, "保底预测业绩"])
        high_reserve = to_number(out.at[idx, "冲高储备量"])
        high_perf = to_number(out.at[idx, "冲高预测业绩"])

        if status == "未启动":
            out.at[idx, "保底总储备量"] = base_reserve
            out.at[idx, "保底总预测业绩"] = base_perf
            out.at[idx, "冲高总储备量"] = high_reserve
            out.at[idx, "冲高总预测业绩"] = high_perf

        elif status == "招生中":
            out.at[idx, "保底总储备量"] = add_optional(entered, base_reserve)
            out.at[idx, "保底总预测业绩"] = add_optional(achieved, base_perf)
            out.at[idx, "冲高总储备量"] = add_optional(entered, high_reserve)
            out.at[idx, "冲高总预测业绩"] = add_optional(achieved, high_perf)

        elif status == "已结束":
            out.at[idx, "保底总储备量"] = entered
            out.at[idx, "保底总预测业绩"] = achieved
            out.at[idx, "冲高总储备量"] = entered
            out.at[idx, "冲高总预测业绩"] = achieved

            out.at[idx, "保底储备量"] = None
            out.at[idx, "保底预测业绩"] = None
            out.at[idx, "冲高储备量"] = None
            out.at[idx, "冲高预测业绩"] = None

        else:
            out.at[idx, "保底总储备量"] = base_reserve
            out.at[idx, "保底总预测业绩"] = base_perf
            out.at[idx, "冲高总储备量"] = high_reserve
            out.at[idx, "冲高总预测业绩"] = high_perf

    return out
