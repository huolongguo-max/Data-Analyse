from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.common.response import ok
from app.common.security import create_access_token, hash_password, verify_password
from app.deps import CurrentUser, DbDep
from app.models.user import User

router = APIRouter(prefix="/auth", tags=["认证"])


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


@router.post("/login")
def login(form: OAuth2PasswordRequestForm = Depends(), db: DbDep = None):
    user = db.query(User).filter(User.username == form.username).first()
    if user is None or not verify_password(form.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="账号或密码错误")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="账号已被禁用")
    token = create_access_token(subject=user.id)
    return {
        "access_token": token,
        "token_type": "bearer",
        "role": user.role,
        "username": user.username,
        "permissions": user.permissions,
    }


@router.get("/me")
def get_me(current_user: CurrentUser):
    return ok(data={
        "id": current_user.id,
        "username": current_user.username,
        "role": current_user.role,
        "permissions": current_user.permissions,
    })


@router.post("/change-password")
def change_password(body: ChangePasswordRequest, current_user: CurrentUser, db: DbDep):
    if not body.current_password or not body.new_password:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="请完整输入当前密码和新密码")
    if len(body.new_password) < 8:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="新密码至少需要 8 位")
    if not verify_password(body.current_password, current_user.hashed_password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="当前密码错误")
    if verify_password(body.new_password, current_user.hashed_password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="新密码不能与当前密码相同")

    current_user.hashed_password = hash_password(body.new_password)
    db.add(current_user)
    db.commit()
    return ok(message="密码已修改，请重新登录")
