from __future__ import annotations

from fastapi import APIRouter, File, Form, UploadFile

from app.common.response import created, ok
from app.deps import CurrentUser, DbDep, SuperAdminUser
from app.services.import_service import delete_upload_batch, import_monthly_workbook, list_period_uploads, list_periods

router = APIRouter(tags=["imports"])


@router.post("/imports/workbook")
@router.post("/uploads/monthly-batch")
def upload_monthly_workbook(
    db: DbDep,
    _: SuperAdminUser,
    file: UploadFile = File(...),
    uploaded_by: str | None = Form(default=None),
):
    result = import_monthly_workbook(db=db, upload_file=file, uploaded_by=uploaded_by)
    return created(data=result.model_dump(), message="uploaded")


@router.get("/imports/periods")
@router.get("/periods")
def get_periods(db: DbDep, _: CurrentUser):
    periods = list_periods(db)
    return ok(data=[period.model_dump() for period in periods])


@router.get("/imports/periods/{period_code}/uploads")
@router.get("/periods/{period_code}/uploads")
def get_period_uploads(period_code: str, db: DbDep, _: CurrentUser):
    uploads = list_period_uploads(db, period_code)
    return ok(data=[upload.model_dump() for upload in uploads])


@router.delete("/periods/{period_code}/uploads/{upload_seq}")
def delete_period_upload(period_code: str, upload_seq: int, db: DbDep, _: SuperAdminUser):
    delete_upload_batch(db, period_code, upload_seq)
    return ok(message="deleted")
