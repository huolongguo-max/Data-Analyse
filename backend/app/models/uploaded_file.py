from __future__ import annotations

from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Integer, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.db_compat import BIGINT_TYPE, CURRENT_TIMESTAMP_DEFAULT, fk, table_args


class UploadedFile(Base):
    __tablename__ = "uploaded_files"
    __table_args__ = table_args(
        UniqueConstraint("batch_id", "file_role", name="uq_uploaded_files_batch_role"),
        CheckConstraint(
            "file_role IN ('original_workbook', 'completed_workbook')",
            name="ck_uploaded_files_role",
        ),
        Index("idx_uploaded_files_period_seq_role", "period_id", "upload_seq", "file_role"),
        Index("idx_uploaded_files_sha256", "file_sha256"),
        schema="meta",
    )

    file_id: Mapped[int] = mapped_column(BIGINT_TYPE, primary_key=True, autoincrement=True)
    batch_id: Mapped[int] = mapped_column(BIGINT_TYPE, ForeignKey(fk("meta.upload_batches.batch_id")), nullable=False)
    period_id: Mapped[int] = mapped_column(BIGINT_TYPE, ForeignKey(fk("meta.periods.period_id")), nullable=False)
    upload_seq: Mapped[int] = mapped_column(Integer, nullable=False)

    file_role: Mapped[str] = mapped_column(Text, nullable=False)
    original_filename: Mapped[str] = mapped_column(Text, nullable=False)
    stored_filename: Mapped[str] = mapped_column(Text, nullable=False)
    file_path: Mapped[str] = mapped_column(Text, nullable=False)
    file_sha256: Mapped[str] = mapped_column(Text, nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(BIGINT_TYPE, nullable=False)
    content_type: Mapped[str | None] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=CURRENT_TIMESTAMP_DEFAULT, nullable=False)
