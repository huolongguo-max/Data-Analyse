from __future__ import annotations

from fastapi import APIRouter

from app.common.response import ok
from app.deps import CurrentUser, DbDep
from app.services.dashboard_service import get_compare_dashboard, get_single_dashboard

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/single")
def dashboard_single(
    db: DbDep,
    _: CurrentUser,
    period_code: str,
    upload_seq: int,
    dimension_level: str,
    scenario: str = "all",
):
    result = get_single_dashboard(
        db,
        period_code=period_code,
        upload_seq=upload_seq,
        dimension_level=dimension_level,
        scenario=scenario,
    )
    return ok(data=result.model_dump())


@router.get("/compare")
def dashboard_compare(
    db: DbDep,
    _: CurrentUser,
    period_code: str,
    upload_seq: int,
    dimension_level: str,
    scenario: str = "all",
):
    result = get_compare_dashboard(
        db,
        period_code=period_code,
        upload_seq=upload_seq,
        dimension_level=dimension_level,
        scenario=scenario,
    )
    return ok(data=result.model_dump())
