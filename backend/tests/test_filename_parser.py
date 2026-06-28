import pytest

from app.services.filename_parser import (
    build_workbook_filename,
    parse_sheet_name,
    parse_workbook_filename,
    validate_required_sheet_names,
)


def test_parse_workbook_filename() -> None:
    parsed = parse_workbook_filename("【0612】2026年6月全国储备摸底.xlsx")

    assert parsed.period_year == 2026
    assert parsed.period_code == "2026-06"
    assert parsed.source_period_month == 6
    assert parsed.source_period_label == "6月班期"
    assert parsed.upload_seq == 1
    assert parsed.source_record_mmdd == "0612"


def test_parse_workbook_filename_with_upload_seq() -> None:
    parsed = parse_workbook_filename("【0615】2026年6月全国储备摸底.xlsx", upload_seq=2)
    assert parsed.upload_seq == 2
    assert parsed.source_record_mmdd == "0615"


def test_build_workbook_filename() -> None:
    assert build_workbook_filename("0612", 2026, 6) == "【0612】2026年6月全国储备摸底.xlsx"


def test_parse_workbook_filename_rejects_old_format() -> None:
    with pytest.raises(ValueError):
        parse_workbook_filename("2026-3月班期-第1次-0303.xlsx")


@pytest.mark.parametrize(
    ("sheet_name", "table_type"),
    [
        ("储备明细表", "reserve_detail"),
        ("每月班期表", "monthly_class"),
        ("已进线表", "inbound"),
        ("每月目标表", "monthly_target"),
    ],
)
def test_parse_sheet_name(sheet_name: str, table_type: str) -> None:
    assert parse_sheet_name(sheet_name) == table_type


def test_parse_sheet_name_rejects_unexpected_name() -> None:
    with pytest.raises(ValueError):
        parse_sheet_name("进线表")


def test_validate_required_sheet_names_accepts_expected_sheets() -> None:
    actual_names = validate_required_sheet_names(["储备明细表", "每月班期表", "已进线表", "每月目标表"])
    assert actual_names == ("储备明细表", "每月班期表", "已进线表", "每月目标表")


def test_validate_required_sheet_names_rejects_missing_or_unexpected_sheet() -> None:
    with pytest.raises(ValueError):
        validate_required_sheet_names(["储备明细表", "每月班期表", "每月目标表", "临时sheet"])
