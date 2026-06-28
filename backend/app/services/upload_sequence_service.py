from __future__ import annotations

import re
from datetime import datetime
from typing import Iterable

from app.models import UploadBatch


MMDD_RE = re.compile(r"^\d{4}$")


def get_batch_record_mmdd_value(batch: UploadBatch) -> int | None:
    raw = str(batch.source_record_mmdd or "").strip()
    if MMDD_RE.fullmatch(raw) is None:
        return None

    month = int(raw[:2])
    day = int(raw[2:])
    if month < 1 or month > 12 or day < 1 or day > 31:
        return None

    return int(raw)


def _uploaded_at_or_min(batch: UploadBatch) -> datetime:
    return batch.uploaded_at or datetime.min


def order_batches_for_compare(batches: Iterable[UploadBatch]) -> list[UploadBatch]:
    dated_batches: list[UploadBatch] = []
    undated_batches: list[UploadBatch] = []

    for batch in batches:
        if get_batch_record_mmdd_value(batch) is None:
            undated_batches.append(batch)
        else:
            dated_batches.append(batch)

    dated_batches.sort(
        key=lambda batch: (
            get_batch_record_mmdd_value(batch) or 0,
            _uploaded_at_or_min(batch),
            batch.upload_seq,
        )
    )
    undated_batches.sort(key=lambda batch: (_uploaded_at_or_min(batch), batch.upload_seq))
    return dated_batches + undated_batches


def order_batches_for_display(batches: Iterable[UploadBatch]) -> list[UploadBatch]:
    ordered = order_batches_for_compare(batches)
    dated_batches = [batch for batch in ordered if get_batch_record_mmdd_value(batch) is not None]
    undated_batches = [batch for batch in ordered if get_batch_record_mmdd_value(batch) is None]
    return list(reversed(dated_batches)) + list(reversed(undated_batches))


def build_previous_batch_map(batches: Iterable[UploadBatch]) -> dict[int, UploadBatch | None]:
    previous_map: dict[int, UploadBatch | None] = {}
    previous_dated_batch: UploadBatch | None = None

    for batch in order_batches_for_compare(batches):
        if get_batch_record_mmdd_value(batch) is None:
            previous_map[batch.upload_seq] = None
            continue

        previous_map[batch.upload_seq] = previous_dated_batch
        previous_dated_batch = batch

    return previous_map
