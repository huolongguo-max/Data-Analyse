from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Index, Integer, Numeric, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.db_compat import BIGINT_TYPE, CURRENT_TIMESTAMP_DEFAULT, fk, table_args


AMOUNT_NUMERIC = Numeric(18, 6)


class MonthlySnapshotMetric(Base):
    __tablename__ = "monthly_snapshot_metrics"
    __table_args__ = table_args(
        UniqueConstraint(
            "period_id",
            "upload_seq",
            "dimension_level",
            "dimension_key",
            name="uq_fact_period_seq_level_key",
        ),
        Index("idx_fact_period_seq_level", "period_id", "upload_seq", "dimension_level"),
        Index("idx_fact_compare", "period_id", "dimension_level", "dimension_key", "upload_seq"),
        schema="fact",
    )

    metric_id: Mapped[int] = mapped_column(BIGINT_TYPE, primary_key=True, autoincrement=True)
    period_id: Mapped[int] = mapped_column(BIGINT_TYPE, ForeignKey(fk("meta.periods.period_id")), nullable=False)
    upload_seq: Mapped[int] = mapped_column(Integer, nullable=False)

    dimension_level: Mapped[str] = mapped_column(Text, nullable=False)
    dimension_key: Mapped[str] = mapped_column(Text, nullable=False)
    dimension_name: Mapped[str] = mapped_column(Text, nullable=False)

    course_line: Mapped[str | None] = mapped_column(Text)
    class_key: Mapped[str | None] = mapped_column(Text)
    class_name: Mapped[str | None] = mapped_column(Text)
    area_name: Mapped[str | None] = mapped_column(Text)
    province_name: Mapped[str | None] = mapped_column(Text)
    city_name: Mapped[str | None] = mapped_column(Text)
    bd_name: Mapped[str | None] = mapped_column(Text)
    acquisition_type: Mapped[str | None] = mapped_column(Text)
    project_reliability: Mapped[str | None] = mapped_column(Text)

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

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=CURRENT_TIMESTAMP_DEFAULT, nullable=False)
