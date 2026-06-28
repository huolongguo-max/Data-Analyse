from __future__ import annotations

from decimal import Decimal
from types import SimpleNamespace
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.common.exceptions import NotFoundError, ValidationError
from app.models import MonthlySnapshotMetric, Period, UploadBatch
from app.schemas.dashboard import DashboardCompareResponse, DashboardSingleResponse
from app.services.location_config import FIXED_DIMENSION_ORDER, resolve_area_for_province
from app.services.upload_sequence_service import build_previous_batch_map, get_batch_record_mmdd_value


DIMENSION_LEVEL_ALIASES = {
    "national": "national",
    "country": "national",
    "all": "national",
    "area": "area",
    "province": "province",
    "city": "city",
    "bd": "bd",
}

SCENARIO_FIELDS = {
    "base": [
        "base_reserve_qty",
        "base_forecast_revenue",
        "base_total_reserve_qty",
        "base_total_revenue",
        "base_achievement_rate",
    ],
    "stretch": [
        "stretch_reserve_qty",
        "stretch_forecast_revenue",
        "stretch_total_reserve_qty",
        "stretch_total_revenue",
        "stretch_achievement_rate",
    ],
}

COMMON_FACT_FIELDS = [
    "dimension_key",
    "dimension_name",
    "target_revenue",
    "inbound_qty",
    "achieved_revenue",
    "course_line",
    "class_key",
    "class_name",
    "area_name",
    "province_name",
    "city_name",
    "bd_name",
    "acquisition_type",
    "project_reliability",
]

COMPARE_BASE_FIELDS = [
    "target_revenue",
    "inbound_qty",
    "achieved_revenue",
]


def _resolve_period_batch(db: Session, period_code: str, upload_seq: int) -> tuple[Period, UploadBatch]:
    period = db.scalar(select(Period).where(Period.period_code == period_code))
    if period is None:
        raise NotFoundError(f"Period not found: {period_code}")

    batch = db.scalar(
        select(UploadBatch).where(
            UploadBatch.period_id == period.period_id,
            UploadBatch.upload_seq == upload_seq,
        )
    )
    if batch is None:
        raise NotFoundError(f"Upload batch not found: {period_code} #{upload_seq}")

    return period, batch


def _normalize_dimension_level(value: str) -> str:
    normalized = DIMENSION_LEVEL_ALIASES.get(value.strip().lower())
    if normalized is None:
        raise ValidationError(f"Unsupported dimension_level: {value}")
    return normalized


def _normalize_scenario(value: str) -> str:
    scenario = value.strip().lower()
    if scenario not in {"base", "stretch", "all"}:
        raise ValidationError(f"Unsupported scenario: {value}")
    return scenario


def _scenario_metric_fields(scenario: str) -> list[str]:
    if scenario == "all":
        return SCENARIO_FIELDS["base"] + SCENARIO_FIELDS["stretch"]
    return SCENARIO_FIELDS[scenario]


def _serialize_value(value: Any) -> Any:
    if isinstance(value, Decimal):
        return float(value)
    return value


def _inbound_progress_rate(inbound_qty: Decimal | None, total_reserve_qty: Decimal | None) -> float:
    denominator = total_reserve_qty or Decimal("0")
    if not denominator:
        return 0.0
    numerator = inbound_qty or Decimal("0")
    return _serialize_value(numerator / denominator)


def _serialize_fact_row(row: MonthlySnapshotMetric, scenario: str) -> dict[str, Any]:
    data = {
        "dimension_level": row.dimension_level,
    }

    for field_name in COMMON_FACT_FIELDS + _scenario_metric_fields(scenario):
        data[field_name] = _serialize_value(getattr(row, field_name))

    if scenario in {"base", "all"}:
        data["base_inbound_progress_rate"] = _inbound_progress_rate(
            getattr(row, "inbound_qty", None),
            getattr(row, "base_total_reserve_qty", None),
        )
    if scenario in {"stretch", "all"}:
        data["stretch_inbound_progress_rate"] = _inbound_progress_rate(
            getattr(row, "inbound_qty", None),
            getattr(row, "stretch_total_reserve_qty", None),
        )

    if row.dimension_level in {"province", "bd"} and not data.get("area_name"):
        province_name = data.get("province_name") or (
            data.get("dimension_name") if row.dimension_level == "province" else None
        )
        data["area_name"] = resolve_area_for_province(province_name)

    return data


def _dimension_identity(row: MonthlySnapshotMetric) -> str:
    return row.dimension_key or row.dimension_name


def _build_placeholder_metric(dimension_level: str, dimension_name: str) -> SimpleNamespace:
    area_name = ""
    province_name = ""
    if dimension_level == "area":
        area_name = dimension_name
    elif dimension_level == "province":
        area_name = resolve_area_for_province(dimension_name)
        province_name = dimension_name

    payload: dict[str, Any] = {
        "dimension_level": dimension_level,
        "dimension_key": dimension_name,
        "dimension_name": dimension_name,
        "target_revenue": Decimal("0"),
        "inbound_qty": Decimal("0"),
        "achieved_revenue": Decimal("0"),
        "course_line": None,
        "class_key": None,
        "class_name": None,
        "area_name": area_name,
        "province_name": province_name,
        "city_name": None,
        "bd_name": None,
        "acquisition_type": None,
        "project_reliability": None,
    }
    for field_name in SCENARIO_FIELDS["base"] + SCENARIO_FIELDS["stretch"]:
        payload[field_name] = Decimal("0")
    return SimpleNamespace(**payload)


def _materialize_single_rows(
    rows: list[MonthlySnapshotMetric],
    *,
    dimension_level: str,
) -> list[MonthlySnapshotMetric | SimpleNamespace]:
    fixed_dimension_names = FIXED_DIMENSION_ORDER.get(dimension_level)
    if not fixed_dimension_names:
        return rows

    row_map = {_dimension_identity(row): row for row in rows}
    return [
        row_map.get(dimension_name) or _build_placeholder_metric(dimension_level, dimension_name)
        for dimension_name in fixed_dimension_names
    ]


def get_single_dashboard(
    db: Session,
    *,
    period_code: str,
    upload_seq: int,
    dimension_level: str,
    scenario: str,
) -> DashboardSingleResponse:
    normalized_level = _normalize_dimension_level(dimension_level)
    normalized_scenario = _normalize_scenario(scenario)
    period, _ = _resolve_period_batch(db, period_code, upload_seq)

    rows = db.scalars(
        select(MonthlySnapshotMetric)
        .where(
            MonthlySnapshotMetric.period_id == period.period_id,
            MonthlySnapshotMetric.upload_seq == upload_seq,
            MonthlySnapshotMetric.dimension_level == normalized_level,
        )
        .order_by(MonthlySnapshotMetric.dimension_name.asc(), MonthlySnapshotMetric.metric_id.asc())
    ).all()

    materialized_rows = _materialize_single_rows(rows, dimension_level=normalized_level)
    serialized_rows = [_serialize_fact_row(row, normalized_scenario) for row in materialized_rows]
    return DashboardSingleResponse(
        period_code=period_code,
        upload_seq=upload_seq,
        dimension_level=normalized_level,
        scenario=normalized_scenario,
        total=len(serialized_rows),
        rows=serialized_rows,
    )


def _compare_metrics(
    current_row: MonthlySnapshotMetric | None,
    previous_row: MonthlySnapshotMetric | None,
    scenario: str,
) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for field_name in COMPARE_BASE_FIELDS + _scenario_metric_fields(scenario):
        current_value = getattr(current_row, field_name, None) if current_row is not None else None
        previous_value = getattr(previous_row, field_name, None) if previous_row is not None else None
        result[f"current_{field_name}"] = _serialize_value(current_value)
        result[f"previous_{field_name}"] = _serialize_value(previous_value)

        if current_value is None and previous_value is None:
            result[f"diff_{field_name}"] = None
        else:
            current_decimal = current_value or Decimal("0")
            previous_decimal = previous_value or Decimal("0")
            result[f"diff_{field_name}"] = _serialize_value(current_decimal - previous_decimal)

    return result


def get_compare_dashboard(
    db: Session,
    *,
    period_code: str,
    upload_seq: int,
    dimension_level: str,
    scenario: str,
) -> DashboardCompareResponse:
    normalized_level = _normalize_dimension_level(dimension_level)
    normalized_scenario = _normalize_scenario(scenario)
    period, current_batch = _resolve_period_batch(db, period_code, upload_seq)

    if get_batch_record_mmdd_value(current_batch) is None:
        return DashboardCompareResponse(
            show_compare=False,
            message="当前批次缺少班期日期，暂无可对比的上期数据。",
        )

    period_batches = db.scalars(select(UploadBatch).where(UploadBatch.period_id == period.period_id)).all()
    previous_batch = build_previous_batch_map(period_batches).get(current_batch.upload_seq)
    if previous_batch is None:
        return DashboardCompareResponse(
            show_compare=False,
            message="当前批次为当月首期，暂无上期对比数据。",
        )

    current_rows = db.scalars(
        select(MonthlySnapshotMetric)
        .where(
            MonthlySnapshotMetric.period_id == period.period_id,
            MonthlySnapshotMetric.upload_seq == upload_seq,
            MonthlySnapshotMetric.dimension_level == normalized_level,
        )
    ).all()
    previous_rows = db.scalars(
        select(MonthlySnapshotMetric)
        .where(
            MonthlySnapshotMetric.period_id == period.period_id,
            MonthlySnapshotMetric.upload_seq == previous_batch.upload_seq,
            MonthlySnapshotMetric.dimension_level == normalized_level,
        )
    ).all()

    if not previous_rows and normalized_level not in FIXED_DIMENSION_ORDER:
        return DashboardCompareResponse(
            show_compare=False,
            message="未找到对应上期批次的数据，暂时无法对比。",
        )

    current_map = {_dimension_identity(row): row for row in current_rows}
    previous_map = {_dimension_identity(row): row for row in previous_rows}
    fixed_dimension_names = FIXED_DIMENSION_ORDER.get(normalized_level)
    all_keys = list(fixed_dimension_names) if fixed_dimension_names else sorted(set(current_map) | set(previous_map))

    rows: list[dict[str, Any]] = []
    for key in all_keys:
        current_row = current_map.get(key)
        previous_row = previous_map.get(key)
        if fixed_dimension_names:
            current_row = current_row or _build_placeholder_metric(normalized_level, key)
            previous_row = previous_row or _build_placeholder_metric(normalized_level, key)
        anchor_row = current_row or previous_row
        if anchor_row is None:
            continue

        row_data = {
            "dimension_key": key,
            "dimension_name": anchor_row.dimension_name,
        }
        for field_name in [
            "course_line",
            "class_key",
            "class_name",
            "area_name",
            "province_name",
            "city_name",
            "bd_name",
            "acquisition_type",
            "project_reliability",
        ]:
            row_data[field_name] = _serialize_value(getattr(anchor_row, field_name))
        row_data.update(_compare_metrics(current_row, previous_row, normalized_scenario))
        rows.append(row_data)

    return DashboardCompareResponse(
        show_compare=True,
        period_code=period_code,
        current_upload_seq=upload_seq,
        previous_upload_seq=previous_batch.upload_seq,
        dimension_level=normalized_level,
        scenario=normalized_scenario,
        total=len(rows),
        rows=rows,
    )
