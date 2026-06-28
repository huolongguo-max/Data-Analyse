from __future__ import annotations

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from app.common.response import ok
from app.common.security import hash_password
from app.deps import DbDep, SuperAdminUser
from app.models.user import User

router = APIRouter(prefix="/users", tags=["用户管理"])


class CreateUserRequest(BaseModel):
    username: str
    password: str
    permissions: dict = {}


class UpdateUserRequest(BaseModel):
    password: str | None = None
    permissions: dict | None = None
    is_active: bool | None = None


def _user_dict(user: User) -> dict:
    return {
        "id": user.id,
        "username": user.username,
        "role": user.role,
        "is_active": user.is_active,
        "permissions": user.permissions,
        "created_at": user.created_at.isoformat() if user.created_at else None,
    }


@router.get("")
def list_users(db: DbDep, _: SuperAdminUser):
    users = db.query(User).filter(User.role == "viewer").order_by(User.created_at).all()
    return ok(data=[_user_dict(u) for u in users])


@router.post("")
def create_user(body: CreateUserRequest, db: DbDep, _: SuperAdminUser):
    existing = db.query(User).filter(User.username == body.username).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="用户名已存在")
    user = User(
        username=body.username,
        hashed_password=hash_password(body.password),
        role="viewer",
        is_active=True,
    )
    user.permissions = body.permissions
    db.add(user)
    db.commit()
    db.refresh(user)
    return ok(data=_user_dict(user), message="账号已创建")


@router.put("/{user_id}")
def update_user(user_id: int, body: UpdateUserRequest, db: DbDep, _: SuperAdminUser):
    user = db.get(User, user_id)
    if user is None or user.is_super_admin:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")
    if body.password is not None:
        user.hashed_password = hash_password(body.password)
    if body.permissions is not None:
        user.permissions = body.permissions
    if body.is_active is not None:
        user.is_active = body.is_active
    db.commit()
    db.refresh(user)
    return ok(data=_user_dict(user), message="账号已更新")


@router.delete("/{user_id}")
def delete_user(user_id: int, db: DbDep, _: SuperAdminUser):
    user = db.get(User, user_id)
    if user is None or user.is_super_admin:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")
    db.delete(user)
    db.commit()
    return ok(message="账号已删除")
