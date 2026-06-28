from __future__ import annotations

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import FileResponse

from app.common.response import ok
from app.deps import CurrentUser, DbDep
from app.services.export_service import (
    get_completed_table_rows,
    get_completed_workbook_filename,
    get_completed_workbook_path,
)

router = APIRouter(prefix="/exports", tags=["导出"])


def _can_export_any(current_user: CurrentUser) -> bool:
    if getattr(current_user, "is_super_admin", False):
        return True
    permissions = getattr(current_user, "permissions", {}) or {}
    return bool(
        permissions.get("single", {}).get("allow_export")
        or permissions.get("compare", {}).get("allow_export")
    )


@router.get("/completed-workbook")
def download_completed_workbook(period_code: str, upload_seq: int, db: DbDep, current_user: CurrentUser):
    if not _can_export_any(current_user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="当前账号未开启复制 / 下载权限")
    file_path = get_completed_workbook_path(db, period_code, upload_seq)
    filename = get_completed_workbook_filename(db, period_code, upload_seq)
    return FileResponse(
        path=file_path,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename=filename,
    )


@router.get("/completed-table")
def get_completed_table(period_code: str, upload_seq: int, table_type: str, db: DbDep, _: CurrentUser):
    result = get_completed_table_rows(db, period_code, upload_seq, table_type)
    return ok(data=result.model_dump())
