"""increase metric precision for raw storage

Revision ID: 20260612_0003
Revises: 20260611_0002
Create Date: 2026-06-12 12:10:00
"""

from typing import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260612_0003"
down_revision: str | None = "20260611_0002"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


AMOUNT_COLUMNS: dict[tuple[str, str], list[str]] = {
    ("source", "reserve_detail_rows"): [
        "base_reserve_qty",
        "base_forecast_revenue",
        "stretch_reserve_qty",
        "stretch_forecast_revenue",
        "next_week_base_reserve_qty",
        "next_week_base_forecast_revenue",
        "next_week_stretch_reserve_qty",
        "next_week_stretch_forecast_revenue",
    ],
    ("source", "monthly_class_rows"): [
        "prefilled_base_qty",
        "prefilled_base_revenue",
        "prefilled_stretch_qty",
        "prefilled_stretch_revenue",
    ],
    ("source", "monthly_target_rows"): [
        "target_revenue",
    ],
    ("source", "inbound_rows"): [
        "inbound_qty",
        "achieved_revenue",
    ],
    ("base", "reserve_detail_completed"): [
        "base_reserve_qty",
        "base_forecast_revenue",
        "stretch_reserve_qty",
        "stretch_forecast_revenue",
        "next_week_base_reserve_qty",
        "next_week_base_forecast_revenue",
        "next_week_stretch_reserve_qty",
        "next_week_stretch_forecast_revenue",
    ],
    ("base", "monthly_class_completed"): [
        "prefilled_base_qty",
        "prefilled_base_revenue",
        "prefilled_stretch_qty",
        "prefilled_stretch_revenue",
        "calc_base_reserve_qty",
        "calc_base_forecast_revenue",
        "calc_stretch_reserve_qty",
        "calc_stretch_forecast_revenue",
        "final_base_reserve_qty",
        "final_base_forecast_revenue",
        "final_stretch_reserve_qty",
        "final_stretch_forecast_revenue",
    ],
    ("base", "monthly_target_completed"): [
        "target_revenue",
        "inbound_qty",
        "achieved_revenue",
        "base_reserve_qty",
        "base_forecast_revenue",
        "base_total_reserve_qty",
        "base_total_revenue",
        "stretch_reserve_qty",
        "stretch_forecast_revenue",
        "stretch_total_reserve_qty",
        "stretch_total_revenue",
    ],
    ("base", "inbound_completed"): [
        "inbound_qty",
        "achieved_revenue",
        "final_inbound_qty",
        "final_achieved_revenue",
    ],
    ("fact", "monthly_snapshot_metrics"): [
        "target_revenue",
        "inbound_qty",
        "achieved_revenue",
        "base_reserve_qty",
        "base_forecast_revenue",
        "base_total_reserve_qty",
        "base_total_revenue",
        "stretch_reserve_qty",
        "stretch_forecast_revenue",
        "stretch_total_reserve_qty",
        "stretch_total_revenue",
    ],
}


def _alter_metric_precision(*, new_scale: int, old_scale: int) -> None:
    for (schema_name, table_name), columns in AMOUNT_COLUMNS.items():
        for column_name in columns:
            op.alter_column(
                table_name,
                column_name,
                schema=schema_name,
                existing_type=sa.Numeric(18, old_scale),
                type_=sa.Numeric(18, new_scale),
                existing_nullable=True,
            )


def upgrade() -> None:
    _alter_metric_precision(new_scale=6, old_scale=2)


def downgrade() -> None:
    _alter_metric_precision(new_scale=2, old_scale=6)
