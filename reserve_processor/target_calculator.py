# reserve_processor/target_calculator.py

from __future__ import annotations

import pandas as pd

from .constants import (
    BASE_METRICS,
    RATE_METRICS,
    TARGET_LEVEL_TO_DETAIL_COLUMN,
    TOTAL_METRICS,
)
from .utils import add_optional, ensure_columns, round_number, safe_rate, to_number, to_number_zero


def sum_detail_metric_by_target(
    detail: pd.DataFrame,
    target_level: str,
    target_object,
    metric: str,
) -> float | None:
    """
    已进线表四个基础指标：

    根据：
    - 目标层面
    - 目标对象

    回到储备明细表加总。

    目标层面映射：
    - 全国 -> 不筛选，直接全表加总
    - 片区 -> 储备明细表的片区
    - 省份 -> 储备明细表的省份
    - BD -> 储备明细表的 BD
    """
    if metric not in detail.columns:
        return None

    dim_col = TARGET_LEVEL_TO_DETAIL_COLUMN.get(target_level)

    metric_values = pd.to_numeric(detail[metric], errors="coerce").fillna(0)

    if dim_col is None:
        return round_number(metric_values.sum())

    if dim_col not in detail.columns:
        return None

    mask = (
        detail[dim_col].astype(str).str.strip()
        == str(target_object).strip()
    )

    if not mask.any():
        return 0.0

    return round_number(metric_values.loc[mask].sum())


def calculate_target_sheet(
    target: pd.DataFrame,
    detail: pd.DataFrame,
) -> pd.DataFrame:
    """
    计算已进线表：

    1. 根据目标层面 + 目标对象，从储备明细表汇总：
       - 保底储备量
       - 保底预测业绩
       - 冲高储备量
       - 冲高预测业绩

    2. 根据本 sheet 字段计算：
       - 保底总储备量
       - 保底总预测业绩
       - 保底总预测业绩达标率
       - 冲高总储备量
       - 冲高总预测业绩
       - 冲高总预测业绩达标率
    """
    out = ensure_columns(
        target.reset_index(drop=True),
        BASE_METRICS + TOTAL_METRICS + RATE_METRICS,
    )

    for idx, row in out.iterrows():
        target_level = str(row.get("目标层面", "")).strip()
        target_object = row.get("目标对象")

        for metric in BASE_METRICS:
            out.at[idx, metric] = sum_detail_metric_by_target(
                detail=detail,
                target_level=target_level,
                target_object=target_object,
                metric=metric,
            )

        target_amount = to_number(row.get("预测业绩目标"))
        entered = to_number_zero(row.get("已进线"))
        achieved = to_number_zero(row.get("已达成预测业绩"))

        base_reserve = to_number(out.at[idx, "保底储备量"])
        base_perf = to_number(out.at[idx, "保底预测业绩"])
        high_reserve = to_number(out.at[idx, "冲高储备量"])
        high_perf = to_number(out.at[idx, "冲高预测业绩"])

        base_total_reserve = add_optional(entered, base_reserve)
        base_total_perf = add_optional(achieved, base_perf)

        high_total_reserve = add_optional(entered, high_reserve)
        high_total_perf = add_optional(achieved, high_perf)

        out.at[idx, "保底总储备量"] = base_total_reserve
        out.at[idx, "保底总预测业绩"] = base_total_perf
        out.at[idx, "保底总预测业绩达标率"] = safe_rate(
            base_total_perf,
            target_amount,
        )

        out.at[idx, "冲高总储备量"] = high_total_reserve
        out.at[idx, "冲高总预测业绩"] = high_total_perf
        out.at[idx, "冲高总预测业绩达标率"] = safe_rate(
            high_total_perf,
            target_amount,
        )

    return out
