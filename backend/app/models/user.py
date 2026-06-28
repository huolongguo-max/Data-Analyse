from __future__ import annotations

import json
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(256), nullable=False)
    role: Mapped[str] = mapped_column(String(32), nullable=False, default="viewer")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    # JSON string storing permission config (only used for viewer role)
    permissions_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    @property
    def permissions(self) -> dict:
        if self.permissions_json:
            try:
                return json.loads(self.permissions_json)
            except Exception:
                pass
        return {}

    @permissions.setter
    def permissions(self, value: dict) -> None:
        self.permissions_json = json.dumps(value, ensure_ascii=False)

    @property
    def is_super_admin(self) -> bool:
        return self.role == "super_admin"
