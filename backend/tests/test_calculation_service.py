from datetime import date
from decimal import Decimal

import pytest

from app.services.calculation_service import (
    InboundMetricInput,
    InboundRowInput,
    LockedScheduleInput,
    MonthlyClassMetrics,
    MonthlyClassScheduleInput,
    MonthlyTargetRowInput,
    ReserveDetailCalculationInput,
    TargetReserveMetricInput,
    aggregate_monthly_target_metrics,
    calculate_monthly_class_metrics,
    calculate_reserve_detail_metrics,
    finalize_monthly_class_metrics,
    match_inbound_to_schedule,
)


def test_calculate_reserve_detail_metrics_keeps_raw_values_without_two_decimal_rounding() -> None:
    result = calculate_reserve_detail_metrics(
        ReserveDetailCalculationInput(
            course_line="AI-无盒",
            project_reliability="高",
            start_date=date(2026, 5, 18),
            end_date=date(2026, 6, 16),
            base_reserve_qty=Decimal("10.239"),
            base_forecast_revenue=Decimal("20.235"),
            stretch_reserve_qty=Decimal("30.234"),
            stretch_forecast_revenue=Decimal("40.235"),
            next_week_start_date=date(2026, 5, 18),
            next_week_end_date=date(2026, 5, 24),
            next_week_base_reserve_qty=Decimal("1.005"),
            next_week_base_forecast_revenue=Decimal("2.005"),
            next_week_stretch_reserve_qty=Decimal("3.005"),
            next_week_stretch_forecast_revenue=Decimal("4.005"),
        )
    )

    assert result.base_reserve_qty == Decimal("10.239000")
    assert result.base_forecast_revenue == Decimal("20.235000")
    assert result.stretch_reserve_qty == Decimal("30.234000")
    assert result.stretch_forecast_revenue == Decimal("40.235000")
    assert result.next_week_base_reserve_qty == Decimal("1.005000")
    assert result.project_reliability == "高"


def test_calculate_reserve_detail_metrics_uses_inclusive_days_and_daily_split() -> None:
    result = calculate_reserve_detail_metrics(
        ReserveDetailCalculationInput(
            course_line="AI-无盒",
            start_date=date(2026, 5, 18),
            end_date=date(2026, 6, 16),
            next_week_start_date=date(2026, 5, 18),
            next_week_end_date=date(2026, 5, 24),
            base_reserve_qty=Decimal("300.00"),
            base_forecast_revenue=Decimal("600.00"),
            stretch_reserve_qty=Decimal("360.00"),
            stretch_forecast_revenue=Decimal("720.00"),
            next_week_base_reserve_qty=Decimal("70.00"),
            next_week_base_forecast_revenue=Decimal("140.00"),
            next_week_stretch_reserve_qty=Decimal("84.00"),
            next_week_stretch_forecast_revenue=Decimal("168.00"),
        )
    )

    assert result.customer_days == 30
    assert result.next_week_customer_days == 7
    assert result.base_reserve_daily_next_week == Decimal("10.000000")
    assert result.base_reserve_daily_other == Decimal("10.000000")
    assert result.base_revenue_daily_next_week == Decimal("20.000000")
    assert result.stretch_reserve_daily_other == Decimal("12.000000")


def test_calculate_monthly_class_metrics_rolls_up_by_locked_schedule_window() -> None:
    reserve_result = calculate_reserve_detail_metrics(
        ReserveDetailCalculationInput(
            course_line="AI-无盒",
            start_date=date(2026, 5, 18),
            end_date=date(2026, 6, 16),
            next_week_start_date=date(2026, 5, 18),
            next_week_end_date=date(2026, 5, 24),
            base_reserve_qty=Decimal("300.00"),
            base_forecast_revenue=Decimal("600.00"),
            stretch_reserve_qty=Decimal("360.00"),
            stretch_forecast_revenue=Decimal("720.00"),
            next_week_base_reserve_qty=Decimal("70.00"),
            next_week_base_forecast_revenue=Decimal("140.00"),
            next_week_stretch_reserve_qty=Decimal("84.00"),
            next_week_stretch_forecast_revenue=Decimal("168.00"),
        )
    )

    metrics = calculate_monthly_class_metrics(
        MonthlyClassScheduleInput(
            course_line="AI-无盒",
            inbound_start_date=date(2026, 5, 18),
            inbound_end_date=date(2026, 5, 24),
        ),
        [reserve_result],
    )

    assert metrics.calc_base_reserve_qty == Decimal("70.00")
    assert metrics.calc_base_forecast_revenue == Decimal("140.00")
    assert metrics.calc_stretch_reserve_qty == Decimal("84.00")
    assert metrics.calc_stretch_forecast_revenue == Decimal("168.00")


def test_finalize_monthly_class_metrics_nullifies_stretch_for_ended_status() -> None:
    final_metrics = finalize_monthly_class_metrics(
        enrollment_status="已结束",
        calc_metrics=MonthlyClassMetrics(
            calc_base_reserve_qty=Decimal("70.00"),
            calc_base_forecast_revenue=Decimal("140.00"),
            calc_stretch_reserve_qty=Decimal("84.00"),
            calc_stretch_forecast_revenue=Decimal("168.00"),
        ),
    )

    assert final_metrics.final_base_reserve_qty == Decimal("70.00")
    assert final_metrics.final_stretch_reserve_qty is None
    assert final_metrics.final_stretch_forecast_revenue is None
    assert final_metrics.calc_rule == "ended_status_nullify_stretch"


def test_aggregate_monthly_target_metrics_matches_doc_formulas() -> None:
    target_metrics = aggregate_monthly_target_metrics(
        MonthlyTargetRowInput(target_level="片区", area_name="粤海片区", target_revenue=Decimal("1000.00")),
        reserve_rows=[
            TargetReserveMetricInput(
                area_name="粤海片区",
                base_reserve_qty=Decimal("300.00"),
                base_forecast_revenue=Decimal("400.00"),
                stretch_reserve_qty=Decimal("360.00"),
                stretch_forecast_revenue=Decimal("480.00"),
            )
        ],
        inbound_rows=[
            InboundMetricInput(
                area_name="粤海片区",
                final_inbound_qty=Decimal("20.00"),
                final_achieved_revenue=Decimal("100.00"),
            )
        ],
    )

    assert target_metrics.base_total_reserve_qty == Decimal("320.00")
    assert target_metrics.base_total_revenue == Decimal("500.00")
    assert target_metrics.base_achievement_rate == Decimal("0.500000")
    assert target_metrics.stretch_total_reserve_qty == Decimal("380.00")
    assert target_metrics.stretch_total_revenue == Decimal("580.00")
    assert target_metrics.stretch_achievement_rate == Decimal("0.580000")


def test_aggregate_monthly_target_metrics_respects_full_scope_not_only_primary_dimension() -> None:
    target_metrics = aggregate_monthly_target_metrics(
        MonthlyTargetRowInput(
            target_level="省份",
            area_name="粤海片区",
            province_name="广东省",
            target_revenue=Decimal("1000.00"),
        ),
        reserve_rows=[
            TargetReserveMetricInput(
                area_name="粤海片区",
                province_name="广东省",
                base_reserve_qty=Decimal("100.00"),
                base_forecast_revenue=Decimal("200.00"),
            ),
            TargetReserveMetricInput(
                area_name="浙闽片区",
                province_name="广东省",
                base_reserve_qty=Decimal("999.00"),
                base_forecast_revenue=Decimal("999.00"),
            ),
        ],
        inbound_rows=[],
    )

    assert target_metrics.base_reserve_qty == Decimal("100.00")
    assert target_metrics.base_forecast_revenue == Decimal("200.00")


def test_match_inbound_to_schedule_uses_locked_class_window() -> None:
    match_result = match_inbound_to_schedule(
        InboundRowInput(
            course_line="AI-无盒",
            inbound_date=date(2026, 5, 20),
            inbound_qty=Decimal("10.125"),
            achieved_revenue=Decimal("100.125"),
        ),
        [
            LockedScheduleInput(
                schedule_id=1,
                course_line="AI-无盒",
                class_key="2026-06-ai-1",
                class_seq=1,
                class_name="第1期",
                inbound_start_date=date(2026, 5, 18),
                inbound_end_date=date(2026, 5, 24),
            )
        ],
    )

    assert match_result.matched_schedule_id == 1
    assert match_result.is_in_class_period is True
    assert match_result.final_inbound_qty == Decimal("10.125000")
    assert match_result.final_achieved_revenue == Decimal("100.125000")


def test_calculate_reserve_detail_metrics_rejects_invalid_dates() -> None:
    with pytest.raises(ValueError):
        calculate_reserve_detail_metrics(
            ReserveDetailCalculationInput(
                course_line="AI-无盒",
                start_date=date(2026, 6, 1),
                end_date=date(2026, 5, 31),
                base_reserve_qty=Decimal("10.00"),
            )
        )
