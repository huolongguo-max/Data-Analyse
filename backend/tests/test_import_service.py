from datetime import date

from app.services.import_service import _build_period, _dimension_fields, _dimension_level


class _Meta:
    def __init__(self, year: int | None, month: int | None) -> None:
        self.year = year
        self.month = month


def test_build_period_uses_filename_year_and_month() -> None:
    period_code, period_month = _build_period(_Meta(2026, 3))
    assert period_code == "2026-03"
    assert period_month == date(2026, 3, 1)


def test_dimension_level_mapping_matches_dashboard_query_contract() -> None:
    assert _dimension_level("全国") == "national"
    assert _dimension_level("片区") == "area"
    assert _dimension_level("省份") == "province"
    assert _dimension_level("BD") == "bd"


def test_dimension_fields_only_fill_matching_dimension() -> None:
    assert _dimension_fields("片区", "粤海片区") == {
        "area_name": "粤海片区",
        "province_name": None,
        "city_name": None,
        "bd_name": None,
    }
    assert _dimension_fields("BD", "庄小龙") == {
        "area_name": None,
        "province_name": None,
        "city_name": None,
        "bd_name": "庄小龙",
    }
