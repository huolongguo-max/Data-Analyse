from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP
from typing import Iterable


# Keep raw metric values instead of rounding them to integers or 2 decimals during calculation.
RAW_QUANT = Decimal("0.000001")
DAILY_QUANT = Decimal("0.000001")
RATE_QUANT = Decimal("0.000001")
ZERO_2 = Decimal("0.000000")
ZERO_6 = Decimal("0.000000")

ENDED_ENROLLMENT_STATUSES = frozenset({"已结束"})

TARGET_LEVEL_FIELD_MAP = {
    "area": "area_name",
    "片区": "area_name",
    "province": "province_name",
    "省份": "province_name",
    "city": "city_name",
    "城市": "city_name",
    "bd": "bd_name",
    "BD": "bd_name",
}


def quantize_decimal(value: Decimal | int | float | str | None, quant: Decimal = RAW_QUANT) -> Decimal | None:
    if value is None:
        return None
    return Decimal(str(value)).quantize(quant, rounding=ROUND_HALF_UP)


def inclusive_days(start_date: date | None, end_date: date | None) -> int:
    if start_date is None or end_date is None:
        raise ValueError("开始日期和结束日期不能为空。")
    if end_date < start_date:
        raise ValueError("结束日期不能早于开始日期。")
    return (end_date - start_date).days + 1


def calculate_next_week_customer_days(next_week_start_date: date | None, next_week_end_date: date | None) -> int:
    if next_week_start_date is None or next_week_end_date is None:
        return 0
    return inclusive_days(next_week_start_date, next_week_end_date)


def overlap_days(start_a: date, end_a: date, start_b: date, end_b: date) -> int:
    overlap_start = max(start_a, start_b)
    overlap_end = min(end_a, end_b)
    if overlap_end < overlap_start:
        return 0
    return (overlap_end - overlap_start).days + 1


def sum_decimals(values: Iterable[Decimal | None], quant: Decimal = RAW_QUANT) -> Decimal:
    total = sum(((value or Decimal("0")) for value in values), Decimal("0"))
    return total.quantize(quant, rounding=ROUND_HALF_UP)


def safe_rate(numerator: Decimal | None, denominator: Decimal | None) -> Decimal | None:
    if numerator is None or denominator in (None, Decimal("0"), ZERO_2):
        return None
    return (numerator / denominator).quantize(RATE_QUANT, rounding=ROUND_HALF_UP)


@dataclass(frozen=True)
class DailySplit:
    next_week_daily: Decimal
    other_daily: Decimal


@dataclass(frozen=True)
class DailyMetricSegment:
    start_date: date
    end_date: date
    daily_amount: Decimal


@dataclass(frozen=True)
class ReserveDetailCalculationInput:
    course_line: str | None
    area_name: str | None = None
    province_name: str | None = None
    city_name: str | None = None
    bd_name: str | None = None
    acquisition_type: str | None = None
    project_reliability: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    next_week_start_date: date | None = None
    next_week_end_date: date | None = None
    base_reserve_qty: Decimal | int | float | str | None = None
    base_forecast_revenue: Decimal | int | float | str | None = None
    stretch_reserve_qty: Decimal | int | float | str | None = None
    stretch_forecast_revenue: Decimal | int | float | str | None = None
    next_week_base_reserve_qty: Decimal | int | float | str | None = None
    next_week_base_forecast_revenue: Decimal | int | float | str | None = None
    next_week_stretch_reserve_qty: Decimal | int | float | str | None = None
    next_week_stretch_forecast_revenue: Decimal | int | float | str | None = None


@dataclass(frozen=True)
class ReserveDetailCalculationResult:
    course_line: str | None
    area_name: str | None
    province_name: str | None
    city_name: str | None
    bd_name: str | None
    acquisition_type: str | None
    project_reliability: str | None
    start_date: date
    end_date: date
    next_week_start_date: date | None
    next_week_end_date: date | None
    base_reserve_qty: Decimal | None
    base_forecast_revenue: Decimal | None
    stretch_reserve_qty: Decimal | None
    stretch_forecast_revenue: Decimal | None
    next_week_base_reserve_qty: Decimal | None
    next_week_base_forecast_revenue: Decimal | None
    next_week_stretch_reserve_qty: Decimal | None
    next_week_stretch_forecast_revenue: Decimal | None
    customer_days: int
    next_week_customer_days: int
    base_reserve_daily_next_week: Decimal
    base_reserve_daily_other: Decimal
    base_revenue_daily_next_week: Decimal
    base_revenue_daily_other: Decimal
    stretch_reserve_daily_next_week: Decimal
    stretch_reserve_daily_other: Decimal
    stretch_revenue_daily_next_week: Decimal
    stretch_revenue_daily_other: Decimal


@dataclass(frozen=True)
class MonthlyClassScheduleInput:
    course_line: str
    inbound_start_date: date
    inbound_end_date: date


@dataclass(frozen=True)
class MonthlyClassMetrics:
    calc_base_reserve_qty: Decimal
    calc_base_forecast_revenue: Decimal
    calc_stretch_reserve_qty: Decimal
    calc_stretch_forecast_revenue: Decimal


@dataclass(frozen=True)
class MonthlyClassFinalMetrics:
    calc_base_reserve_qty: Decimal
    calc_base_forecast_revenue: Decimal
    calc_stretch_reserve_qty: Decimal
    calc_stretch_forecast_revenue: Decimal
    final_base_reserve_qty: Decimal
    final_base_forecast_revenue: Decimal
    final_stretch_reserve_qty: Decimal | None
    final_stretch_forecast_revenue: Decimal | None
    calc_rule: str


@dataclass(frozen=True)
class MonthlyTargetRowInput:
    target_level: str | None
    area_name: str | None = None
    province_name: str | None = None
    city_name: str | None = None
    bd_name: str | None = None
    target_revenue: Decimal | int | float | str | None = None


@dataclass(frozen=True)
class TargetReserveMetricInput:
    area_name: str | None = None
    province_name: str | None = None
    city_name: str | None = None
    bd_name: str | None = None
    base_reserve_qty: Decimal | int | float | str | None = None
    base_forecast_revenue: Decimal | int | float | str | None = None
    stretch_reserve_qty: Decimal | int | float | str | None = None
    stretch_forecast_revenue: Decimal | int | float | str | None = None


@dataclass(frozen=True)
class InboundMetricInput:
    area_name: str | None = None
    province_name: str | None = None
    city_name: str | None = None
    bd_name: str | None = None
    inbound_qty: Decimal | int | float | str | None = None
    achieved_revenue: Decimal | int | float | str | None = None
    final_inbound_qty: Decimal | int | float | str | None = None
    final_achieved_revenue: Decimal | int | float | str | None = None


@dataclass(frozen=True)
class MonthlyTargetMetrics:
    inbound_qty: Decimal
    achieved_revenue: Decimal
    base_reserve_qty: Decimal
    base_forecast_revenue: Decimal
    base_total_reserve_qty: Decimal
    base_total_revenue: Decimal
    base_achievement_rate: Decimal | None
    stretch_reserve_qty: Decimal
    stretch_forecast_revenue: Decimal
    stretch_total_reserve_qty: Decimal
    stretch_total_revenue: Decimal
    stretch_achievement_rate: Decimal | None


@dataclass(frozen=True)
class InboundRowInput:
    course_line: str | None
    inbound_date: date | None
    inbound_qty: Decimal | int | float | str | None = None
    achieved_revenue: Decimal | int | float | str | None = None


@dataclass(frozen=True)
class LockedScheduleInput:
    schedule_id: int
    course_line: str
    class_key: str
    class_seq: int | None
    class_name: str | None
    inbound_start_date: date
    inbound_end_date: date


@dataclass(frozen=True)
class InboundMatchResult:
    matched_schedule_id: int | None
    matched_class_key: str | None
    matched_class_seq: int | None
    matched_class_name: str | None
    is_in_class_period: bool
    final_inbound_qty: Decimal | None
    final_achieved_revenue: Decimal | None


def split_metric_into_daily_values(
    *,
    total_amount: Decimal | int | float | str | None,
    next_week_amount: Decimal | int | float | str | None,
    customer_days: int,
    next_week_customer_days: int,
) -> DailySplit:
    total = quantize_decimal(total_amount, RAW_QUANT)
    next_week = quantize_decimal(next_week_amount, RAW_QUANT)

    if total is None:
        return DailySplit(next_week_daily=ZERO_6, other_daily=ZERO_6)

    if next_week_customer_days > 0 and next_week is not None:
        next_week_daily = (next_week / Decimal(next_week_customer_days)).quantize(DAILY_QUANT, rounding=ROUND_HALF_UP)
        remaining_days = customer_days - next_week_customer_days
        remaining_amount = total - next_week

        if remaining_days < 0:
            raise ValueError("下周获客天数不能大于总获客天数。")
        if remaining_days == 0:
            if remaining_amount != Decimal("0.00"):
                raise ValueError("当下周获客天数等于总获客天数时，剩余量必须为 0。")
            return DailySplit(next_week_daily=next_week_daily, other_daily=ZERO_6)

        other_daily = (remaining_amount / Decimal(remaining_days)).quantize(DAILY_QUANT, rounding=ROUND_HALF_UP)
        return DailySplit(next_week_daily=next_week_daily, other_daily=other_daily)

    other_daily = (total / Decimal(customer_days)).quantize(DAILY_QUANT, rounding=ROUND_HALF_UP)
    return DailySplit(next_week_daily=ZERO_6, other_daily=other_daily)


def _build_metric_segments(
    *,
    start_date: date,
    end_date: date,
    next_week_start_date: date | None,
    next_week_end_date: date | None,
    daily_split: DailySplit,
    use_next_week_split: bool,
) -> list[DailyMetricSegment]:
    if not use_next_week_split or next_week_start_date is None or next_week_end_date is None:
        return [DailyMetricSegment(start_date=start_date, end_date=end_date, daily_amount=daily_split.other_daily)]

    if next_week_start_date < start_date or next_week_end_date > end_date:
        raise ValueError("下周日期区间必须落在启动日期和停止日期内。")

    segments: list[DailyMetricSegment] = []
    if next_week_start_date > start_date:
        segments.append(
            DailyMetricSegment(
                start_date=start_date,
                end_date=next_week_start_date - timedelta(days=1),
                daily_amount=daily_split.other_daily,
            )
        )

    segments.append(
        DailyMetricSegment(
            start_date=next_week_start_date,
            end_date=next_week_end_date,
            daily_amount=daily_split.next_week_daily,
        )
    )

    if next_week_end_date < end_date:
        segments.append(
            DailyMetricSegment(
                start_date=next_week_end_date + timedelta(days=1),
                end_date=end_date,
                daily_amount=daily_split.other_daily,
            )
        )

    return segments


def calculate_reserve_detail_metrics(row: ReserveDetailCalculationInput) -> ReserveDetailCalculationResult:
    start_date = row.start_date
    end_date = row.end_date
    customer_days = inclusive_days(start_date, end_date)
    next_week_customer_days = calculate_next_week_customer_days(row.next_week_start_date, row.next_week_end_date)

    base_reserve_split = split_metric_into_daily_values(
        total_amount=row.base_reserve_qty,
        next_week_amount=row.next_week_base_reserve_qty,
        customer_days=customer_days,
        next_week_customer_days=next_week_customer_days,
    )
    base_revenue_split = split_metric_into_daily_values(
        total_amount=row.base_forecast_revenue,
        next_week_amount=row.next_week_base_forecast_revenue,
        customer_days=customer_days,
        next_week_customer_days=next_week_customer_days,
    )
    stretch_reserve_split = split_metric_into_daily_values(
        total_amount=row.stretch_reserve_qty,
        next_week_amount=row.next_week_stretch_reserve_qty,
        customer_days=customer_days,
        next_week_customer_days=next_week_customer_days,
    )
    stretch_revenue_split = split_metric_into_daily_values(
        total_amount=row.stretch_forecast_revenue,
        next_week_amount=row.next_week_stretch_forecast_revenue,
        customer_days=customer_days,
        next_week_customer_days=next_week_customer_days,
    )

    return ReserveDetailCalculationResult(
        course_line=row.course_line,
        area_name=row.area_name,
        province_name=row.province_name,
        city_name=row.city_name,
        bd_name=row.bd_name,
        acquisition_type=row.acquisition_type,
        project_reliability=row.project_reliability,
        start_date=start_date,
        end_date=end_date,
        next_week_start_date=row.next_week_start_date,
        next_week_end_date=row.next_week_end_date,
        base_reserve_qty=quantize_decimal(row.base_reserve_qty, RAW_QUANT),
        base_forecast_revenue=quantize_decimal(row.base_forecast_revenue, RAW_QUANT),
        stretch_reserve_qty=quantize_decimal(row.stretch_reserve_qty, RAW_QUANT),
        stretch_forecast_revenue=quantize_decimal(row.stretch_forecast_revenue, RAW_QUANT),
        next_week_base_reserve_qty=quantize_decimal(row.next_week_base_reserve_qty, RAW_QUANT),
        next_week_base_forecast_revenue=quantize_decimal(row.next_week_base_forecast_revenue, RAW_QUANT),
        next_week_stretch_reserve_qty=quantize_decimal(row.next_week_stretch_reserve_qty, RAW_QUANT),
        next_week_stretch_forecast_revenue=quantize_decimal(row.next_week_stretch_forecast_revenue, RAW_QUANT),
        customer_days=customer_days,
        next_week_customer_days=next_week_customer_days,
        base_reserve_daily_next_week=base_reserve_split.next_week_daily,
        base_reserve_daily_other=base_reserve_split.other_daily,
        base_revenue_daily_next_week=base_revenue_split.next_week_daily,
        base_revenue_daily_other=base_revenue_split.other_daily,
        stretch_reserve_daily_next_week=stretch_reserve_split.next_week_daily,
        stretch_reserve_daily_other=stretch_reserve_split.other_daily,
        stretch_revenue_daily_next_week=stretch_revenue_split.next_week_daily,
        stretch_revenue_daily_other=stretch_revenue_split.other_daily,
    )


def reserve_metric_segments(
    row: ReserveDetailCalculationResult,
    *,
    total_amount_field: str,
    next_week_amount_field: str,
    next_week_daily_field: str,
    other_daily_field: str,
) -> list[DailyMetricSegment]:
    total_amount = getattr(row, total_amount_field)
    next_week_amount = getattr(row, next_week_amount_field)
    next_week_daily = getattr(row, next_week_daily_field)
    other_daily = getattr(row, other_daily_field)

    return _build_metric_segments(
        start_date=row.start_date,
        end_date=row.end_date,
        next_week_start_date=row.next_week_start_date,
        next_week_end_date=row.next_week_end_date,
        daily_split=DailySplit(next_week_daily=next_week_daily, other_daily=other_daily),
        use_next_week_split=row.next_week_customer_days > 0 and next_week_amount is not None and total_amount is not None,
    )


def calculate_monthly_class_metrics(
    schedule: MonthlyClassScheduleInput,
    reserve_rows: Iterable[ReserveDetailCalculationResult],
) -> MonthlyClassMetrics:
    base_reserve_total = Decimal("0")
    base_revenue_total = Decimal("0")
    stretch_reserve_total = Decimal("0")
    stretch_revenue_total = Decimal("0")

    for reserve_row in reserve_rows:
        if reserve_row.course_line != schedule.course_line:
            continue

        for segment in reserve_metric_segments(
            reserve_row,
            total_amount_field="base_reserve_qty",
            next_week_amount_field="next_week_base_reserve_qty",
            next_week_daily_field="base_reserve_daily_next_week",
            other_daily_field="base_reserve_daily_other",
        ):
            base_reserve_total += segment.daily_amount * overlap_days(
                segment.start_date,
                segment.end_date,
                schedule.inbound_start_date,
                schedule.inbound_end_date,
            )

        for segment in reserve_metric_segments(
            reserve_row,
            total_amount_field="base_forecast_revenue",
            next_week_amount_field="next_week_base_forecast_revenue",
            next_week_daily_field="base_revenue_daily_next_week",
            other_daily_field="base_revenue_daily_other",
        ):
            base_revenue_total += segment.daily_amount * overlap_days(
                segment.start_date,
                segment.end_date,
                schedule.inbound_start_date,
                schedule.inbound_end_date,
            )

        for segment in reserve_metric_segments(
            reserve_row,
            total_amount_field="stretch_reserve_qty",
            next_week_amount_field="next_week_stretch_reserve_qty",
            next_week_daily_field="stretch_reserve_daily_next_week",
            other_daily_field="stretch_reserve_daily_other",
        ):
            stretch_reserve_total += segment.daily_amount * overlap_days(
                segment.start_date,
                segment.end_date,
                schedule.inbound_start_date,
                schedule.inbound_end_date,
            )

        for segment in reserve_metric_segments(
            reserve_row,
            total_amount_field="stretch_forecast_revenue",
            next_week_amount_field="next_week_stretch_forecast_revenue",
            next_week_daily_field="stretch_revenue_daily_next_week",
            other_daily_field="stretch_revenue_daily_other",
        ):
            stretch_revenue_total += segment.daily_amount * overlap_days(
                segment.start_date,
                segment.end_date,
                schedule.inbound_start_date,
                schedule.inbound_end_date,
            )

    return MonthlyClassMetrics(
        calc_base_reserve_qty=base_reserve_total.quantize(RAW_QUANT, rounding=ROUND_HALF_UP),
        calc_base_forecast_revenue=base_revenue_total.quantize(RAW_QUANT, rounding=ROUND_HALF_UP),
        calc_stretch_reserve_qty=stretch_reserve_total.quantize(RAW_QUANT, rounding=ROUND_HALF_UP),
        calc_stretch_forecast_revenue=stretch_revenue_total.quantize(RAW_QUANT, rounding=ROUND_HALF_UP),
    )


def finalize_monthly_class_metrics(
    *,
    enrollment_status: str | None,
    calc_metrics: MonthlyClassMetrics,
    ended_statuses: frozenset[str] = ENDED_ENROLLMENT_STATUSES,
) -> MonthlyClassFinalMetrics:
    if enrollment_status in ended_statuses:
        return MonthlyClassFinalMetrics(
            calc_base_reserve_qty=calc_metrics.calc_base_reserve_qty,
            calc_base_forecast_revenue=calc_metrics.calc_base_forecast_revenue,
            calc_stretch_reserve_qty=calc_metrics.calc_stretch_reserve_qty,
            calc_stretch_forecast_revenue=calc_metrics.calc_stretch_forecast_revenue,
            final_base_reserve_qty=calc_metrics.calc_base_reserve_qty,
            final_base_forecast_revenue=calc_metrics.calc_base_forecast_revenue,
            final_stretch_reserve_qty=None,
            final_stretch_forecast_revenue=None,
            calc_rule="ended_status_nullify_stretch",
        )

    return MonthlyClassFinalMetrics(
        calc_base_reserve_qty=calc_metrics.calc_base_reserve_qty,
        calc_base_forecast_revenue=calc_metrics.calc_base_forecast_revenue,
        calc_stretch_reserve_qty=calc_metrics.calc_stretch_reserve_qty,
        calc_stretch_forecast_revenue=calc_metrics.calc_stretch_forecast_revenue,
        final_base_reserve_qty=calc_metrics.calc_base_reserve_qty,
        final_base_forecast_revenue=calc_metrics.calc_base_forecast_revenue,
        final_stretch_reserve_qty=calc_metrics.calc_stretch_reserve_qty,
        final_stretch_forecast_revenue=calc_metrics.calc_stretch_forecast_revenue,
        calc_rule="calculated_override_prefilled",
    )


def resolve_target_dimension_field(target_row: MonthlyTargetRowInput) -> str:
    if target_row.target_level in TARGET_LEVEL_FIELD_MAP:
        return TARGET_LEVEL_FIELD_MAP[target_row.target_level]

    for field_name in ("bd_name", "city_name", "province_name", "area_name"):
        if getattr(target_row, field_name):
            return field_name

    raise ValueError("无法识别目标表的统计维度。")


def _matches_target_scope(target_row: MonthlyTargetRowInput, record: object, dimension_field: str) -> bool:
    if getattr(target_row, dimension_field) is None:
        return False

    for field_name in ("area_name", "province_name", "city_name", "bd_name"):
        target_value = getattr(target_row, field_name)
        if target_value is None:
            continue
        if getattr(record, field_name, None) != target_value:
            return False

    return True


def aggregate_monthly_target_metrics(
    target_row: MonthlyTargetRowInput,
    reserve_rows: Iterable[TargetReserveMetricInput],
    inbound_rows: Iterable[InboundMetricInput],
) -> MonthlyTargetMetrics:
    dimension_field = resolve_target_dimension_field(target_row)

    matched_reserve_rows = [row for row in reserve_rows if _matches_target_scope(target_row, row, dimension_field)]
    matched_inbound_rows = [row for row in inbound_rows if _matches_target_scope(target_row, row, dimension_field)]

    inbound_qty = sum_decimals(
        quantize_decimal(row.final_inbound_qty if row.final_inbound_qty is not None else row.inbound_qty, RAW_QUANT)
        for row in matched_inbound_rows
    )
    achieved_revenue = sum_decimals(
        quantize_decimal(
            row.final_achieved_revenue if row.final_achieved_revenue is not None else row.achieved_revenue,
            RAW_QUANT,
        )
        for row in matched_inbound_rows
    )

    base_reserve_qty = sum_decimals(quantize_decimal(row.base_reserve_qty, RAW_QUANT) for row in matched_reserve_rows)
    base_forecast_revenue = sum_decimals(
        quantize_decimal(row.base_forecast_revenue, RAW_QUANT) for row in matched_reserve_rows
    )
    stretch_reserve_qty = sum_decimals(
        quantize_decimal(row.stretch_reserve_qty, RAW_QUANT) for row in matched_reserve_rows
    )
    stretch_forecast_revenue = sum_decimals(
        quantize_decimal(row.stretch_forecast_revenue, RAW_QUANT) for row in matched_reserve_rows
    )

    base_total_reserve_qty = (inbound_qty + base_reserve_qty).quantize(RAW_QUANT, rounding=ROUND_HALF_UP)
    base_total_revenue = (achieved_revenue + base_forecast_revenue).quantize(RAW_QUANT, rounding=ROUND_HALF_UP)
    stretch_total_reserve_qty = (inbound_qty + stretch_reserve_qty).quantize(RAW_QUANT, rounding=ROUND_HALF_UP)
    stretch_total_revenue = (achieved_revenue + stretch_forecast_revenue).quantize(RAW_QUANT, rounding=ROUND_HALF_UP)

    target_revenue = quantize_decimal(target_row.target_revenue, RAW_QUANT)

    return MonthlyTargetMetrics(
        inbound_qty=inbound_qty,
        achieved_revenue=achieved_revenue,
        base_reserve_qty=base_reserve_qty,
        base_forecast_revenue=base_forecast_revenue,
        base_total_reserve_qty=base_total_reserve_qty,
        base_total_revenue=base_total_revenue,
        base_achievement_rate=safe_rate(base_total_revenue, target_revenue),
        stretch_reserve_qty=stretch_reserve_qty,
        stretch_forecast_revenue=stretch_forecast_revenue,
        stretch_total_reserve_qty=stretch_total_reserve_qty,
        stretch_total_revenue=stretch_total_revenue,
        stretch_achievement_rate=safe_rate(stretch_total_revenue, target_revenue),
    )


def match_inbound_to_schedule(
    inbound_row: InboundRowInput,
    schedules: Iterable[LockedScheduleInput],
) -> InboundMatchResult:
    inbound_qty = quantize_decimal(inbound_row.inbound_qty, RAW_QUANT)
    achieved_revenue = quantize_decimal(inbound_row.achieved_revenue, RAW_QUANT)

    if inbound_row.inbound_date is None or inbound_row.course_line is None:
        return InboundMatchResult(
            matched_schedule_id=None,
            matched_class_key=None,
            matched_class_seq=None,
            matched_class_name=None,
            is_in_class_period=False,
            final_inbound_qty=inbound_qty,
            final_achieved_revenue=achieved_revenue,
        )

    for schedule in schedules:
        if schedule.course_line != inbound_row.course_line:
            continue
        if schedule.inbound_start_date <= inbound_row.inbound_date <= schedule.inbound_end_date:
            return InboundMatchResult(
                matched_schedule_id=schedule.schedule_id,
                matched_class_key=schedule.class_key,
                matched_class_seq=schedule.class_seq,
                matched_class_name=schedule.class_name,
                is_in_class_period=True,
                final_inbound_qty=inbound_qty,
                final_achieved_revenue=achieved_revenue,
            )

    return InboundMatchResult(
        matched_schedule_id=None,
        matched_class_key=None,
        matched_class_seq=None,
        matched_class_name=None,
        is_in_class_period=False,
        final_inbound_qty=inbound_qty,
        final_achieved_revenue=achieved_revenue,
    )
