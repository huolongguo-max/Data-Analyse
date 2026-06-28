from __future__ import annotations

from decimal import Decimal
from types import SimpleNamespace

import pytest

from app.services.dashboard_service import (
    _build_placeholder_metric,
    _compare_metrics,
    _inbound_progress_rate,
    _materialize_single_rows,
    _normalize_dimension_level,
    _normalize_scenario,
    _serialize_fact_row,
    _scenario_metric_fields,
)


def test_normalize_dimension_level_accepts_documented_values() -> None:
    assert _normalize_dimension_level("area") == "area"
    assert _normalize_dimension_level("province") == "province"
    assert _normalize_dimension_level("bd") == "bd"


def test_normalize_dimension_level_rejects_unknown_value() -> None:
    with pytest.raises(Exception):
        _normalize_dimension_level("unknown")


def test_scenario_metric_fields_expand_all_scenario() -> None:
    fields = _scenario_metric_fields("all")
    assert "base_total_revenue" in fields
    assert "stretch_total_revenue" in fields


def test_compare_metrics_returns_current_previous_and_diff() -> None:
    current_row = SimpleNamespace(
        base_reserve_qty=Decimal("10.00"),
        base_forecast_revenue=Decimal("20.00"),
        base_total_reserve_qty=Decimal("30.00"),
        base_total_revenue=Decimal("40.00"),
        base_achievement_rate=Decimal("0.400000"),
    )
    previous_row = SimpleNamespace(
        base_reserve_qty=Decimal("1.00"),
        base_forecast_revenue=Decimal("2.00"),
        base_total_reserve_qty=Decimal("3.00"),
        base_total_revenue=Decimal("4.00"),
        base_achievement_rate=Decimal("0.040000"),
    )

    result = _compare_metrics(current_row, previous_row, "base")

    assert result["current_base_total_revenue"] == 40.0
    assert result["previous_base_total_revenue"] == 4.0
    assert result["diff_base_total_revenue"] == 36.0


def test_inbound_progress_rate_handles_zero_denominator() -> None:
    assert _inbound_progress_rate(Decimal("5"), Decimal("0")) == 0.0


def test_serialize_fact_row_includes_inbound_progress_rate() -> None:
    row = SimpleNamespace(
        dimension_level="area",
        dimension_key="A",
        dimension_name="A",
        target_revenue=Decimal("100"),
        inbound_qty=Decimal("20"),
        achieved_revenue=Decimal("30"),
        course_line=None,
        class_key=None,
        class_name=None,
        area_name="A",
        province_name=None,
        city_name=None,
        bd_name=None,
        acquisition_type=None,
        project_reliability=None,
        base_reserve_qty=Decimal("40"),
        base_forecast_revenue=Decimal("50"),
        base_total_reserve_qty=Decimal("60"),
        base_total_revenue=Decimal("70"),
        base_achievement_rate=Decimal("0.7"),
        stretch_reserve_qty=Decimal("80"),
        stretch_forecast_revenue=Decimal("90"),
        stretch_total_reserve_qty=Decimal("100"),
        stretch_total_revenue=Decimal("110"),
        stretch_achievement_rate=Decimal("1.1"),
    )

    serialized = _serialize_fact_row(row, "all")

    assert serialized["base_inbound_progress_rate"] == 20 / 60
    assert serialized["stretch_inbound_progress_rate"] == 0.2


def test_serialize_fact_row_backfills_fixed_area_for_province() -> None:
    row = SimpleNamespace(
        dimension_level="province",
        dimension_key="北京",
        dimension_name="北京",
        target_revenue=Decimal("100"),
        inbound_qty=Decimal("20"),
        achieved_revenue=Decimal("30"),
        course_line=None,
        class_key=None,
        class_name=None,
        area_name="",
        province_name="北京",
        city_name=None,
        bd_name=None,
        acquisition_type=None,
        project_reliability=None,
        base_reserve_qty=Decimal("40"),
        base_forecast_revenue=Decimal("50"),
        base_total_reserve_qty=Decimal("60"),
        base_total_revenue=Decimal("70"),
        base_achievement_rate=Decimal("0.7"),
        stretch_reserve_qty=Decimal("80"),
        stretch_forecast_revenue=Decimal("90"),
        stretch_total_reserve_qty=Decimal("100"),
        stretch_total_revenue=Decimal("110"),
        stretch_achievement_rate=Decimal("1.1"),
    )

    serialized = _serialize_fact_row(row, "all")

    assert serialized["area_name"] == "冀豫片区"


def test_serialize_fact_row_backfills_fixed_area_for_bd() -> None:
    row = SimpleNamespace(
        dimension_level="bd",
        dimension_key="BD-A",
        dimension_name="BD-A",
        target_revenue=Decimal("100"),
        inbound_qty=Decimal("20"),
        achieved_revenue=Decimal("30"),
        course_line=None,
        class_key=None,
        class_name=None,
        area_name="",
        province_name="北京",
        city_name=None,
        bd_name="BD-A",
        acquisition_type=None,
        project_reliability=None,
        base_reserve_qty=Decimal("40"),
        base_forecast_revenue=Decimal("50"),
        base_total_reserve_qty=Decimal("60"),
        base_total_revenue=Decimal("70"),
        base_achievement_rate=Decimal("0.7"),
        stretch_reserve_qty=Decimal("80"),
        stretch_forecast_revenue=Decimal("90"),
        stretch_total_reserve_qty=Decimal("100"),
        stretch_total_revenue=Decimal("110"),
        stretch_achievement_rate=Decimal("1.1"),
    )

    serialized = _serialize_fact_row(row, "all")

    assert serialized["area_name"] == "冀豫片区"


def test_placeholder_metric_uses_fixed_province_area_mapping() -> None:
    placeholder = _build_placeholder_metric("province", "北京市")

    assert placeholder.dimension_key == "北京市"
    assert placeholder.area_name == "冀豫片区"
    assert placeholder.base_total_revenue == Decimal("0")


def test_placeholder_metric_supports_short_province_name() -> None:
    placeholder = _build_placeholder_metric("province", "北京")

    assert placeholder.dimension_key == "北京"
    assert placeholder.area_name == "冀豫片区"


def test_materialize_single_rows_backfills_fixed_area_order() -> None:
    existing_row = SimpleNamespace(
        dimension_key="津鲁片区",
        dimension_name="津鲁片区",
        dimension_level="area",
        target_revenue=Decimal("1"),
        inbound_qty=Decimal("2"),
        achieved_revenue=Decimal("3"),
        course_line=None,
        class_key=None,
        class_name=None,
        area_name="津鲁片区",
        province_name=None,
        city_name=None,
        bd_name=None,
        acquisition_type=None,
        project_reliability=None,
        base_reserve_qty=Decimal("4"),
        base_forecast_revenue=Decimal("5"),
        base_total_reserve_qty=Decimal("6"),
        base_total_revenue=Decimal("7"),
        base_achievement_rate=Decimal("0.1"),
        stretch_reserve_qty=Decimal("8"),
        stretch_forecast_revenue=Decimal("9"),
        stretch_total_reserve_qty=Decimal("10"),
        stretch_total_revenue=Decimal("11"),
        stretch_achievement_rate=Decimal("0.2"),
    )

    rows = _materialize_single_rows([existing_row], dimension_level="area")

    assert rows[0].dimension_name == "黑吉辽片区"
    assert rows[2].dimension_name == "津鲁片区"
    assert rows[2].target_revenue == Decimal("1")
    assert rows[-1].dimension_name == "重庆片区"


def test_normalize_scenario_rejects_unknown_value() -> None:
    with pytest.raises(Exception):
        _normalize_scenario("invalid")
