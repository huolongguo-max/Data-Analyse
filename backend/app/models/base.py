from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Index, Integer, Numeric, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.db_compat import BIGINT_TYPE, CURRENT_TIMESTAMP_DEFAULT, JSON_TYPE, fk, table_args, table_kwargs


AMOUNT_NUMERIC = Numeric(18, 6)


class PeriodClassSchedule(Base):
    __tablename__ = "period_class_schedule"
    __table_args__ = table_args(
        UniqueConstraint("period_id", "course_line", "class_key", name="uq_schedule_period_course_class"),
        Index("idx_schedule_period_course", "period_id", "course_line"),
        schema="base",
    )

    schedule_id: Mapped[int] = mapped_column(BIGINT_TYPE, primary_key=True, autoincrement=True)
    period_id: Mapped[int] = mapped_column(BIGINT_TYPE, ForeignKey(fk("meta.periods.period_id")), nullable=False)

    course_line: Mapped[str] = mapped_column(Text, nullable=False)
    class_key: Mapped[str] = mapped_column(Text, nullable=False)
    class_seq: Mapped[int | None] = mapped_column(Integer)
    class_name: Mapped[str | None] = mapped_column(Text)

    inbound_start_date: Mapped[date] = mapped_column(Date, nullable=False)
    inbound_end_date: Mapped[date] = mapped_column(Date, nullable=False)

    source_table_instance_id: Mapped[int | None] = mapped_column(BIGINT_TYPE, ForeignKey(fk("meta.upload_table_instances.table_instance_id")))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=CURRENT_TIMESTAMP_DEFAULT, nullable=False)


class ReserveDetailCompleted(Base):
    __tablename__ = "reserve_detail_completed"
    __table_args__ = table_kwargs("base")

    id: Mapped[int] = mapped_column(BIGINT_TYPE, primary_key=True, autoincrement=True)
    period_id: Mapped[int] = mapped_column(BIGINT_TYPE, ForeignKey(fk("meta.periods.period_id")), nullable=False)
    upload_seq: Mapped[int] = mapped_column(Integer, nullable=False)
    source_row_id: Mapped[int | None] = mapped_column(BIGINT_TYPE, ForeignKey(fk("source.reserve_detail_rows.id")))

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

    customer_days: Mapped[int | None] = mapped_column(Integer)
    next_week_customer_days: Mapped[int | None] = mapped_column(Integer)

    base_reserve_daily_next_week: Mapped[Decimal | None] = mapped_column(Numeric(18, 6))
    base_reserve_daily_other: Mapped[Decimal | None] = mapped_column(Numeric(18, 6))
    base_revenue_daily_next_week: Mapped[Decimal | None] = mapped_column(Numeric(18, 6))
    base_revenue_daily_other: Mapped[Decimal | None] = mapped_column(Numeric(18, 6))

    stretch_reserve_daily_next_week: Mapped[Decimal | None] = mapped_column(Numeric(18, 6))
    stretch_reserve_daily_other: Mapped[Decimal | None] = mapped_column(Numeric(18, 6))
    stretch_revenue_daily_next_week: Mapped[Decimal | None] = mapped_column(Numeric(18, 6))
    stretch_revenue_daily_other: Mapped[Decimal | None] = mapped_column(Numeric(18, 6))

    validation_status: Mapped[str | None] = mapped_column(Text)
    validation_message: Mapped[str | None] = mapped_column(Text)
    raw_data: Mapped[dict[str, Any] | None] = mapped_column(JSON_TYPE)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=CURRENT_TIMESTAMP_DEFAULT, nullable=False)


class MonthlyClassCompleted(Base):
    __tablename__ = "monthly_class_completed"
    __table_args__ = table_kwargs("base")

    id: Mapped[int] = mapped_column(BIGINT_TYPE, primary_key=True, autoincrement=True)
    period_id: Mapped[int] = mapped_column(BIGINT_TYPE, ForeignKey(fk("meta.periods.period_id")), nullable=False)
    upload_seq: Mapped[int] = mapped_column(Integer, nullable=False)
    source_row_id: Mapped[int | None] = mapped_column(BIGINT_TYPE, ForeignKey(fk("source.monthly_class_rows.id")))
    schedule_id: Mapped[int | None] = mapped_column(BIGINT_TYPE, ForeignKey(fk("base.period_class_schedule.schedule_id")))

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

    calc_base_reserve_qty: Mapped[Decimal | None] = mapped_column(AMOUNT_NUMERIC)
    calc_base_forecast_revenue: Mapped[Decimal | None] = mapped_column(AMOUNT_NUMERIC)
    calc_stretch_reserve_qty: Mapped[Decimal | None] = mapped_column(AMOUNT_NUMERIC)
    calc_stretch_forecast_revenue: Mapped[Decimal | None] = mapped_column(AMOUNT_NUMERIC)

    final_base_reserve_qty: Mapped[Decimal | None] = mapped_column(AMOUNT_NUMERIC)
    final_base_forecast_revenue: Mapped[Decimal | None] = mapped_column(AMOUNT_NUMERIC)
    final_stretch_reserve_qty: Mapped[Decimal | None] = mapped_column(AMOUNT_NUMERIC)
    final_stretch_forecast_revenue: Mapped[Decimal | None] = mapped_column(AMOUNT_NUMERIC)

    calc_rule: Mapped[str | None] = mapped_column(Text)
    validation_status: Mapped[str | None] = mapped_column(Text)
    validation_message: Mapped[str | None] = mapped_column(Text)
    raw_data: Mapped[dict[str, Any] | None] = mapped_column(JSON_TYPE)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=CURRENT_TIMESTAMP_DEFAULT, nullable=False)


class MonthlyTargetCompleted(Base):
    __tablename__ = "monthly_target_completed"
    __table_args__ = table_kwargs("base")

    id: Mapped[int] = mapped_column(BIGINT_TYPE, primary_key=True, autoincrement=True)
    period_id: Mapped[int] = mapped_column(BIGINT_TYPE, ForeignKey(fk("meta.periods.period_id")), nullable=False)
    upload_seq: Mapped[int] = mapped_column(Integer, nullable=False)
    source_row_id: Mapped[int | None] = mapped_column(BIGINT_TYPE, ForeignKey(fk("source.monthly_target_rows.id")))

    target_level: Mapped[str | None] = mapped_column(Text)
    area_name: Mapped[str | None] = mapped_column(Text)
    province_name: Mapped[str | None] = mapped_column(Text)
    city_name: Mapped[str | None] = mapped_column(Text)
    bd_name: Mapped[str | None] = mapped_column(Text)
    target_revenue: Mapped[Decimal | None] = mapped_column(AMOUNT_NUMERIC)

    inbound_qty: Mapped[Decimal | None] = mapped_column(AMOUNT_NUMERIC)
    achieved_revenue: Mapped[Decimal | None] = mapped_column(AMOUNT_NUMERIC)

    base_reserve_qty: Mapped[Decimal | None] = mapped_column(AMOUNT_NUMERIC)
    base_forecast_revenue: Mapped[Decimal | None] = mapped_column(AMOUNT_NUMERIC)
    base_total_reserve_qty: Mapped[Decimal | None] = mapped_column(AMOUNT_NUMERIC)
    base_total_revenue: Mapped[Decimal | None] = mapped_column(AMOUNT_NUMERIC)
    base_achievement_rate: Mapped[Decimal | None] = mapped_column(Numeric(18, 6))

    stretch_reserve_qty: Mapped[Decimal | None] = mapped_column(AMOUNT_NUMERIC)
    stretch_forecast_revenue: Mapped[Decimal | None] = mapped_column(AMOUNT_NUMERIC)
    stretch_total_reserve_qty: Mapped[Decimal | None] = mapped_column(AMOUNT_NUMERIC)
    stretch_total_revenue: Mapped[Decimal | None] = mapped_column(AMOUNT_NUMERIC)
    stretch_achievement_rate: Mapped[Decimal | None] = mapped_column(Numeric(18, 6))

    validation_status: Mapped[str | None] = mapped_column(Text)
    validation_message: Mapped[str | None] = mapped_column(Text)
    raw_data: Mapped[dict[str, Any] | None] = mapped_column(JSON_TYPE)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=CURRENT_TIMESTAMP_DEFAULT, nullable=False)


class InboundCompleted(Base):
    __tablename__ = "inbound_completed"
    __table_args__ = table_kwargs("base")

    id: Mapped[int] = mapped_column(BIGINT_TYPE, primary_key=True, autoincrement=True)
    period_id: Mapped[int] = mapped_column(BIGINT_TYPE, ForeignKey(fk("meta.periods.period_id")), nullable=False)
    upload_seq: Mapped[int] = mapped_column(Integer, nullable=False)
    source_row_id: Mapped[int | None] = mapped_column(BIGINT_TYPE, ForeignKey(fk("source.inbound_rows.id")))

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

    matched_schedule_id: Mapped[int | None] = mapped_column(BIGINT_TYPE, ForeignKey(fk("base.period_class_schedule.schedule_id")))
    matched_class_key: Mapped[str | None] = mapped_column(Text)
    matched_class_seq: Mapped[int | None] = mapped_column(Integer)
    matched_class_name: Mapped[str | None] = mapped_column(Text)
    is_in_class_period: Mapped[bool | None] = mapped_column(Boolean)

    final_inbound_qty: Mapped[Decimal | None] = mapped_column(AMOUNT_NUMERIC)
    final_achieved_revenue: Mapped[Decimal | None] = mapped_column(AMOUNT_NUMERIC)

    validation_status: Mapped[str | None] = mapped_column(Text)
    validation_message: Mapped[str | None] = mapped_column(Text)
    raw_data: Mapped[dict[str, Any] | None] = mapped_column(JSON_TYPE)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=CURRENT_TIMESTAMP_DEFAULT, nullable=False)
