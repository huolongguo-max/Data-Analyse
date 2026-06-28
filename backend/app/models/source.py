from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import Date, DateTime, ForeignKey, Index, Integer, Numeric, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.db_compat import BIGINT_TYPE, CURRENT_TIMESTAMP_DEFAULT, JSON_TYPE, fk, table_args


AMOUNT_NUMERIC = Numeric(18, 6)


class ReserveDetailRow(Base):
    __tablename__ = "reserve_detail_rows"
    __table_args__ = table_args(Index("idx_reserve_period_seq", "period_id", "upload_seq"), schema="source")

    id: Mapped[int] = mapped_column(BIGINT_TYPE, primary_key=True, autoincrement=True)
    table_instance_id: Mapped[int] = mapped_column(BIGINT_TYPE, ForeignKey(fk("meta.upload_table_instances.table_instance_id")), nullable=False)
    period_id: Mapped[int] = mapped_column(BIGINT_TYPE, ForeignKey(fk("meta.periods.period_id")), nullable=False)
    upload_seq: Mapped[int] = mapped_column(Integer, nullable=False)
    row_no: Mapped[int | None] = mapped_column(Integer)

    course_line: Mapped[str | None] = mapped_column(Text)
    area_name: Mapped[str | None] = mapped_column(Text)
    province_name: Mapped[str | None] = mapped_column(Text)
    city_name: Mapped[str | None] = mapped_column(Text)
    district_name: Mapped[str | None] = mapped_column(Text)
    bd_name: Mapped[str | None] = mapped_column(Text)
    acquisition_type: Mapped[str | None] = mapped_column(Text)
    project_reliability: Mapped[str | None] = mapped_column(Text)
    project_name: Mapped[str | None] = mapped_column(Text)
    school_name: Mapped[str | None] = mapped_column(Text)

    start_date: Mapped[date | None] = mapped_column(Date)
    end_date: Mapped[date | None] = mapped_column(Date)
    next_week_start_date: Mapped[date | None] = mapped_column(Date)
    next_week_end_date: Mapped[date | None] = mapped_column(Date)

    base_reserve_qty: Mapped[Decimal | None] = mapped_column(AMOUNT_NUMERIC)
    base_forecast_revenue: Mapped[Decimal | None] = mapped_column(AMOUNT_NUMERIC)
    stretch_reserve_qty: Mapped[Decimal | None] = mapped_column(AMOUNT_NUMERIC)
    stretch_forecast_revenue: Mapped[Decimal | None] = mapped_column(AMOUNT_NUMERIC)

    next_week_base_reserve_qty: Mapped[Decimal | None] = mapped_column(AMOUNT_NUMERIC)
    next_week_base_forecast_revenue: Mapped[Decimal | None] = mapped_column(AMOUNT_NUMERIC)
    next_week_stretch_reserve_qty: Mapped[Decimal | None] = mapped_column(AMOUNT_NUMERIC)
    next_week_stretch_forecast_revenue: Mapped[Decimal | None] = mapped_column(AMOUNT_NUMERIC)

    raw_data: Mapped[dict[str, Any] | None] = mapped_column(JSON_TYPE)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=CURRENT_TIMESTAMP_DEFAULT, nullable=False)


class MonthlyClassRow(Base):
    __tablename__ = "monthly_class_rows"
    __table_args__ = table_args(Index("idx_class_period_seq", "period_id", "upload_seq"), schema="source")

    id: Mapped[int] = mapped_column(BIGINT_TYPE, primary_key=True, autoincrement=True)
    table_instance_id: Mapped[int] = mapped_column(BIGINT_TYPE, ForeignKey(fk("meta.upload_table_instances.table_instance_id")), nullable=False)
    period_id: Mapped[int] = mapped_column(BIGINT_TYPE, ForeignKey(fk("meta.periods.period_id")), nullable=False)
    upload_seq: Mapped[int] = mapped_column(Integer, nullable=False)
    row_no: Mapped[int | None] = mapped_column(Integer)

    course_line: Mapped[str | None] = mapped_column(Text)
    class_key: Mapped[str | None] = mapped_column(Text)
    class_seq: Mapped[int | None] = mapped_column(Integer)
    class_name: Mapped[str | None] = mapped_column(Text)
    enrollment_status: Mapped[str | None] = mapped_column(Text)

    inbound_start_date: Mapped[date | None] = mapped_column(Date)
    inbound_end_date: Mapped[date | None] = mapped_column(Date)

    prefilled_base_qty: Mapped[Decimal | None] = mapped_column(AMOUNT_NUMERIC)
    prefilled_base_revenue: Mapped[Decimal | None] = mapped_column(AMOUNT_NUMERIC)
    prefilled_stretch_qty: Mapped[Decimal | None] = mapped_column(AMOUNT_NUMERIC)
    prefilled_stretch_revenue: Mapped[Decimal | None] = mapped_column(AMOUNT_NUMERIC)

    raw_data: Mapped[dict[str, Any] | None] = mapped_column(JSON_TYPE)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=CURRENT_TIMESTAMP_DEFAULT, nullable=False)


class MonthlyTargetRow(Base):
    __tablename__ = "monthly_target_rows"
    __table_args__ = table_args(Index("idx_target_period_seq", "period_id", "upload_seq"), schema="source")

    id: Mapped[int] = mapped_column(BIGINT_TYPE, primary_key=True, autoincrement=True)
    table_instance_id: Mapped[int] = mapped_column(BIGINT_TYPE, ForeignKey(fk("meta.upload_table_instances.table_instance_id")), nullable=False)
    period_id: Mapped[int] = mapped_column(BIGINT_TYPE, ForeignKey(fk("meta.periods.period_id")), nullable=False)
    upload_seq: Mapped[int] = mapped_column(Integer, nullable=False)
    row_no: Mapped[int | None] = mapped_column(Integer)

    target_level: Mapped[str | None] = mapped_column(Text)
    area_name: Mapped[str | None] = mapped_column(Text)
    province_name: Mapped[str | None] = mapped_column(Text)
    city_name: Mapped[str | None] = mapped_column(Text)
    bd_name: Mapped[str | None] = mapped_column(Text)
    target_revenue: Mapped[Decimal | None] = mapped_column(AMOUNT_NUMERIC)

    raw_data: Mapped[dict[str, Any] | None] = mapped_column(JSON_TYPE)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=CURRENT_TIMESTAMP_DEFAULT, nullable=False)


class InboundRow(Base):
    __tablename__ = "inbound_rows"
    __table_args__ = table_args(Index("idx_inbound_period_seq", "period_id", "upload_seq"), schema="source")

    id: Mapped[int] = mapped_column(BIGINT_TYPE, primary_key=True, autoincrement=True)
    table_instance_id: Mapped[int] = mapped_column(BIGINT_TYPE, ForeignKey(fk("meta.upload_table_instances.table_instance_id")), nullable=False)
    period_id: Mapped[int] = mapped_column(BIGINT_TYPE, ForeignKey(fk("meta.periods.period_id")), nullable=False)
    upload_seq: Mapped[int] = mapped_column(Integer, nullable=False)
    row_no: Mapped[int | None] = mapped_column(Integer)

    course_line: Mapped[str | None] = mapped_column(Text)
    area_name: Mapped[str | None] = mapped_column(Text)
    province_name: Mapped[str | None] = mapped_column(Text)
    city_name: Mapped[str | None] = mapped_column(Text)
    district_name: Mapped[str | None] = mapped_column(Text)
    bd_name: Mapped[str | None] = mapped_column(Text)
    acquisition_type: Mapped[str | None] = mapped_column(Text)

    inbound_date: Mapped[date | None] = mapped_column(Date)
    inbound_qty: Mapped[Decimal | None] = mapped_column(AMOUNT_NUMERIC)
    achieved_revenue: Mapped[Decimal | None] = mapped_column(AMOUNT_NUMERIC)

    raw_data: Mapped[dict[str, Any] | None] = mapped_column(JSON_TYPE)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=CURRENT_TIMESTAMP_DEFAULT, nullable=False)
