from __future__ import annotations

from app.common.security import hash_password
from app.database import SessionLocal
from app.main import SUPER_ADMINS, _seed_super_admins
from app.models.user import User


def _login(client, username: str, password: str):
    return client.post(
        "/api/auth/login",
        data={"username": username, "password": password},
    )


def _reset_super_admins() -> None:
    with SessionLocal() as db:
        for admin in SUPER_ADMINS:
            user = db.query(User).filter(User.username == admin["username"]).first()
            assert user is not None
            user.role = "super_admin"
            user.is_active = True
            user.hashed_password = hash_password(admin["password"])
        db.commit()


def test_seeded_super_admins_can_login(client) -> None:
    _reset_super_admins()

    for admin in SUPER_ADMINS:
        response = _login(client, admin["username"], admin["password"])

        assert response.status_code == 200
        payload = response.json()
        assert payload["username"] == admin["username"]
        assert payload["role"] == "super_admin"


def test_change_password_updates_current_user_credentials(client) -> None:
    _reset_super_admins()
    admin = SUPER_ADMINS[0]
    new_password = "codemao5678"

    try:
        login_response = _login(client, admin["username"], admin["password"])
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]

        response = client.post(
            "/api/auth/change-password",
            json={
                "current_password": admin["password"],
                "new_password": new_password,
            },
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        assert response.json()["message"] == "密码已修改，请重新登录"
        assert _login(client, admin["username"], admin["password"]).status_code == 401
        assert _login(client, admin["username"], new_password).status_code == 200
    finally:
        _reset_super_admins()


def test_seed_super_admins_disables_legacy_super_admins(client) -> None:
    with SessionLocal() as db:
        legacy = db.query(User).filter(User.username == "superadmin1").first()
        if legacy is None:
            legacy = User(
                username="superadmin1",
                hashed_password=hash_password("legacypass123"),
                role="super_admin",
                is_active=True,
            )
            db.add(legacy)
            db.commit()
            db.refresh(legacy)
        else:
            legacy.role = "super_admin"
            legacy.is_active = True
            db.commit()

        _seed_super_admins(db)
        db.refresh(legacy)

        assert legacy.is_active is False
