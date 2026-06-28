from __future__ import annotations

import sys
from pathlib import Path
from tempfile import TemporaryDirectory

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from reserve_processor.constants import SHEET_DETAIL, SHEET_SCHEDULE, SHEET_TARGET  # noqa: E402
from reserve_processor.pipeline import process_workbook  # noqa: E402
from reserve_processor.utils import metric_date_col  # noqa: E402


def _write_workbook(
    path: Path,
    *,
    detail_rows: list[dict],
    schedule_rows: list[dict],
    target_rows: list[dict],
) -> None:
    detail = pd.DataFrame(detail_rows)
    schedule = pd.DataFrame(schedule_rows)
    target = pd.DataFrame(target_rows)

    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        detail.to_excel(writer, sheet_name=SHEET_DETAIL, index=False)
        schedule.to_excel(writer, sheet_name=SHEET_SCHEDULE, index=False)
        target.to_excel(writer, sheet_name=SHEET_TARGET, index=False)


def _base_detail_row() -> dict:
    return {
        "片区": "粤海片区",
        "BD": "张三",
        "省份": "广东省",
        "城市": "广州市",
        "区县": "天河区",
        "获客类型": "自然流",
        "启动日期": "2026-04-01",
        "停止日期": "2026-04-05",
        "项目可靠程度": "高",
        "课线项目": "编程",
        "冲高储备量": 70,
        "周储备提醒": "",
        "下周储备量": "",
        "下周启动日期": "",
        "下周停止日期": "",
        "BD准确率": "",
        "保底储备量": 50,
        "下周保底储备量": "",
        "冲高预测业绩": 7000,
        "保底预测业绩": 5000,
    }


def test_process_workbook_uses_zero_for_unmatched_schedule_metrics() -> None:
    schedule_row = {
        "课线项目": "机器人",
        "班期": "2026-04-10",
        "进线开始时间": "2026-04-01",
        "进线截止时间": "2026-04-03",
        "上课开始时间": "2026-04-10",
        "上课截止时间": "2026-04-20",
        "招生进度": "招生中",
        "已进线量": 10,
        "已达成预测业绩": 2000,
        "保底储备量": "",
        "保底预测业绩": "",
        "保底总储备量": "",
        "保底总预测业绩": "",
        "冲高储备量": "",
        "冲高预测业绩": "",
        "冲高总储备量": "",
        "冲高总预测业绩": "",
    }

    target_row = {
        "目标层面": "省份",
        "目标对象": "广东省",
        "预测业绩目标": 1000,
        "已进线": 0,
        "已达成预测业绩": 0,
    }

    with TemporaryDirectory() as tmp_dir:
        workbook_path = Path(tmp_dir) / "test.xlsx"
        _write_workbook(
            workbook_path,
            detail_rows=[_base_detail_row()],
            schedule_rows=[schedule_row],
            target_rows=[target_row],
        )

        result = process_workbook(workbook_path)

    row = result.schedule.iloc[0]
    assert row["保底储备量"] == 0.0
    assert row["保底预测业绩"] == 0.0
    assert row["冲高储备量"] == 0.0
    assert row["冲高预测业绩"] == 0.0
    assert row["保底总储备量"] == 10.0
    assert row["保底总预测业绩"] == 2000.0
    assert row["冲高总储备量"] == 10.0
    assert row["冲高总预测业绩"] == 2000.0


def test_process_workbook_uses_zero_for_unmatched_target_metrics() -> None:
    schedule_row = {
        "课线项目": "编程",
        "班期": "2026-04-10",
        "进线开始时间": "2026-04-01",
        "进线截止时间": "2026-04-03",
        "上课开始时间": "2026-04-10",
        "上课截止时间": "2026-04-20",
        "招生进度": "未启动",
        "已进线量": "",
        "已达成预测业绩": "",
        "保底储备量": "",
        "保底预测业绩": "",
        "保底总储备量": "",
        "保底总预测业绩": "",
        "冲高储备量": "",
        "冲高预测业绩": "",
        "冲高总储备量": "",
        "冲高总预测业绩": "",
    }

    target_row = {
        "目标层面": "省份",
        "目标对象": "海南省",
        "预测业绩目标": 1000,
        "已进线": 12,
        "已达成预测业绩": 30,
    }

    with TemporaryDirectory() as tmp_dir:
        workbook_path = Path(tmp_dir) / "test.xlsx"
        _write_workbook(
            workbook_path,
            detail_rows=[_base_detail_row()],
            schedule_rows=[schedule_row],
            target_rows=[target_row],
        )

        result = process_workbook(workbook_path)

    row = result.target.iloc[0]
    assert row["保底储备量"] == 0.0
    assert row["保底预测业绩"] == 0.0
    assert row["冲高储备量"] == 0.0
    assert row["冲高预测业绩"] == 0.0
    assert row["保底总储备量"] == 12.0
    assert row["保底总预测业绩"] == 30.0
    assert row["保底总预测业绩达标率"] == 0.03
    assert row["冲高总储备量"] == 12.0
    assert row["冲高总预测业绩"] == 30.0
    assert row["冲高总预测业绩达标率"] == 0.03


def test_process_workbook_treats_blank_target_entered_values_as_zero() -> None:
    schedule_row = {
        "课线项目": "编程",
        "班期": "2026-04-10",
        "进线开始时间": "2026-04-01",
        "进线截止时间": "2026-04-05",
        "上课开始时间": "2026-04-10",
        "上课截止时间": "2026-04-20",
        "招生进度": "未启动",
        "已进线量": "",
        "已达成预测业绩": "",
        "保底储备量": "",
        "保底预测业绩": "",
        "保底总储备量": "",
        "保底总预测业绩": "",
        "冲高储备量": "",
        "冲高预测业绩": "",
        "冲高总储备量": "",
        "冲高总预测业绩": "",
    }

    target_row = {
        "目标层面": "省份",
        "目标对象": "广东省",
        "预测业绩目标": 1000,
        "已进线": "",
        "已达成预测业绩": "",
    }

    with TemporaryDirectory() as tmp_dir:
        workbook_path = Path(tmp_dir) / "test.xlsx"
        _write_workbook(
            workbook_path,
            detail_rows=[_base_detail_row()],
            schedule_rows=[schedule_row],
            target_rows=[target_row],
        )

        result = process_workbook(workbook_path)

    row = result.target.iloc[0]
    assert row["保底储备量"] == 50.0
    assert row["保底预测业绩"] == 5000.0
    assert row["保底总储备量"] == 50.0
    assert row["保底总预测业绩"] == 5000.0
    assert row["冲高储备量"] == 70.0
    assert row["冲高预测业绩"] == 7000.0
    assert row["冲高总储备量"] == 70.0
    assert row["冲高总预测业绩"] == 7000.0


def test_process_workbook_quantizes_final_aggregates_without_float_tail() -> None:
    detail_rows = [
        {
            **_base_detail_row(),
            "保底储备量": 0.1,
            "冲高储备量": 0.1,
            "保底预测业绩": 0.1,
            "冲高预测业绩": 0.1,
            "启动日期": "2026-04-01",
            "停止日期": "2026-04-01",
        },
        {
            **_base_detail_row(),
            "保底储备量": 0.2,
            "冲高储备量": 0.2,
            "保底预测业绩": 0.2,
            "冲高预测业绩": 0.2,
            "启动日期": "2026-04-01",
            "停止日期": "2026-04-01",
        },
    ]

    schedule_row = {
        "课线项目": "编程",
        "班期": "2026-04-10",
        "进线开始时间": "2026-04-01",
        "进线截止时间": "2026-04-01",
        "上课开始时间": "2026-04-10",
        "上课截止时间": "2026-04-20",
        "招生进度": "招生中",
        "已进线量": 0,
        "已达成预测业绩": 0,
        "保底储备量": "",
        "保底预测业绩": "",
        "保底总储备量": "",
        "保底总预测业绩": "",
        "冲高储备量": "",
        "冲高预测业绩": "",
        "冲高总储备量": "",
        "冲高总预测业绩": "",
    }

    target_row = {
        "目标层面": "省份",
        "目标对象": "广东省",
        "预测业绩目标": 1,
        "已进线": 0,
        "已达成预测业绩": 0,
    }

    with TemporaryDirectory() as tmp_dir:
        workbook_path = Path(tmp_dir) / "test.xlsx"
        _write_workbook(
            workbook_path,
            detail_rows=detail_rows,
            schedule_rows=[schedule_row],
            target_rows=[target_row],
        )

        result = process_workbook(workbook_path)

    schedule_result = result.schedule.iloc[0]
    target_result = result.target.iloc[0]

    assert schedule_result["保底储备量"] == 0.3
    assert schedule_result["保底预测业绩"] == 0.3
    assert schedule_result["冲高储备量"] == 0.3
    assert schedule_result["冲高预测业绩"] == 0.3
    assert target_result["保底储备量"] == 0.3
    assert target_result["保底预测业绩"] == 0.3
    assert target_result["冲高储备量"] == 0.3
    assert target_result["冲高预测业绩"] == 0.3
    assert target_result["保底总预测业绩达标率"] == 0.3
    assert target_result["冲高总预测业绩达标率"] == 0.3


def test_process_workbook_uses_stretch_metrics_for_stretch_schedule_totals() -> None:
    schedule_rows = [
        {
            "课线项目": "编程",
            "班期": "2026-04-10",
            "进线开始时间": "2026-04-01",
            "进线截止时间": "2026-04-01",
            "上课开始时间": "2026-04-10",
            "上课截止时间": "2026-04-20",
            "招生进度": "未启动",
            "已进线量": "",
            "已达成预测业绩": "",
            "保底储备量": "",
            "保底预测业绩": "",
            "保底总储备量": "",
            "保底总预测业绩": "",
            "冲高储备量": "",
            "冲高预测业绩": "",
            "冲高总储备量": "",
            "冲高总预测业绩": "",
        },
        {
            "课线项目": "编程",
            "班期": "2026-04-11",
            "进线开始时间": "2026-04-01",
            "进线截止时间": "2026-04-01",
            "上课开始时间": "2026-04-11",
            "上课截止时间": "2026-04-21",
            "招生进度": "招生中",
            "已进线量": 10,
            "已达成预测业绩": 20,
            "保底储备量": "",
            "保底预测业绩": "",
            "保底总储备量": "",
            "保底总预测业绩": "",
            "冲高储备量": "",
            "冲高预测业绩": "",
            "冲高总储备量": "",
            "冲高总预测业绩": "",
        },
    ]

    target_row = {
        "目标层面": "省份",
        "目标对象": "广东省",
        "预测业绩目标": 1000,
        "已进线": 0,
        "已达成预测业绩": 0,
    }

    with TemporaryDirectory() as tmp_dir:
        workbook_path = Path(tmp_dir) / "test.xlsx"
        _write_workbook(
            workbook_path,
            detail_rows=[
                {
                    **_base_detail_row(),
                    "启动日期": "2026-04-01",
                    "停止日期": "2026-04-01",
                    "保底储备量": 50,
                    "保底预测业绩": 500,
                    "冲高储备量": 70,
                    "冲高预测业绩": 700,
                }
            ],
            schedule_rows=schedule_rows,
            target_rows=[target_row],
        )

        result = process_workbook(workbook_path)

    not_started = result.schedule.iloc[0]
    in_progress = result.schedule.iloc[1]

    assert not_started["保底总储备量"] == 50.0
    assert not_started["保底总预测业绩"] == 500.0
    assert not_started["冲高总储备量"] == 70.0
    assert not_started["冲高总预测业绩"] == 700.0

    assert in_progress["保底总储备量"] == 60.0
    assert in_progress["保底总预测业绩"] == 520.0
    assert in_progress["冲高总储备量"] == 80.0
    assert in_progress["冲高总预测业绩"] == 720.0


def test_process_workbook_zero_fills_detail_dates_outside_active_range() -> None:
    detail_rows = [
        {
            **_base_detail_row(),
            "启动日期": "2026-04-02",
            "停止日期": "2026-04-03",
            "保底储备量": 20,
            "冲高储备量": 40,
            "保底预测业绩": 200,
            "冲高预测业绩": 400,
        },
        {
            **_base_detail_row(),
            "BD": "李四",
            "启动日期": "2026-04-01",
            "停止日期": "2026-04-04",
            "保底储备量": 4,
            "冲高储备量": 8,
            "保底预测业绩": 40,
            "冲高预测业绩": 80,
        },
    ]

    schedule_row = {
        "课线项目": "编程",
        "班期": "2026-04-10",
        "进线开始时间": "2026-04-01",
        "进线截止时间": "2026-04-04",
        "上课开始时间": "2026-04-10",
        "上课截止时间": "2026-04-20",
        "招生进度": "未启动",
        "已进线量": "",
        "已达成预测业绩": "",
        "保底储备量": "",
        "保底预测业绩": "",
        "保底总储备量": "",
        "保底总预测业绩": "",
        "冲高储备量": "",
        "冲高预测业绩": "",
        "冲高总储备量": "",
        "冲高总预测业绩": "",
    }

    target_row = {
        "目标层面": "省份",
        "目标对象": "广东省",
        "预测业绩目标": 1000,
        "已进线": 0,
        "已达成预测业绩": 0,
    }

    with TemporaryDirectory() as tmp_dir:
        workbook_path = Path(tmp_dir) / "test.xlsx"
        _write_workbook(
            workbook_path,
            detail_rows=detail_rows,
            schedule_rows=[schedule_row],
            target_rows=[target_row],
        )

        result = process_workbook(workbook_path)

    row = result.detail.iloc[0]
    assert row[metric_date_col("保底储备量", pd.Timestamp("2026-04-01"))] == 0.0
    assert row[metric_date_col("保底储备量", pd.Timestamp("2026-04-02"))] == 10.0
    assert row[metric_date_col("保底储备量", pd.Timestamp("2026-04-03"))] == 10.0
    assert row[metric_date_col("保底储备量", pd.Timestamp("2026-04-04"))] == 0.0
    assert row[metric_date_col("冲高预测业绩", pd.Timestamp("2026-04-01"))] == 0.0
    assert row[metric_date_col("冲高预测业绩", pd.Timestamp("2026-04-04"))] == 0.0


def test_process_workbook_ignores_existing_export_date_only_columns() -> None:
    detail_rows = [
        {
            **_base_detail_row(),
            "启动日期": "2026-04-01",
            "停止日期": "2026-04-01",
            "保底储备量": 20,
            "冲高储备量": 40,
            "保底预测业绩": 200,
            "冲高预测业绩": 400,
            "4月1日": 999,
        }
    ]

    schedule_row = {
        "课线项目": "编程",
        "班期": "2026-04-10",
        "进线开始时间": "2026-04-01",
        "进线截止时间": "2026-04-01",
        "上课开始时间": "2026-04-10",
        "上课截止时间": "2026-04-20",
        "招生进度": "未启动",
        "已进线量": "",
        "已达成预测业绩": "",
        "保底储备量": "",
        "保底预测业绩": "",
        "保底总储备量": "",
        "保底总预测业绩": "",
        "冲高储备量": "",
        "冲高预测业绩": "",
        "冲高总储备量": "",
        "冲高总预测业绩": "",
    }

    target_row = {
        "目标层面": "省份",
        "目标对象": "广东省",
        "预测业绩目标": 1000,
        "已进线": 0,
        "已达成预测业绩": 0,
    }

    with TemporaryDirectory() as tmp_dir:
        workbook_path = Path(tmp_dir) / "test.xlsx"
        _write_workbook(
            workbook_path,
            detail_rows=detail_rows,
            schedule_rows=[schedule_row],
            target_rows=[target_row],
        )

        result = process_workbook(workbook_path)

    row = result.detail.iloc[0]
    assert "4月1日" not in result.detail.columns
    assert row[metric_date_col("保底储备量", pd.Timestamp("2026-04-01"))] == 20.0
    assert row[metric_date_col("冲高储备量", pd.Timestamp("2026-04-01"))] == 40.0
    assert row[metric_date_col("保底预测业绩", pd.Timestamp("2026-04-01"))] == 200.0
    assert row[metric_date_col("冲高预测业绩", pd.Timestamp("2026-04-01"))] == 400.0


def test_process_workbook_keeps_base_metrics_and_clears_stretch_metrics_for_ended_schedule() -> None:
    schedule_row = {
        "课线项目": "编程",
        "班期": "2026-04-10",
        "进线开始时间": "2026-04-01",
        "进线截止时间": "2026-04-01",
        "上课开始时间": "2026-04-10",
        "上课截止时间": "2026-04-20",
        "招生进度": "已结束",
        "已进线量": 10,
        "已达成预测业绩": 20,
        "保底储备量": "",
        "保底预测业绩": "",
        "保底总储备量": "",
        "保底总预测业绩": "",
        "冲高储备量": "",
        "冲高预测业绩": "",
        "冲高总储备量": "",
        "冲高总预测业绩": "",
    }

    target_row = {
        "目标层面": "省份",
        "目标对象": "广东省",
        "预测业绩目标": 1000,
        "已进线": 0,
        "已达成预测业绩": 0,
    }

    with TemporaryDirectory() as tmp_dir:
        workbook_path = Path(tmp_dir) / "test.xlsx"
        _write_workbook(
            workbook_path,
            detail_rows=[
                {
                    **_base_detail_row(),
                    "启动日期": "2026-04-01",
                    "停止日期": "2026-04-01",
                    "保底储备量": 50,
                    "保底预测业绩": 500,
                    "冲高储备量": 70,
                    "冲高预测业绩": 700,
                }
            ],
            schedule_rows=[schedule_row],
            target_rows=[target_row],
        )

        result = process_workbook(workbook_path)

    row = result.schedule.iloc[0]
    assert pd.isna(row["保底储备量"])
    assert pd.isna(row["保底预测业绩"])
    assert pd.isna(row["冲高储备量"])
    assert pd.isna(row["冲高预测业绩"])
    assert row["保底总储备量"] == 10.0
    assert row["保底总预测业绩"] == 20.0
    assert row["冲高总储备量"] == 10.0
    assert row["冲高总预测业绩"] == 20.0
