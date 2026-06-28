from __future__ import annotations

from decimal import Decimal
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.common.exceptions import NotFoundError, ValidationError
from app.models import InboundCompleted, MonthlyClassCompleted, MonthlyTargetCompleted, Period, ReserveDetailCompleted, UploadBatch
from app.models.uploaded_file import UploadedFile
from app.schemas.export import CompletedTableResponse
from app.services.filename_parser import build_workbook_filename
from app.services.reserve_processor_adapter import process_xlsx_to_xlsx


TABLE_MODEL_MAP = {
    "reserve_detail": ReserveDetailCompleted,
    "monthly_class": MonthlyClassCompleted,
    "monthly_target": MonthlyTargetCompleted,
    "inbound": InboundCompleted,
}

MONTHLY_CLASS_STATUS_STYLE_MAP = {
    "未启动": "not-started",
    "招生中": "in-progress",
    "已结束": "ended",
}

MONTHLY_CLASS_META_FIELDS = {
    "base": {
        "totalReserve": ("保底总储备量",),
        "reserve": ("保底储备量",),
        "inbound": ("已进线量", "已进线"),
        "totalRevenue": ("保底总预测业绩",),
        "forecast": ("保底预测业绩",),
        "achieved": ("已达成预测业绩",),
    },
    "stretch": {
        "totalReserve": ("冲高总储备量",),
        "reserve": ("冲高储备量",),
        "inbound": ("已进线量", "已进线"),
        "totalRevenue": ("冲高总预测业绩",),
        "forecast": ("冲高预测业绩",),
        "achieved": ("已达成预测业绩",),
    },
}


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


def _get_uploaded_file(db: Session, *, period_id: int, batch_id: int, file_role: str) -> UploadedFile:
    file_record = db.scalar(
        select(UploadedFile).where(
            UploadedFile.period_id == period_id,
            UploadedFile.batch_id == batch_id,
            UploadedFile.file_role == file_role,
        )
    )
    if file_record is None:
        raise NotFoundError(f"Missing uploaded file record: {file_role}")
    return file_record


def get_completed_workbook_path(db: Session, period_code: str, upload_seq: int) -> Path:
    period, batch = _resolve_period_batch(db, period_code, upload_seq)
    original_record = _get_uploaded_file(
        db,
        period_id=period.period_id,
        batch_id=batch.batch_id,
        file_role="original_workbook",
    )
    completed_record = _get_uploaded_file(
        db,
        period_id=period.period_id,
        batch_id=batch.batch_id,
        file_role="completed_workbook",
    )

    raw_completed_path = Path(completed_record.file_path)
    download_path = raw_completed_path.parent.parent / "download" / raw_completed_path.name
    processed = process_xlsx_to_xlsx(
        Path(original_record.file_path),
        download_path,
        round_for_export=True,
    )
    if processed.output_path is None:
        raise ValidationError("Completed workbook was not generated.")
    return processed.output_path


def get_completed_workbook_filename(db: Session, period_code: str, upload_seq: int) -> str:
    period, batch = _resolve_period_batch(db, period_code, upload_seq)
    if batch.source_period_year and batch.source_period_month and batch.source_record_mmdd:
        return build_workbook_filename(
            record_mmdd=batch.source_record_mmdd,
            period_year=batch.source_period_year,
            source_period_month=batch.source_period_month,
        )
    return _get_uploaded_file(
        db,
        period_id=period.period_id,
        batch_id=batch.batch_id,
        file_role="completed_workbook",
    ).stored_filename


def _serialize_numeric(value: object) -> float:
    if isinstance(value, Decimal):
        return float(value)
    if value is None:
        return 0.0
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _pick_first(row: dict, keys: tuple[str, ...]) -> object:
    for key in keys:
        if key in row:
            return row.get(key)
    return None


def _build_monthly_class_meta(raw_rows: list[dict]) -> dict:
    totals: dict[str, dict[str, float]] = {}
    for scenario, field_map in MONTHLY_CLASS_META_FIELDS.items():
        totals[scenario] = {
            metric_name: sum(_serialize_numeric(_pick_first(row, aliases)) for row in raw_rows)
            for metric_name, aliases in field_map.items()
        }

    return {
        "overall_totals": totals,
        "status_styles": MONTHLY_CLASS_STATUS_STYLE_MAP,
    }


def get_completed_table_rows(db: Session, period_code: str, upload_seq: int, table_type: str) -> CompletedTableResponse:
    model = TABLE_MODEL_MAP.get(table_type)
    if model is None:
        raise ValidationError(f"Unsupported table_type: {table_type}")

    period, _ = _resolve_period_batch(db, period_code, upload_seq)

    rows = db.scalars(
        select(model).where(
            model.period_id == period.period_id,
            model.upload_seq == upload_seq,
        ).order_by(model.id.asc())
    ).all()

    raw_rows = [row.raw_data or {} for row in rows]
    columns = list(raw_rows[0].keys()) if raw_rows else []
    meta = _build_monthly_class_meta(raw_rows) if table_type == "monthly_class" else {}

    return CompletedTableResponse(
        table_type=table_type,
        columns=columns,
        total=len(raw_rows),
        rows=raw_rows,
        meta=meta,
    )
