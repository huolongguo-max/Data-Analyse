from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace

from app.services.export_service import (
    _build_monthly_class_meta,
    get_completed_workbook_filename,
    get_completed_workbook_path,
)


def test_get_completed_workbook_filename_uses_batch_metadata(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.services.export_service._resolve_period_batch",
        lambda db, period_code, upload_seq: (
            SimpleNamespace(period_id=1),
            SimpleNamespace(
                batch_id=10,
                source_period_year=2026,
                source_period_month=6,
                source_record_mmdd="0612",
            ),
        ),
    )
    monkeypatch.setattr(
        "app.services.export_service._get_uploaded_file",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("should not read stored filename")),
    )

    filename = get_completed_workbook_filename(db=None, period_code="2026-06", upload_seq=1)

    assert filename == "【0612】2026年6月全国储备摸底.xlsx"


def test_get_completed_workbook_filename_falls_back_to_stored_filename(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.services.export_service._resolve_period_batch",
        lambda db, period_code, upload_seq: (
            SimpleNamespace(period_id=1),
            SimpleNamespace(
                batch_id=10,
                source_period_year=None,
                source_period_month=None,
                source_record_mmdd=None,
            ),
        ),
    )
    monkeypatch.setattr(
        "app.services.export_service._get_uploaded_file",
        lambda *args, **kwargs: SimpleNamespace(stored_filename="legacy-name.xlsx"),
    )

    filename = get_completed_workbook_filename(db=None, period_code="2026-06", upload_seq=1)

    assert filename == "legacy-name.xlsx"


def test_build_monthly_class_meta_returns_overall_totals_and_status_styles() -> None:
    meta = _build_monthly_class_meta(
        [
            {
                "保底总储备量": 100,
                "保底储备量": 40,
                "已进线量": 15,
                "保底总预测业绩": 80,
                "保底预测业绩": 30,
                "已达成预测业绩": 12,
                "冲高总储备量": 120,
                "冲高储备量": 50,
                "冲高总预测业绩": 90,
                "冲高预测业绩": 35,
                "招生进度": "招生中",
            },
            {
                "保底总储备量": 60,
                "保底储备量": 20,
                "已进线量": 5,
                "保底总预测业绩": 40,
                "保底预测业绩": 10,
                "已达成预测业绩": 8,
                "冲高总储备量": 70,
                "冲高储备量": 25,
                "冲高总预测业绩": 45,
                "冲高预测业绩": 15,
                "招生进度": "未启动",
            },
        ]
    )

    assert meta["overall_totals"]["base"]["totalReserve"] == 160.0
    assert meta["overall_totals"]["base"]["reserve"] == 60.0
    assert meta["overall_totals"]["base"]["inbound"] == 20.0
    assert meta["overall_totals"]["stretch"]["totalRevenue"] == 135.0
    assert meta["status_styles"]["招生中"] == "in-progress"


def test_get_completed_workbook_path_rebuilds_from_original_workbook(monkeypatch) -> None:
    with TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        original_path = tmp_path / "original.xlsx"
        completed_path = tmp_path / "completed" / "legacy.xlsx"
        completed_path.parent.mkdir(parents=True, exist_ok=True)
        original_path.write_bytes(b"original")
        completed_path.write_bytes(b"legacy")

        monkeypatch.setattr(
            "app.services.export_service._resolve_period_batch",
            lambda db, period_code, upload_seq: (
                SimpleNamespace(period_id=1),
                SimpleNamespace(batch_id=10),
            ),
        )

        def fake_get_uploaded_file(*args, **kwargs):
            if kwargs["file_role"] == "original_workbook":
                return SimpleNamespace(file_path=str(original_path))
            if kwargs["file_role"] == "completed_workbook":
                return SimpleNamespace(file_path=str(completed_path))
            raise AssertionError("unexpected file role")

        calls: list[tuple[Path, Path, bool]] = []

        def fake_process_xlsx_to_xlsx(input_path, output_path=None, *, round_for_export=False):
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_bytes(b"rebuilt")
            calls.append((Path(input_path), output_path, round_for_export))
            return SimpleNamespace(output_path=output_path)

        monkeypatch.setattr("app.services.export_service._get_uploaded_file", fake_get_uploaded_file)
        monkeypatch.setattr("app.services.export_service.process_xlsx_to_xlsx", fake_process_xlsx_to_xlsx)

        result = get_completed_workbook_path(db=None, period_code="2026-06", upload_seq=1)

        assert result == completed_path.parent.parent / "download" / completed_path.name
        assert result.read_bytes() == b"rebuilt"
        assert calls == [(original_path, result, True)]
