from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import Any

import pandas as pd
from fastapi import UploadFile
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.common.exceptions import ValidationError
from app.models import (
    InboundCompleted,
    InboundRow,
    MonthlyClassCompleted,
    MonthlyClassRow,
    MonthlySnapshotMetric,
    MonthlyTargetCompleted,
    MonthlyTargetRow,
    Period,
    PeriodClassSchedule,
    ReserveDetailCompleted,
    ReserveDetailRow,
    UploadBatch,
    UploadTableInstance,
)
from app.models.uploaded_file import UploadedFile
from app.schemas.import_task import ImportedTableSummary, PeriodSummary, UploadBatchSummary, WorkbookImportResponse
from app.services.filename_parser import build_workbook_filename
from app.services.reserve_processor_adapter import build_completed_output_path, parse_filename, process_xlsx_to_xlsx, read_xlsx
from app.services.upload_sequence_service import build_previous_batch_map, order_batches_for_display
from app.utils.file_utils import (
    build_completed_workbook_dir,
    build_original_workbook_path,
    describe_local_file,
    store_upload_file,
)


DETAIL_SHEET_NAME = "\u50a8\u5907\u660e\u7ec6\u8868"
SCHEDULE_SHEET_NAME = "\u6bcf\u6708\u73ed\u671f\u8868"
TARGET_SHEET_NAME = "\u5df2\u8fdb\u7ebf\u8868"

DETAIL_COL_AREA = "\u7247\u533a"
DETAIL_COL_BD = "BD"
DETAIL_COL_PROVINCE = "\u7701\u4efd"
DETAIL_COL_CITY = "\u57ce\u5e02"
DETAIL_COL_DISTRICT = "\u533a\u53bf"
DETAIL_COL_ACQUISITION = "\u83b7\u5ba2\u7c7b\u578b"
DETAIL_COL_RELIABILITY = "\u9879\u76ee\u53ef\u9760\u7a0b\u5ea6"
DETAIL_COL_PROJECT = "\u8bfe\u7ebf\u9879\u76ee"
DETAIL_COL_START = "\u542f\u52a8\u65e5\u671f"
DETAIL_COL_END = "\u505c\u6b62\u65e5\u671f"
DETAIL_COL_NEXT_WEEK_START = "\u4e0b\u5468\u542f\u52a8\u65e5\u671f"
DETAIL_COL_NEXT_WEEK_END = "\u4e0b\u5468\u505c\u6b62\u65e5\u671f"
DETAIL_COL_BASE_RESERVE = "\u4fdd\u5e95\u50a8\u5907\u91cf"
DETAIL_COL_BASE_FORECAST = "\u4fdd\u5e95\u9884\u6d4b\u4e1a\u7ee9"
DETAIL_COL_STRETCH_RESERVE = "\u51b2\u9ad8\u50a8\u5907\u91cf"
DETAIL_COL_STRETCH_FORECAST = "\u51b2\u9ad8\u9884\u6d4b\u4e1a\u7ee9"
DETAIL_COL_NEXT_WEEK_BASE_RESERVE = "\u4e0b\u5468\u4fdd\u5e95\u50a8\u5907\u91cf"
DETAIL_COL_NEXT_WEEK_STRETCH_RESERVE = "\u4e0b\u5468\u50a8\u5907\u91cf"

SCHEDULE_COL_PROJECT = "\u8bfe\u7ebf\u9879\u76ee"
SCHEDULE_COL_CLASS = "\u73ed\u671f"
SCHEDULE_COL_INBOUND_START = "\u8fdb\u7ebf\u5f00\u59cb\u65f6\u95f4"
SCHEDULE_COL_INBOUND_END = "\u8fdb\u7ebf\u622a\u6b62\u65f6\u95f4"
SCHEDULE_COL_ENROLLMENT = "\u62db\u751f\u8fdb\u5ea6"
SCHEDULE_COL_BASE_TOTAL_RESERVE = "\u4fdd\u5e95\u603b\u50a8\u5907\u91cf"
SCHEDULE_COL_BASE_TOTAL_FORECAST = "\u4fdd\u5e95\u603b\u9884\u6d4b\u4e1a\u7ee9"
SCHEDULE_COL_STRETCH_TOTAL_RESERVE = "\u51b2\u9ad8\u603b\u50a8\u5907\u91cf"
SCHEDULE_COL_STRETCH_TOTAL_FORECAST = "\u51b2\u9ad8\u603b\u9884\u6d4b\u4e1a\u7ee9"

TARGET_COL_LEVEL = "\u76ee\u6807\u5c42\u9762"
TARGET_COL_OBJECT = "\u76ee\u6807\u5bf9\u8c61"
TARGET_COL_REVENUE = "\u9884\u6d4b\u4e1a\u7ee9\u76ee\u6807"
TARGET_COL_ENTERED = "\u5df2\u8fdb\u7ebf"
TARGET_COL_ACHIEVED = "\u5df2\u8fbe\u6210\u9884\u6d4b\u4e1a\u7ee9"
TARGET_COL_BASE_ACHIEVEMENT = "\u4fdd\u5e95\u603b\u9884\u6d4b\u4e1a\u7ee9\u8fbe\u6807\u7387"
TARGET_COL_STRETCH_ACHIEVEMENT = "\u51b2\u9ad8\u603b\u9884\u6d4b\u4e1a\u7ee9\u8fbe\u6807\u7387"

LEVEL_NATIONAL = "\u5168\u56fd"
LEVEL_AREA = "\u7247\u533a"
LEVEL_PROVINCE = "\u7701\u4efd"
LEVEL_CITY = "\u57ce\u5e02"

TABLE_CONFIGS = (
    ("reserve_detail", DETAIL_SHEET_NAME),
    ("monthly_class", SCHEDULE_SHEET_NAME),
    ("monthly_target", TARGET_SHEET_NAME),
)

# Keep raw metric values at 6-decimal precision in storage.
DECIMAL_2 = Decimal("0.000001")
DECIMAL_6 = Decimal("0.000001")


def _quantize_decimal(value: Any, quant: Decimal) -> Decimal | None:
    if value is None:
        return None

    if isinstance(value, str) and value.strip() == "":
        return None

    try:
        if pd.isna(value):
            return None
    except TypeError:
        pass

    return Decimal(str(value)).quantize(quant, rounding=ROUND_HALF_UP)


def _to_date(value: Any) -> date | None:
    if value is None:
        return None

    if isinstance(value, date) and not isinstance(value, datetime):
        return value

    if isinstance(value, pd.Timestamp):
        return value.date()

    try:
        if pd.isna(value):
            return None
    except TypeError:
        pass

    parsed = pd.to_datetime(value, errors="coerce")
    if pd.isna(parsed):
        return None

    return pd.Timestamp(parsed).date()


def _text(value: Any) -> str | None:
    if value is None:
        return None

    if isinstance(value, str):
        stripped = value.strip()
        return stripped or None

    try:
        if pd.isna(value):
            return None
    except TypeError:
        pass

    return str(value).strip() or None


def _jsonable_value(value: Any) -> Any:
    if value is None:
        return None

    if isinstance(value, pd.Timestamp):
        return value.isoformat()

    if isinstance(value, datetime):
        return value.isoformat()

    if isinstance(value, date):
        return value.isoformat()

    if isinstance(value, Decimal):
        return float(value)

    if hasattr(value, "item"):
        try:
            return _jsonable_value(value.item())
        except Exception:
            pass

    try:
        if pd.isna(value):
            return None
    except TypeError:
        pass

    return value


def _row_to_json(row: pd.Series) -> dict[str, Any]:
    return {str(column): _jsonable_value(value) for column, value in row.items()}


def _build_period(meta) -> tuple[str, date]:
    if meta.year is None or meta.month is None:
        raise ValidationError("Filename does not contain a valid period.")

    return f"{meta.year:04d}-{meta.month:02d}", date(meta.year, meta.month, 1)


def _get_or_create_period(db: Session, period_code: str, period_month: date) -> Period:
    period = db.scalar(select(Period).where(Period.period_code == period_code))
    if period is not None:
        return period

    period = Period(period_code=period_code, period_month=period_month)
    db.add(period)
    db.flush()
    return period


def _next_upload_seq(db: Session, period_id: int) -> int:
    current_max = db.scalar(select(func.max(UploadBatch.upload_seq)).where(UploadBatch.period_id == period_id))
    return int(current_max or 0) + 1


def _class_identity(row: pd.Series) -> tuple[str | None, str | None]:
    class_date = _to_date(row.get(SCHEDULE_COL_CLASS))
    course_line = _text(row.get(SCHEDULE_COL_PROJECT))

    if class_date is None:
        return None, None

    class_name = class_date.isoformat()
    if course_line:
        return f"{course_line}:{class_name}", class_name
    return class_name, class_name


def _schedule_rule(status: str | None) -> str:
    status_value = (status or "").strip()
    if status_value == "\u5df2\u7ed3\u675f":
        return "entered_only"
    if status_value == "\u62db\u751f\u4e2d":
        return "entered_plus_calculated"
    if status_value == "\u672a\u542f\u52a8":
        return "calculated_only"
    return "fallback"


def _build_table_summaries(processed_result) -> list[ImportedTableSummary]:
    row_counts = {
        "reserve_detail": len(processed_result.detail.index),
        "monthly_class": len(processed_result.schedule.index),
        "monthly_target": len(processed_result.target.index),
    }
    return [
        ImportedTableSummary(table_type=table_type, sheet_name=sheet_name, row_count=row_counts[table_type])
        for table_type, sheet_name in TABLE_CONFIGS
    ]


def _dimension_fields(level: str | None, obj: str | None) -> dict[str, str | None]:
    level_value = (level or "").strip()
    target_object = obj or None

    fields = {
        "area_name": None,
        "province_name": None,
        "city_name": None,
        "bd_name": None,
    }

    if level_value == LEVEL_AREA:
        fields["area_name"] = target_object
    elif level_value == LEVEL_PROVINCE:
        fields["province_name"] = target_object
    elif level_value == LEVEL_CITY:
        fields["city_name"] = target_object
    elif level_value.upper() == "BD":
        fields["bd_name"] = target_object

    return fields


def _dimension_level(level: str | None) -> str:
    mapping = {
        LEVEL_NATIONAL: "national",
        LEVEL_AREA: "area",
        LEVEL_PROVINCE: "province",
        LEVEL_CITY: "city",
        "BD": "bd",
        "bd": "bd",
    }
    return mapping.get((level or "").strip(), "unknown")


def _cleanup_created_files(paths: list[Path]) -> None:
    for path in reversed(paths):
        try:
            if path.exists():
                path.unlink()
        except OSError:
            continue


def _build_upload_table_instances(
    *,
    batch_id: int,
    period_id: int,
    upload_seq: int,
    original_filename: str,
    original_path: Path,
    original_sha256: str,
    processed_result,
) -> list[UploadTableInstance]:
    row_counts = {
        "reserve_detail": len(processed_result.detail.index),
        "monthly_class": len(processed_result.schedule.index),
        "monthly_target": len(processed_result.target.index),
    }
    return [
        UploadTableInstance(
            batch_id=batch_id,
            period_id=period_id,
            upload_seq=upload_seq,
            table_type=table_type,
            sheet_name=sheet_name,
            original_filename=original_filename,
            file_path=str(original_path),
            file_sha256=original_sha256,
            row_count=row_counts[table_type],
        )
        for table_type, sheet_name in TABLE_CONFIGS
    ]


def _build_source_rows(
    *,
    period_id: int,
    upload_seq: int,
    detail_table: UploadTableInstance,
    schedule_table: UploadTableInstance,
    target_table: UploadTableInstance,
    raw_workbook,
    processed,
) -> tuple[list[ReserveDetailRow], list[MonthlyClassRow], list[MonthlyTargetRow], list[InboundRow]]:
    detail_source_rows: list[ReserveDetailRow] = []
    for idx, row in raw_workbook.detail.reset_index(drop=True).iterrows():
        detail_source_rows.append(
            ReserveDetailRow(
                table_instance_id=detail_table.table_instance_id,
                period_id=period_id,
                upload_seq=upload_seq,
                row_no=idx + 1,
                course_line=_text(row.get(DETAIL_COL_PROJECT)),
                area_name=_text(row.get(DETAIL_COL_AREA)),
                province_name=_text(row.get(DETAIL_COL_PROVINCE)),
                city_name=_text(row.get(DETAIL_COL_CITY)),
                district_name=_text(row.get(DETAIL_COL_DISTRICT)),
                bd_name=_text(row.get(DETAIL_COL_BD)),
                acquisition_type=_text(row.get(DETAIL_COL_ACQUISITION)),
                project_reliability=_text(row.get(DETAIL_COL_RELIABILITY)),
                project_name=_text(row.get(DETAIL_COL_PROJECT)),
                school_name=None,
                start_date=_to_date(row.get(DETAIL_COL_START)),
                end_date=_to_date(row.get(DETAIL_COL_END)),
                next_week_start_date=_to_date(row.get(DETAIL_COL_NEXT_WEEK_START)),
                next_week_end_date=_to_date(row.get(DETAIL_COL_NEXT_WEEK_END)),
                base_reserve_qty=_quantize_decimal(row.get(DETAIL_COL_BASE_RESERVE), DECIMAL_2),
                base_forecast_revenue=_quantize_decimal(row.get(DETAIL_COL_BASE_FORECAST), DECIMAL_2),
                stretch_reserve_qty=_quantize_decimal(row.get(DETAIL_COL_STRETCH_RESERVE), DECIMAL_2),
                stretch_forecast_revenue=_quantize_decimal(row.get(DETAIL_COL_STRETCH_FORECAST), DECIMAL_2),
                next_week_base_reserve_qty=_quantize_decimal(row.get(DETAIL_COL_NEXT_WEEK_BASE_RESERVE), DECIMAL_2),
                next_week_base_forecast_revenue=None,
                next_week_stretch_reserve_qty=_quantize_decimal(row.get(DETAIL_COL_NEXT_WEEK_STRETCH_RESERVE), DECIMAL_2),
                next_week_stretch_forecast_revenue=None,
                raw_data=_row_to_json(row),
            )
        )

    schedule_source_rows: list[MonthlyClassRow] = []
    processed_schedule = processed.schedule.reset_index(drop=True)
    for idx, row in raw_workbook.schedule.reset_index(drop=True).iterrows():
        processed_row = processed_schedule.iloc[idx] if idx < len(processed_schedule.index) else pd.Series(dtype=object)
        class_key, class_name = _class_identity(processed_row)
        schedule_source_rows.append(
            MonthlyClassRow(
                table_instance_id=schedule_table.table_instance_id,
                period_id=period_id,
                upload_seq=upload_seq,
                row_no=idx + 1,
                course_line=_text(row.get(SCHEDULE_COL_PROJECT)),
                class_key=class_key,
                class_seq=None,
                class_name=class_name,
                enrollment_status=_text(row.get(SCHEDULE_COL_ENROLLMENT)),
                inbound_start_date=_to_date(row.get(SCHEDULE_COL_INBOUND_START)),
                inbound_end_date=_to_date(row.get(SCHEDULE_COL_INBOUND_END)),
                prefilled_base_qty=_quantize_decimal(row.get(DETAIL_COL_BASE_RESERVE), DECIMAL_2),
                prefilled_base_revenue=_quantize_decimal(row.get(DETAIL_COL_BASE_FORECAST), DECIMAL_2),
                prefilled_stretch_qty=_quantize_decimal(row.get(DETAIL_COL_STRETCH_RESERVE), DECIMAL_2),
                prefilled_stretch_revenue=_quantize_decimal(row.get(DETAIL_COL_STRETCH_FORECAST), DECIMAL_2),
                raw_data=_row_to_json(row),
            )
        )

    target_source_rows: list[MonthlyTargetRow] = []
    inbound_source_rows: list[InboundRow] = []
    for idx, row in raw_workbook.target.reset_index(drop=True).iterrows():
        level = _text(row.get(TARGET_COL_LEVEL))
        target_object = _text(row.get(TARGET_COL_OBJECT))
        dim_fields = _dimension_fields(level, target_object)
        raw_json = _row_to_json(row)

        target_source_rows.append(
            MonthlyTargetRow(
                table_instance_id=target_table.table_instance_id,
                period_id=period_id,
                upload_seq=upload_seq,
                row_no=idx + 1,
                target_level=level,
                area_name=dim_fields["area_name"],
                province_name=dim_fields["province_name"],
                city_name=dim_fields["city_name"],
                bd_name=dim_fields["bd_name"],
                target_revenue=_quantize_decimal(row.get(TARGET_COL_REVENUE), DECIMAL_2),
                raw_data=raw_json,
            )
        )

        # The current third sheet carries both target rows and aggregated inbound results.
        inbound_source_rows.append(
            InboundRow(
                table_instance_id=target_table.table_instance_id,
                period_id=period_id,
                upload_seq=upload_seq,
                row_no=idx + 1,
                course_line=None,
                area_name=dim_fields["area_name"],
                province_name=dim_fields["province_name"],
                city_name=dim_fields["city_name"],
                district_name=None,
                bd_name=dim_fields["bd_name"],
                acquisition_type=None,
                inbound_date=None,
                inbound_qty=_quantize_decimal(row.get(TARGET_COL_ENTERED), DECIMAL_2),
                achieved_revenue=_quantize_decimal(row.get(TARGET_COL_ACHIEVED), DECIMAL_2),
                raw_data=raw_json,
            )
        )

    return detail_source_rows, schedule_source_rows, target_source_rows, inbound_source_rows


def import_monthly_workbook(db: Session, upload_file: UploadFile, uploaded_by: str | None = None) -> WorkbookImportResponse:
    filename = upload_file.filename or ""
    if not filename.lower().endswith(".xlsx"):
        raise ValidationError("Only .xlsx files are supported.")

    meta = parse_filename(filename)
    period_code, period_month = _build_period(meta)
    created_paths: list[Path] = []

    try:
        period = _get_or_create_period(db, period_code, period_month)

        # 同期同日期的文件视为覆盖，复用原 upload_seq 并清除旧数据
        existing_batch = db.scalar(
            select(UploadBatch).where(
                UploadBatch.period_id == period.period_id,
                UploadBatch.source_record_mmdd == meta.file_date_code,
            )
        ) if meta.file_date_code else None

        if existing_batch is not None:
            reuse_seq = existing_batch.upload_seq
            delete_upload_batch(db, period_code, reuse_seq)
            # delete_upload_batch commits; re-fetch or re-create period
            period = _get_or_create_period(db, period_code, period_month)
            upload_seq = reuse_seq
        else:
            upload_seq = _next_upload_seq(db, period.period_id)

        batch = UploadBatch(
            period_id=period.period_id,
            upload_seq=upload_seq,
            source_period_year=meta.year,
            source_period_month=meta.month,
            source_record_mmdd=meta.file_date_code,
            uploaded_by=uploaded_by,
            status="processing",
        )
        db.add(batch)
        db.flush()

        original_file = store_upload_file(upload_file, build_original_workbook_path(period_code, upload_seq, filename))
        created_paths.append(original_file.path)

        raw_workbook = read_xlsx(original_file.path)
        completed_output_path = build_completed_output_path(
            original_file.path,
            build_completed_workbook_dir(period_code, upload_seq),
        )
        processed = process_xlsx_to_xlsx(
            original_file.path,
            completed_output_path,
            round_for_export=False,
        )
        if processed.output_path is None:
            raise ValidationError("Completed workbook was not generated.")

        created_paths.append(processed.output_path)
        completed_file = describe_local_file(processed.output_path)
        completed_workbook_filename = build_workbook_filename(
            record_mmdd=meta.file_date_code,
            period_year=meta.year,
            source_period_month=meta.month,
        )

        db.add_all(
            [
                UploadedFile(
                    batch_id=batch.batch_id,
                    period_id=period.period_id,
                    upload_seq=upload_seq,
                    file_role="original_workbook",
                    original_filename=filename,
                    stored_filename=original_file.path.name,
                    file_path=str(original_file.path),
                    file_sha256=original_file.sha256,
                    file_size_bytes=original_file.size_bytes,
                    content_type=upload_file.content_type,
                ),
                UploadedFile(
                    batch_id=batch.batch_id,
                    period_id=period.period_id,
                    upload_seq=upload_seq,
                    file_role="completed_workbook",
                    original_filename=completed_workbook_filename,
                    stored_filename=completed_workbook_filename,
                    file_path=str(processed.output_path),
                    file_sha256=completed_file.sha256,
                    file_size_bytes=completed_file.size_bytes,
                    content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                ),
            ]
        )
        db.flush()

        table_instances = _build_upload_table_instances(
            batch_id=batch.batch_id,
            period_id=period.period_id,
            upload_seq=upload_seq,
            original_filename=filename,
            original_path=original_file.path,
            original_sha256=original_file.sha256,
            processed_result=processed,
        )
        db.add_all(table_instances)
        db.flush()
        table_instance_map = {row.table_type: row for row in table_instances}

        detail_source_rows, schedule_source_rows, target_source_rows, inbound_source_rows = _build_source_rows(
            period_id=period.period_id,
            upload_seq=upload_seq,
            detail_table=table_instance_map["reserve_detail"],
            schedule_table=table_instance_map["monthly_class"],
            target_table=table_instance_map["monthly_target"],
            raw_workbook=raw_workbook,
            processed=processed,
        )
        db.add_all(detail_source_rows + schedule_source_rows + target_source_rows + inbound_source_rows)
        db.flush()

        existing_schedules = db.scalars(
            select(PeriodClassSchedule).where(PeriodClassSchedule.period_id == period.period_id)
        ).all()
        schedule_id_map = {(row.course_line, row.class_key): row.schedule_id for row in existing_schedules}

        # 课线以该期月第一次上传为准；后续上传跳过插入，复用已有 schedule。
        processed_schedule = processed.schedule.reset_index(drop=True)
        if not existing_schedules:
            schedule_rows: list[PeriodClassSchedule] = []
            seen_schedule_keys: set[tuple[str, str]] = set()
            for _, schedule_row in processed_schedule.iterrows():
                class_key, class_name = _class_identity(schedule_row)
                if class_key is None:
                    continue

                course_line = _text(schedule_row.get(SCHEDULE_COL_PROJECT)) or "unknown"
                schedule_identity = (course_line, class_key)
                if schedule_identity in seen_schedule_keys:
                    continue
                seen_schedule_keys.add(schedule_identity)

                schedule_rows.append(
                    PeriodClassSchedule(
                        period_id=period.period_id,
                        course_line=course_line,
                        class_key=class_key,
                        class_seq=None,
                        class_name=class_name,
                        inbound_start_date=_to_date(schedule_row.get(SCHEDULE_COL_INBOUND_START)) or period_month,
                        inbound_end_date=_to_date(schedule_row.get(SCHEDULE_COL_INBOUND_END)) or period_month,
                        source_table_instance_id=table_instance_map["monthly_class"].table_instance_id,
                    )
                )
            db.add_all(schedule_rows)
            db.flush()
            schedule_id_map.update({(row.course_line, row.class_key): row.schedule_id for row in schedule_rows})

        detail_completed_rows: list[ReserveDetailCompleted] = []
        for idx, detail_row in processed.detail.reset_index(drop=True).iterrows():
            source_row = detail_source_rows[idx]
            detail_completed_rows.append(
                ReserveDetailCompleted(
                    period_id=period.period_id,
                    upload_seq=upload_seq,
                    source_row_id=source_row.id,
                    course_line=source_row.course_line,
                    area_name=source_row.area_name,
                    province_name=source_row.province_name,
                    city_name=source_row.city_name,
                    district_name=source_row.district_name,
                    bd_name=source_row.bd_name,
                    acquisition_type=source_row.acquisition_type,
                    project_reliability=source_row.project_reliability,
                    project_name=source_row.project_name,
                    school_name=source_row.school_name,
                    start_date=source_row.start_date,
                    end_date=source_row.end_date,
                    next_week_start_date=source_row.next_week_start_date,
                    next_week_end_date=source_row.next_week_end_date,
                    base_reserve_qty=_quantize_decimal(detail_row.get(DETAIL_COL_BASE_RESERVE), DECIMAL_2),
                    base_forecast_revenue=_quantize_decimal(detail_row.get(DETAIL_COL_BASE_FORECAST), DECIMAL_2),
                    stretch_reserve_qty=_quantize_decimal(detail_row.get(DETAIL_COL_STRETCH_RESERVE), DECIMAL_2),
                    stretch_forecast_revenue=_quantize_decimal(detail_row.get(DETAIL_COL_STRETCH_FORECAST), DECIMAL_2),
                    next_week_base_reserve_qty=_quantize_decimal(detail_row.get(DETAIL_COL_NEXT_WEEK_BASE_RESERVE), DECIMAL_2),
                    next_week_base_forecast_revenue=None,
                    next_week_stretch_reserve_qty=_quantize_decimal(detail_row.get(DETAIL_COL_NEXT_WEEK_STRETCH_RESERVE), DECIMAL_2),
                    next_week_stretch_forecast_revenue=None,
                    customer_days=None,
                    next_week_customer_days=None,
                    base_reserve_daily_next_week=None,
                    base_reserve_daily_other=None,
                    base_revenue_daily_next_week=None,
                    base_revenue_daily_other=None,
                    stretch_reserve_daily_next_week=None,
                    stretch_reserve_daily_other=None,
                    stretch_revenue_daily_next_week=None,
                    stretch_revenue_daily_other=None,
                    validation_status="success",
                    validation_message=None,
                    raw_data=_row_to_json(detail_row),
                )
            )

        schedule_completed_rows: list[MonthlyClassCompleted] = []
        raw_schedule = raw_workbook.schedule.reset_index(drop=True)
        for idx, schedule_row in processed_schedule.iterrows():
            raw_row = raw_schedule.iloc[idx] if idx < len(raw_schedule.index) else pd.Series(dtype=object)
            source_row = schedule_source_rows[idx]
            class_key = source_row.class_key
            course_line = source_row.course_line
            schedule_id = schedule_id_map.get((course_line or "unknown", class_key or ""))

            schedule_completed_rows.append(
                MonthlyClassCompleted(
                    period_id=period.period_id,
                    upload_seq=upload_seq,
                    source_row_id=source_row.id,
                    schedule_id=schedule_id,
                    course_line=course_line,
                    class_key=class_key,
                    class_seq=source_row.class_seq,
                    class_name=source_row.class_name,
                    enrollment_status=_text(schedule_row.get(SCHEDULE_COL_ENROLLMENT)),
                    inbound_start_date=_to_date(schedule_row.get(SCHEDULE_COL_INBOUND_START)),
                    inbound_end_date=_to_date(schedule_row.get(SCHEDULE_COL_INBOUND_END)),
                    prefilled_base_qty=_quantize_decimal(raw_row.get(DETAIL_COL_BASE_RESERVE), DECIMAL_2),
                    prefilled_base_revenue=_quantize_decimal(raw_row.get(DETAIL_COL_BASE_FORECAST), DECIMAL_2),
                    prefilled_stretch_qty=_quantize_decimal(raw_row.get(DETAIL_COL_STRETCH_RESERVE), DECIMAL_2),
                    prefilled_stretch_revenue=_quantize_decimal(raw_row.get(DETAIL_COL_STRETCH_FORECAST), DECIMAL_2),
                    calc_base_reserve_qty=_quantize_decimal(schedule_row.get(DETAIL_COL_BASE_RESERVE), DECIMAL_2),
                    calc_base_forecast_revenue=_quantize_decimal(schedule_row.get(DETAIL_COL_BASE_FORECAST), DECIMAL_2),
                    calc_stretch_reserve_qty=_quantize_decimal(schedule_row.get(DETAIL_COL_STRETCH_RESERVE), DECIMAL_2),
                    calc_stretch_forecast_revenue=_quantize_decimal(schedule_row.get(DETAIL_COL_STRETCH_FORECAST), DECIMAL_2),
                    final_base_reserve_qty=_quantize_decimal(schedule_row.get(SCHEDULE_COL_BASE_TOTAL_RESERVE), DECIMAL_2),
                    final_base_forecast_revenue=_quantize_decimal(schedule_row.get(SCHEDULE_COL_BASE_TOTAL_FORECAST), DECIMAL_2),
                    final_stretch_reserve_qty=_quantize_decimal(schedule_row.get(SCHEDULE_COL_STRETCH_TOTAL_RESERVE), DECIMAL_2),
                    final_stretch_forecast_revenue=_quantize_decimal(schedule_row.get(SCHEDULE_COL_STRETCH_TOTAL_FORECAST), DECIMAL_2),
                    calc_rule=_schedule_rule(_text(schedule_row.get(SCHEDULE_COL_ENROLLMENT))),
                    validation_status="success",
                    validation_message=None,
                    raw_data=_row_to_json(schedule_row),
                )
            )

        target_completed_rows: list[MonthlyTargetCompleted] = []
        inbound_completed_rows: list[InboundCompleted] = []
        fact_rows: list[MonthlySnapshotMetric] = []
        processed_target = processed.target.reset_index(drop=True)
        for idx, target_row in processed_target.iterrows():
            source_row = target_source_rows[idx]
            inbound_source_row = inbound_source_rows[idx]
            level = _text(target_row.get(TARGET_COL_LEVEL))
            target_object = _text(target_row.get(TARGET_COL_OBJECT))
            dim_fields = _dimension_fields(level, target_object)

            target_completed_rows.append(
                MonthlyTargetCompleted(
                    period_id=period.period_id,
                    upload_seq=upload_seq,
                    source_row_id=source_row.id,
                    target_level=level,
                    area_name=dim_fields["area_name"],
                    province_name=dim_fields["province_name"],
                    city_name=dim_fields["city_name"],
                    bd_name=dim_fields["bd_name"],
                    target_revenue=_quantize_decimal(target_row.get(TARGET_COL_REVENUE), DECIMAL_2),
                    inbound_qty=_quantize_decimal(target_row.get(TARGET_COL_ENTERED), DECIMAL_2),
                    achieved_revenue=_quantize_decimal(target_row.get(TARGET_COL_ACHIEVED), DECIMAL_2),
                    base_reserve_qty=_quantize_decimal(target_row.get(DETAIL_COL_BASE_RESERVE), DECIMAL_2),
                    base_forecast_revenue=_quantize_decimal(target_row.get(DETAIL_COL_BASE_FORECAST), DECIMAL_2),
                    base_total_reserve_qty=_quantize_decimal(target_row.get(SCHEDULE_COL_BASE_TOTAL_RESERVE), DECIMAL_2),
                    base_total_revenue=_quantize_decimal(target_row.get(SCHEDULE_COL_BASE_TOTAL_FORECAST), DECIMAL_2),
                    base_achievement_rate=_quantize_decimal(target_row.get(TARGET_COL_BASE_ACHIEVEMENT), DECIMAL_6),
                    stretch_reserve_qty=_quantize_decimal(target_row.get(DETAIL_COL_STRETCH_RESERVE), DECIMAL_2),
                    stretch_forecast_revenue=_quantize_decimal(target_row.get(DETAIL_COL_STRETCH_FORECAST), DECIMAL_2),
                    stretch_total_reserve_qty=_quantize_decimal(target_row.get(SCHEDULE_COL_STRETCH_TOTAL_RESERVE), DECIMAL_2),
                    stretch_total_revenue=_quantize_decimal(target_row.get(SCHEDULE_COL_STRETCH_TOTAL_FORECAST), DECIMAL_2),
                    stretch_achievement_rate=_quantize_decimal(target_row.get(TARGET_COL_STRETCH_ACHIEVEMENT), DECIMAL_6),
                    validation_status="success",
                    validation_message=None,
                    raw_data=_row_to_json(target_row),
                )
            )

            inbound_completed_rows.append(
                InboundCompleted(
                    period_id=period.period_id,
                    upload_seq=upload_seq,
                    source_row_id=inbound_source_row.id,
                    course_line=None,
                    area_name=inbound_source_row.area_name,
                    province_name=inbound_source_row.province_name,
                    city_name=inbound_source_row.city_name,
                    district_name=inbound_source_row.district_name,
                    bd_name=inbound_source_row.bd_name,
                    acquisition_type=None,
                    inbound_date=None,
                    inbound_qty=_quantize_decimal(target_row.get(TARGET_COL_ENTERED), DECIMAL_2),
                    achieved_revenue=_quantize_decimal(target_row.get(TARGET_COL_ACHIEVED), DECIMAL_2),
                    matched_schedule_id=None,
                    matched_class_key=None,
                    matched_class_seq=None,
                    matched_class_name=None,
                    is_in_class_period=None,
                    final_inbound_qty=_quantize_decimal(target_row.get(TARGET_COL_ENTERED), DECIMAL_2),
                    final_achieved_revenue=_quantize_decimal(target_row.get(TARGET_COL_ACHIEVED), DECIMAL_2),
                    validation_status="derived",
                    validation_message="derived from target summary sheet",
                    raw_data=_row_to_json(target_row),
                )
            )

            fact_rows.append(
                MonthlySnapshotMetric(
                    period_id=period.period_id,
                    upload_seq=upload_seq,
                    dimension_level=_dimension_level(level),
                    dimension_key=target_object or _dimension_level(level),
                    dimension_name=target_object or _dimension_level(level),
                    course_line=None,
                    class_key=None,
                    class_name=None,
                    area_name=dim_fields["area_name"],
                    province_name=dim_fields["province_name"],
                    city_name=dim_fields["city_name"],
                    bd_name=dim_fields["bd_name"],
                    acquisition_type=None,
                    project_reliability=None,
                    target_revenue=_quantize_decimal(target_row.get(TARGET_COL_REVENUE), DECIMAL_2),
                    inbound_qty=_quantize_decimal(target_row.get(TARGET_COL_ENTERED), DECIMAL_2),
                    achieved_revenue=_quantize_decimal(target_row.get(TARGET_COL_ACHIEVED), DECIMAL_2),
                    base_reserve_qty=_quantize_decimal(target_row.get(DETAIL_COL_BASE_RESERVE), DECIMAL_2),
                    base_forecast_revenue=_quantize_decimal(target_row.get(DETAIL_COL_BASE_FORECAST), DECIMAL_2),
                    base_total_reserve_qty=_quantize_decimal(target_row.get(SCHEDULE_COL_BASE_TOTAL_RESERVE), DECIMAL_2),
                    base_total_revenue=_quantize_decimal(target_row.get(SCHEDULE_COL_BASE_TOTAL_FORECAST), DECIMAL_2),
                    base_achievement_rate=_quantize_decimal(target_row.get(TARGET_COL_BASE_ACHIEVEMENT), DECIMAL_6),
                    stretch_reserve_qty=_quantize_decimal(target_row.get(DETAIL_COL_STRETCH_RESERVE), DECIMAL_2),
                    stretch_forecast_revenue=_quantize_decimal(target_row.get(DETAIL_COL_STRETCH_FORECAST), DECIMAL_2),
                    stretch_total_reserve_qty=_quantize_decimal(target_row.get(SCHEDULE_COL_STRETCH_TOTAL_RESERVE), DECIMAL_2),
                    stretch_total_revenue=_quantize_decimal(target_row.get(SCHEDULE_COL_STRETCH_TOTAL_FORECAST), DECIMAL_2),
                    stretch_achievement_rate=_quantize_decimal(target_row.get(TARGET_COL_STRETCH_ACHIEVEMENT), DECIMAL_6),
                )
            )

        db.add_all(detail_completed_rows)
        db.add_all(schedule_completed_rows)
        db.add_all(target_completed_rows)
        db.add_all(inbound_completed_rows)
        db.add_all(fact_rows)

        batch.status = "success"
        batch.message = "upload completed"
        db.commit()

        original_record = db.scalar(
            select(UploadedFile).where(
                UploadedFile.batch_id == batch.batch_id,
                UploadedFile.file_role == "original_workbook",
            )
        )
        completed_record = db.scalar(
            select(UploadedFile).where(
                UploadedFile.batch_id == batch.batch_id,
                UploadedFile.file_role == "completed_workbook",
            )
        )
        if original_record is None or completed_record is None:
            raise ValidationError("Uploaded file records were not persisted.")

        return WorkbookImportResponse(
            period_code=period_code,
            upload_seq=upload_seq,
            batch_id=batch.batch_id,
            status=batch.status,
            message=batch.message or "upload completed",
            workbook_filename=filename,
            original_file_id=original_record.file_id,
            completed_file_id=completed_record.file_id,
            warnings=processed.warnings,
            tables=_build_table_summaries(processed),
        )
    except Exception:
        db.rollback()
        _cleanup_created_files(created_paths)
        raise


def delete_upload_batch(db: Session, period_code: str, upload_seq: int) -> None:
    period = db.scalar(select(Period).where(Period.period_code == period_code))
    if period is None:
        from app.common.exceptions import NotFoundError
        raise NotFoundError(f"Period not found: {period_code}")

    batch = db.scalar(
        select(UploadBatch).where(
            UploadBatch.period_id == period.period_id,
            UploadBatch.upload_seq == upload_seq,
        )
    )
    if batch is None:
        from app.common.exceptions import NotFoundError
        raise NotFoundError(f"Upload batch not found: {period_code} #{upload_seq}")

    # delete all data rows for this batch (order matters: children before parents)
    for model in (
        MonthlySnapshotMetric,
        InboundCompleted,
        MonthlyTargetCompleted,
        MonthlyClassCompleted,
        ReserveDetailCompleted,
        InboundRow,
        MonthlyTargetRow,
        MonthlyClassRow,
        ReserveDetailRow,
    ):
        db.query(model).filter(
            model.period_id == period.period_id,
            model.upload_seq == upload_seq,
        ).delete(synchronize_session=False)

    # PeriodClassSchedule.source_table_instance_id references upload_table_instances;
    # null it out so we can delete the instances without FK violation.
    from sqlalchemy import update as sa_update
    batch_instance_ids = db.scalars(
        select(UploadTableInstance.table_instance_id).where(
            UploadTableInstance.batch_id == batch.batch_id
        )
    ).all()
    if batch_instance_ids:
        db.query(PeriodClassSchedule).filter(
            PeriodClassSchedule.source_table_instance_id.in_(batch_instance_ids)
        ).update({"source_table_instance_id": None}, synchronize_session=False)

    # delete table instances (child of batch)
    db.query(UploadTableInstance).filter(
        UploadTableInstance.batch_id == batch.batch_id,
    ).delete(synchronize_session=False)

    # collect file paths before deleting records
    file_records = db.scalars(
        select(UploadedFile).where(UploadedFile.batch_id == batch.batch_id)
    ).all()
    file_paths = [Path(r.file_path) for r in file_records]

    db.query(UploadedFile).filter(
        UploadedFile.batch_id == batch.batch_id,
    ).delete(synchronize_session=False)

    db.delete(batch)
    db.flush()  # flush so the count below reflects the deletion

    # if no more batches for this period, delete the period too
    remaining = db.scalar(
        select(func.count()).where(UploadBatch.period_id == period.period_id)
    )
    if remaining == 0:
        db.query(PeriodClassSchedule).filter(
            PeriodClassSchedule.period_id == period.period_id,
        ).delete(synchronize_session=False)
        db.delete(period)

    db.commit()
    _cleanup_created_files(file_paths)


def list_periods(db: Session) -> list[PeriodSummary]:
    periods = db.scalars(select(Period).order_by(Period.period_month.desc(), Period.period_id.desc())).all()
    return [PeriodSummary(period_id=period.period_id, period_code=period.period_code) for period in periods]


def list_period_uploads(db: Session, period_code: str) -> list[UploadBatchSummary]:
    period = db.scalar(select(Period).where(Period.period_code == period_code))
    if period is None:
        return []

    batches = db.scalars(select(UploadBatch).where(UploadBatch.period_id == period.period_id)).all()
    previous_batch_map = build_previous_batch_map(batches)
    return [
        UploadBatchSummary(
            batch_id=batch.batch_id,
            upload_seq=batch.upload_seq,
            compare_previous_upload_seq=(
                previous_batch_map.get(batch.upload_seq).upload_seq
                if previous_batch_map.get(batch.upload_seq) is not None
                else None
            ),
            source_period_year=batch.source_period_year,
            source_period_month=batch.source_period_month,
            source_record_mmdd=batch.source_record_mmdd,
            uploaded_by=batch.uploaded_by,
            uploaded_at=batch.uploaded_at,
            status=batch.status,
            message=batch.message,
        )
        for batch in order_batches_for_display(batches)
    ]
