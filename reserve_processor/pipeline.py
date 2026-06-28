# reserve_processor/pipeline.py

from __future__ import annotations

from pathlib import Path

from .detail_calculator import calculate_detail_sheet
from .excel_io import read_xlsx, write_xlsx
from .models import ProcessResult
from .schedule_calculator import calculate_schedule_sheet
from .target_calculator import calculate_target_sheet
from .utils import build_completed_output_path
from .validators import validate_workbook


def process_workbook(input_path: str | Path) -> ProcessResult:
    workbook = read_xlsx(input_path)

    warnings = validate_workbook(
        detail=workbook.detail,
        schedule=workbook.schedule,
        target=workbook.target,
    )

    if (
        workbook.meta.year is None
        or workbook.meta.month is None
        or workbook.meta.version is None
    ):
        warnings.append(f"文件名未匹配规定格式：{workbook.meta.filename}")

    detail_processed, date_axis = calculate_detail_sheet(workbook.detail)

    schedule_processed = calculate_schedule_sheet(
        schedule=workbook.schedule,
        detail=detail_processed,
        date_axis=date_axis,
    )

    target_processed = calculate_target_sheet(
        target=workbook.target,
        detail=detail_processed,
    )

    return ProcessResult(
        meta=workbook.meta,
        detail=detail_processed,
        schedule=schedule_processed,
        target=target_processed,
        warnings=warnings,
    )


def process_xlsx_to_xlsx(
    input_path: str | Path,
    output_path: str | Path | None = None,
    *,
    round_for_export: bool = False,
) -> ProcessResult:
    result = process_workbook(input_path)
    final_output_path = build_completed_output_path(
        input_path=input_path,
        output_path=output_path,
    )

    written_path = write_xlsx(
        output_path=final_output_path,
        template_path=input_path,
        detail=result.detail,
        schedule=result.schedule,
        target=result.target,
        round_for_export=round_for_export,
    )

    result.output_path = written_path
    return result
