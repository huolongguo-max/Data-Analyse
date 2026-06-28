from __future__ import annotations

from datetime import datetime
from types import SimpleNamespace

from app.services.upload_sequence_service import (
    build_previous_batch_map,
    get_batch_record_mmdd_value,
    order_batches_for_display,
)


def _batch(upload_seq: int, record_mmdd: str, uploaded_at: str) -> SimpleNamespace:
    return SimpleNamespace(
        upload_seq=upload_seq,
        source_record_mmdd=record_mmdd,
        uploaded_at=datetime.fromisoformat(uploaded_at),
    )


def test_get_batch_record_mmdd_value_rejects_invalid_value() -> None:
    assert get_batch_record_mmdd_value(_batch(1, "0312", "2026-03-12T08:00:00")) == 312
    assert get_batch_record_mmdd_value(_batch(2, "3/12", "2026-03-12T08:00:00")) is None
    assert get_batch_record_mmdd_value(_batch(3, "1399", "2026-03-12T08:00:00")) is None


def test_build_previous_batch_map_uses_record_date_not_upload_sequence() -> None:
    batches = [
        _batch(1, "0305", "2026-03-16T09:00:00"),
        _batch(2, "0315", "2026-03-17T09:00:00"),
        _batch(3, "0312", "2026-03-18T09:00:00"),
    ]

    previous_map = build_previous_batch_map(batches)

    assert previous_map[1] is None
    assert previous_map[3].upload_seq == 1
    assert previous_map[2].upload_seq == 3


def test_order_batches_for_display_shows_latest_record_date_first() -> None:
    batches = [
        _batch(1, "0305", "2026-03-16T09:00:00"),
        _batch(2, "0315", "2026-03-17T09:00:00"),
        _batch(3, "0312", "2026-03-18T09:00:00"),
    ]

    ordered = order_batches_for_display(batches)

    assert [batch.upload_seq for batch in ordered] == [2, 3, 1]
