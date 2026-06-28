from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, Index, Integer, Text, UniqueConstraint, text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.db_compat import BIGINT_TYPE, CURRENT_TIMESTAMP_DEFAULT, fk, mmdd_check_constraint, table_args


class Period(Base):
    __tablename__ = "periods"
    __table_args__ = table_args(UniqueConstraint("period_code", name="uq_periods_period_code"), schema="meta")

    period_id: Mapped[int] = mapped_column(BIGINT_TYPE, primary_key=True, autoincrement=True)
    period_code: Mapped[str] = mapped_column(Text, nullable=False)
    period_month: Mapped[date] = mapped_column(Date, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=CURRENT_TIMESTAMP_DEFAULT, nullable=False)


class UploadBatch(Base):
    __tablename__ = "upload_batches"
    __table_args__ = table_args(
        UniqueConstraint("period_id", "upload_seq", name="uq_upload_batches_period_seq"),
        CheckConstraint(
            "source_period_year IS NULL OR (source_period_year >= 1000 AND source_period_year <= 9999)",
            name="ck_upload_batches_source_period_year",
        ),
        CheckConstraint(
            "source_period_month IS NULL OR (source_period_month >= 1 AND source_period_month <= 12)",
            name="ck_upload_batches_source_period_month",
        ),
        mmdd_check_constraint("ck_upload_batches_source_record_mmdd"),
        Index("idx_upload_batches_period_seq", "period_id", "upload_seq"),
        schema="meta",
    )

    batch_id: Mapped[int] = mapped_column(BIGINT_TYPE, primary_key=True, autoincrement=True)
    period_id: Mapped[int] = mapped_column(BIGINT_TYPE, ForeignKey(fk("meta.periods.period_id")), nullable=False)
    upload_seq: Mapped[int] = mapped_column(Integer, nullable=False)
    source_period_year: Mapped[int | None] = mapped_column(Integer)
    source_period_month: Mapped[int | None] = mapped_column(Integer)
    source_record_mmdd: Mapped[str | None] = mapped_column(Text)
    uploaded_by: Mapped[str | None] = mapped_column(Text)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=CURRENT_TIMESTAMP_DEFAULT, nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("'uploaded'"))
    message: Mapped[str | None] = mapped_column(Text)


class UploadTableInstance(Base):
    __tablename__ = "upload_table_instances"
    __table_args__ = table_args(
        UniqueConstraint("period_id", "upload_seq", "table_type", name="uq_table_instances_period_seq_type"),
        CheckConstraint(
            "table_type IN ('reserve_detail', 'monthly_class', 'monthly_target', 'inbound')",
            name="ck_table_instances_type",
        ),
        CheckConstraint(
            "sheet_name IN ('储备明细表', '每月班期表', '每月目标表', '已进线表')",
            name="ck_table_instances_sheet_name",
        ),
        CheckConstraint(
            "((sheet_name = '储备明细表' AND table_type = 'reserve_detail') "
            "OR (sheet_name = '每月班期表' AND table_type = 'monthly_class') "
            "OR (sheet_name IN ('每月目标表', '已进线表') AND table_type = 'monthly_target') "
            "OR (sheet_name = '已进线表' AND table_type = 'inbound'))",
            name="ck_table_instances_sheet_type_match",
        ),
        Index("idx_table_instances_period_seq_type", "period_id", "upload_seq", "table_type"),
        schema="meta",
    )

    table_instance_id: Mapped[int] = mapped_column(BIGINT_TYPE, primary_key=True, autoincrement=True)
    batch_id: Mapped[int] = mapped_column(BIGINT_TYPE, ForeignKey(fk("meta.upload_batches.batch_id")), nullable=False)
    period_id: Mapped[int] = mapped_column(BIGINT_TYPE, ForeignKey(fk("meta.periods.period_id")), nullable=False)
    upload_seq: Mapped[int] = mapped_column(Integer, nullable=False)
    table_type: Mapped[str] = mapped_column(Text, nullable=False)
    sheet_name: Mapped[str] = mapped_column(Text, nullable=False)
    original_filename: Mapped[str | None] = mapped_column(Text)
    file_path: Mapped[str | None] = mapped_column(Text)
    file_sha256: Mapped[str | None] = mapped_column(Text)
    row_count: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=CURRENT_TIMESTAMP_DEFAULT, nullable=False)
