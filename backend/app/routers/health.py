from datetime import datetime, timezone
from fastapi import APIRouter

from app.common.response import ok

router = APIRouter(tags=["系统"])


@router.get("/health")
def health_check():
    return ok(data={"status": "ok", "timestamp": datetime.now(timezone.utc).isoformat()})


@router.get("/version")
def get_version():
    return ok(data={"version": "0.1.0", "env": "development"})
