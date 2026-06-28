from __future__ import annotations

from datetime import datetime

from app.main import SUPER_ADMINS
from app.schemas.dashboard import DashboardCompareResponse, DashboardSingleResponse
from app.schemas.import_task import PeriodSummary, UploadBatchSummary


def _auth_headers(client) -> dict[str, str]:
    admin = SUPER_ADMINS[0]
    response = client.post(
        "/api/auth/login",
        data={"username": admin["username"], "password": admin["password"]},
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_periods_alias_route_is_available(client, monkeypatch) -> None:
    monkeypatch.setattr(
        "app.routers.imports.list_periods",
        lambda db: [PeriodSummary(period_id=1, period_code="2026-03")],
    )
    response = client.get("/api/periods", headers=_auth_headers(client))
    assert response.status_code == 200
    payload = response.json()
    assert payload["data"][0]["period_code"] == "2026-03"


def test_uploads_alias_route_is_available(client, monkeypatch) -> None:
    monkeypatch.setattr(
        "app.routers.imports.list_period_uploads",
        lambda db, period_code: [
            UploadBatchSummary(
                batch_id=1,
                upload_seq=2,
                uploaded_at=datetime(2026, 6, 11, 20, 0, 0),
                status="success",
                message="ok",
            )
        ],
    )
    response = client.get("/api/periods/2026-03/uploads", headers=_auth_headers(client))
    assert response.status_code == 200
    payload = response.json()
    assert payload["data"][0]["upload_seq"] == 2


def test_dashboard_single_route_is_available(client, monkeypatch) -> None:
    monkeypatch.setattr(
        "app.routers.dashboard.get_single_dashboard",
        lambda *args, **kwargs: DashboardSingleResponse(
            period_code="2026-03",
            upload_seq=2,
            dimension_level="area",
            scenario="all",
            total=1,
            rows=[{"dimension_name": "粤海片区"}],
        ),
    )
    response = client.get(
        "/api/dashboard/single",
        params={"period_code": "2026-03", "upload_seq": 2, "dimension_level": "area"},
        headers=_auth_headers(client),
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["data"]["rows"][0]["dimension_name"] == "粤海片区"


def test_dashboard_compare_route_is_available(client, monkeypatch) -> None:
    monkeypatch.setattr(
        "app.routers.dashboard.get_compare_dashboard",
        lambda *args, **kwargs: DashboardCompareResponse(
            show_compare=True,
            period_code="2026-03",
            current_upload_seq=2,
            previous_upload_seq=1,
            dimension_level="bd",
            scenario="base",
            total=1,
            rows=[{"dimension_name": "庄小龙", "diff_base_total_revenue": 1000.0}],
        ),
    )
    response = client.get(
        "/api/dashboard/compare",
        params={"period_code": "2026-03", "upload_seq": 2, "dimension_level": "bd", "scenario": "base"},
        headers=_auth_headers(client),
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["data"]["show_compare"] is True
