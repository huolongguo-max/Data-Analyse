from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class ImportedTableSummary(BaseModel):
    table_type: str
    sheet_name: str
    row_count: int


class WorkbookImportResponse(BaseModel):
    period_code: str
    upload_seq: int
    batch_id: int
    status: str
    message: str
    workbook_filename: str
    original_file_id: int
    completed_file_id: int
    warnings: list[str]
    tables: list[ImportedTableSummary]


class PeriodSummary(BaseModel):
    period_id: int
    period_code: str


class UploadBatchSummary(BaseModel):
    batch_id: int
    upload_seq: int
    compare_previous_upload_seq: int | None = None
    source_period_year: int | None = None
    source_period_month: int | None = None
    source_record_mmdd: str | None = None
    uploaded_by: str | None = None
    uploaded_at: datetime
    status: str
    message: str | None = None
