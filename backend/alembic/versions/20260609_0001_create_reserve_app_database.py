"""create reserve app database

Revision ID: 20260609_0001
Revises:
Create Date: 2026-06-09 20:40:00
"""

from typing import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "20260609_0001"
down_revision: str | None = None
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS meta")
    op.execute("CREATE SCHEMA IF NOT EXISTS source")
    op.execute("CREATE SCHEMA IF NOT EXISTS base")
    op.execute("CREATE SCHEMA IF NOT EXISTS fact")

    op.create_table(
        "periods",
        sa.Column("period_id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("period_code", sa.Text(), nullable=False),
        sa.Column("period_month", sa.Date(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("period_code", name="uq_periods_period_code"),
        schema="meta",
    )

    op.create_table(
        "upload_batches",
        sa.Column("batch_id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("period_id", sa.BigInteger(), sa.ForeignKey("meta.periods.period_id"), nullable=False),
        sa.Column("upload_seq", sa.Integer(), nullable=False),
        sa.Column("source_period_year", sa.Integer()),
        sa.Column("source_period_month", sa.Integer()),
        sa.Column("source_record_mmdd", sa.Text()),
        sa.Column("uploaded_by", sa.Text()),
        sa.Column("uploaded_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("status", sa.Text(), server_default=sa.text("'uploaded'"), nullable=False),
        sa.Column("message", sa.Text()),
        sa.CheckConstraint(
            "source_period_year IS NULL OR (source_period_year >= 1000 AND source_period_year <= 9999)",
            name="ck_upload_batches_source_period_year",
        ),
        sa.CheckConstraint(
            "source_period_month IS NULL OR (source_period_month >= 1 AND source_period_month <= 12)",
            name="ck_upload_batches_source_period_month",
        ),
        sa.CheckConstraint(
            "source_record_mmdd IS NULL OR source_record_mmdd ~ '^[0-9]{4}$'",
            name="ck_upload_batches_source_record_mmdd",
        ),
        sa.UniqueConstraint("period_id", "upload_seq", name="uq_upload_batches_period_seq"),
        schema="meta",
    )

    op.create_table(
        "upload_table_instances",
        sa.Column("table_instance_id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("batch_id", sa.BigInteger(), sa.ForeignKey("meta.upload_batches.batch_id"), nullable=False),
        sa.Column("period_id", sa.BigInteger(), sa.ForeignKey("meta.periods.period_id"), nullable=False),
        sa.Column("upload_seq", sa.Integer(), nullable=False),
        sa.Column("table_type", sa.Text(), nullable=False),
        sa.Column("sheet_name", sa.Text(), nullable=False),
        sa.Column("original_filename", sa.Text()),
        sa.Column("file_path", sa.Text()),
        sa.Column("file_sha256", sa.Text()),
        sa.Column("row_count", sa.Integer()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint(
            "table_type IN ('reserve_detail', 'monthly_class', 'monthly_target', 'inbound')",
            name="ck_table_instances_type",
        ),
        sa.CheckConstraint(
            "sheet_name IN ('储备明细表', '每月班期表', '每月目标表', '已进线表')",
            name="ck_table_instances_sheet_name",
        ),
        sa.CheckConstraint(
            "((sheet_name = '储备明细表' AND table_type = 'reserve_detail') "
            "OR (sheet_name = '每月班期表' AND table_type = 'monthly_class') "
            "OR (sheet_name = '每月目标表' AND table_type = 'monthly_target') "
            "OR (sheet_name = '已进线表' AND table_type = 'inbound'))",
            name="ck_table_instances_sheet_type_match",
        ),
        sa.UniqueConstraint("period_id", "upload_seq", "table_type", name="uq_table_instances_period_seq_type"),
        schema="meta",
    )

    op.create_table(
        "reserve_detail_rows",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("table_instance_id", sa.BigInteger(), sa.ForeignKey("meta.upload_table_instances.table_instance_id"), nullable=False),
        sa.Column("period_id", sa.BigInteger(), sa.ForeignKey("meta.periods.period_id"), nullable=False),
        sa.Column("upload_seq", sa.Integer(), nullable=False),
        sa.Column("row_no", sa.Integer()),
        sa.Column("course_line", sa.Text()),
        sa.Column("area_name", sa.Text()),
        sa.Column("province_name", sa.Text()),
        sa.Column("city_name", sa.Text()),
        sa.Column("district_name", sa.Text()),
        sa.Column("bd_name", sa.Text()),
        sa.Column("acquisition_type", sa.Text()),
        sa.Column("project_reliability", sa.Text()),
        sa.Column("project_name", sa.Text()),
        sa.Column("school_name", sa.Text()),
        sa.Column("start_date", sa.Date()),
        sa.Column("end_date", sa.Date()),
        sa.Column("next_week_start_date", sa.Date()),
        sa.Column("next_week_end_date", sa.Date()),
        sa.Column("base_reserve_qty", sa.Numeric(18, 2)),
        sa.Column("base_forecast_revenue", sa.Numeric(18, 2)),
        sa.Column("stretch_reserve_qty", sa.Numeric(18, 2)),
        sa.Column("stretch_forecast_revenue", sa.Numeric(18, 2)),
        sa.Column("next_week_base_reserve_qty", sa.Numeric(18, 2)),
        sa.Column("next_week_base_forecast_revenue", sa.Numeric(18, 2)),
        sa.Column("next_week_stretch_reserve_qty", sa.Numeric(18, 2)),
        sa.Column("next_week_stretch_forecast_revenue", sa.Numeric(18, 2)),
        sa.Column("raw_data", postgresql.JSONB(astext_type=sa.Text())),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        schema="source",
    )

    op.create_table(
        "monthly_class_rows",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("table_instance_id", sa.BigInteger(), sa.ForeignKey("meta.upload_table_instances.table_instance_id"), nullable=False),
        sa.Column("period_id", sa.BigInteger(), sa.ForeignKey("meta.periods.period_id"), nullable=False),
        sa.Column("upload_seq", sa.Integer(), nullable=False),
        sa.Column("row_no", sa.Integer()),
        sa.Column("course_line", sa.Text()),
        sa.Column("class_key", sa.Text()),
        sa.Column("class_seq", sa.Integer()),
        sa.Column("class_name", sa.Text()),
        sa.Column("enrollment_status", sa.Text()),
        sa.Column("inbound_start_date", sa.Date()),
        sa.Column("inbound_end_date", sa.Date()),
        sa.Column("prefilled_base_qty", sa.Numeric(18, 2)),
        sa.Column("prefilled_base_revenue", sa.Numeric(18, 2)),
        sa.Column("prefilled_stretch_qty", sa.Numeric(18, 2)),
        sa.Column("prefilled_stretch_revenue", sa.Numeric(18, 2)),
        sa.Column("raw_data", postgresql.JSONB(astext_type=sa.Text())),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        schema="source",
    )

    op.create_table(
        "monthly_target_rows",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("table_instance_id", sa.BigInteger(), sa.ForeignKey("meta.upload_table_instances.table_instance_id"), nullable=False),
        sa.Column("period_id", sa.BigInteger(), sa.ForeignKey("meta.periods.period_id"), nullable=False),
        sa.Column("upload_seq", sa.Integer(), nullable=False),
        sa.Column("row_no", sa.Integer()),
        sa.Column("target_level", sa.Text()),
        sa.Column("area_name", sa.Text()),
        sa.Column("province_name", sa.Text()),
        sa.Column("city_name", sa.Text()),
        sa.Column("bd_name", sa.Text()),
        sa.Column("target_revenue", sa.Numeric(18, 2)),
        sa.Column("raw_data", postgresql.JSONB(astext_type=sa.Text())),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        schema="source",
    )

    op.create_table(
        "inbound_rows",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("table_instance_id", sa.BigInteger(), sa.ForeignKey("meta.upload_table_instances.table_instance_id"), nullable=False),
        sa.Column("period_id", sa.BigInteger(), sa.ForeignKey("meta.periods.period_id"), nullable=False),
        sa.Column("upload_seq", sa.Integer(), nullable=False),
        sa.Column("row_no", sa.Integer()),
        sa.Column("course_line", sa.Text()),
        sa.Column("area_name", sa.Text()),
        sa.Column("province_name", sa.Text()),
        sa.Column("city_name", sa.Text()),
        sa.Column("district_name", sa.Text()),
        sa.Column("bd_name", sa.Text()),
        sa.Column("acquisition_type", sa.Text()),
        sa.Column("inbound_date", sa.Date()),
        sa.Column("inbound_qty", sa.Numeric(18, 2)),
        sa.Column("achieved_revenue", sa.Numeric(18, 2)),
        sa.Column("raw_data", postgresql.JSONB(astext_type=sa.Text())),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        schema="source",
    )

    op.create_table(
        "period_class_schedule",
        sa.Column("schedule_id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("period_id", sa.BigInteger(), sa.ForeignKey("meta.periods.period_id"), nullable=False),
        sa.Column("course_line", sa.Text(), nullable=False),
        sa.Column("class_key", sa.Text(), nullable=False),
        sa.Column("class_seq", sa.Integer()),
        sa.Column("class_name", sa.Text()),
        sa.Column("inbound_start_date", sa.Date(), nullable=False),
        sa.Column("inbound_end_date", sa.Date(), nullable=False),
        sa.Column("source_table_instance_id", sa.BigInteger(), sa.ForeignKey("meta.upload_table_instances.table_instance_id")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("period_id", "course_line", "class_key", name="uq_schedule_period_course_class"),
        schema="base",
    )

    op.create_table(
        "reserve_detail_completed",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("period_id", sa.BigInteger(), sa.ForeignKey("meta.periods.period_id"), nullable=False),
        sa.Column("upload_seq", sa.Integer(), nullable=False),
        sa.Column("source_row_id", sa.BigInteger(), sa.ForeignKey("source.reserve_detail_rows.id")),
        sa.Column("course_line", sa.Text()),
        sa.Column("area_name", sa.Text()),
        sa.Column("province_name", sa.Text()),
        sa.Column("city_name", sa.Text()),
        sa.Column("district_name", sa.Text()),
        sa.Column("bd_name", sa.Text()),
        sa.Column("acquisition_type", sa.Text()),
        sa.Column("project_reliability", sa.Text()),
        sa.Column("project_name", sa.Text()),
        sa.Column("school_name", sa.Text()),
        sa.Column("start_date", sa.Date()),
        sa.Column("end_date", sa.Date()),
        sa.Column("next_week_start_date", sa.Date()),
        sa.Column("next_week_end_date", sa.Date()),
        sa.Column("base_reserve_qty", sa.Numeric(18, 2)),
        sa.Column("base_forecast_revenue", sa.Numeric(18, 2)),
        sa.Column("stretch_reserve_qty", sa.Numeric(18, 2)),
        sa.Column("stretch_forecast_revenue", sa.Numeric(18, 2)),
        sa.Column("next_week_base_reserve_qty", sa.Numeric(18, 2)),
        sa.Column("next_week_base_forecast_revenue", sa.Numeric(18, 2)),
        sa.Column("next_week_stretch_reserve_qty", sa.Numeric(18, 2)),
        sa.Column("next_week_stretch_forecast_revenue", sa.Numeric(18, 2)),
        sa.Column("customer_days", sa.Integer()),
        sa.Column("next_week_customer_days", sa.Integer()),
        sa.Column("base_reserve_daily_next_week", sa.Numeric(18, 6)),
        sa.Column("base_reserve_daily_other", sa.Numeric(18, 6)),
        sa.Column("base_revenue_daily_next_week", sa.Numeric(18, 6)),
        sa.Column("base_revenue_daily_other", sa.Numeric(18, 6)),
        sa.Column("stretch_reserve_daily_next_week", sa.Numeric(18, 6)),
        sa.Column("stretch_reserve_daily_other", sa.Numeric(18, 6)),
        sa.Column("stretch_revenue_daily_next_week", sa.Numeric(18, 6)),
        sa.Column("stretch_revenue_daily_other", sa.Numeric(18, 6)),
        sa.Column("validation_status", sa.Text()),
        sa.Column("validation_message", sa.Text()),
        sa.Column("raw_data", postgresql.JSONB(astext_type=sa.Text())),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        schema="base",
    )

    op.create_table(
        "monthly_class_completed",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("period_id", sa.BigInteger(), sa.ForeignKey("meta.periods.period_id"), nullable=False),
        sa.Column("upload_seq", sa.Integer(), nullable=False),
        sa.Column("source_row_id", sa.BigInteger(), sa.ForeignKey("source.monthly_class_rows.id")),
        sa.Column("schedule_id", sa.BigInteger(), sa.ForeignKey("base.period_class_schedule.schedule_id")),
        sa.Column("course_line", sa.Text()),
        sa.Column("class_key", sa.Text()),
        sa.Column("class_seq", sa.Integer()),
        sa.Column("class_name", sa.Text()),
        sa.Column("enrollment_status", sa.Text()),
        sa.Column("inbound_start_date", sa.Date()),
        sa.Column("inbound_end_date", sa.Date()),
        sa.Column("prefilled_base_qty", sa.Numeric(18, 2)),
        sa.Column("prefilled_base_revenue", sa.Numeric(18, 2)),
        sa.Column("prefilled_stretch_qty", sa.Numeric(18, 2)),
        sa.Column("prefilled_stretch_revenue", sa.Numeric(18, 2)),
        sa.Column("calc_base_reserve_qty", sa.Numeric(18, 2)),
        sa.Column("calc_base_forecast_revenue", sa.Numeric(18, 2)),
        sa.Column("calc_stretch_reserve_qty", sa.Numeric(18, 2)),
        sa.Column("calc_stretch_forecast_revenue", sa.Numeric(18, 2)),
        sa.Column("final_base_reserve_qty", sa.Numeric(18, 2)),
        sa.Column("final_base_forecast_revenue", sa.Numeric(18, 2)),
        sa.Column("final_stretch_reserve_qty", sa.Numeric(18, 2)),
        sa.Column("final_stretch_forecast_revenue", sa.Numeric(18, 2)),
        sa.Column("calc_rule", sa.Text()),
        sa.Column("validation_status", sa.Text()),
        sa.Column("validation_message", sa.Text()),
        sa.Column("raw_data", postgresql.JSONB(astext_type=sa.Text())),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        schema="base",
    )

    op.create_table(
        "monthly_target_completed",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("period_id", sa.BigInteger(), sa.ForeignKey("meta.periods.period_id"), nullable=False),
        sa.Column("upload_seq", sa.Integer(), nullable=False),
        sa.Column("source_row_id", sa.BigInteger(), sa.ForeignKey("source.monthly_target_rows.id")),
        sa.Column("target_level", sa.Text()),
        sa.Column("area_name", sa.Text()),
        sa.Column("province_name", sa.Text()),
        sa.Column("city_name", sa.Text()),
        sa.Column("bd_name", sa.Text()),
        sa.Column("target_revenue", sa.Numeric(18, 2)),
        sa.Column("inbound_qty", sa.Numeric(18, 2)),
        sa.Column("achieved_revenue", sa.Numeric(18, 2)),
        sa.Column("base_reserve_qty", sa.Numeric(18, 2)),
        sa.Column("base_forecast_revenue", sa.Numeric(18, 2)),
        sa.Column("base_total_reserve_qty", sa.Numeric(18, 2)),
        sa.Column("base_total_revenue", sa.Numeric(18, 2)),
        sa.Column("base_achievement_rate", sa.Numeric(18, 6)),
        sa.Column("stretch_reserve_qty", sa.Numeric(18, 2)),
        sa.Column("stretch_forecast_revenue", sa.Numeric(18, 2)),
        sa.Column("stretch_total_reserve_qty", sa.Numeric(18, 2)),
        sa.Column("stretch_total_revenue", sa.Numeric(18, 2)),
        sa.Column("stretch_achievement_rate", sa.Numeric(18, 6)),
        sa.Column("validation_status", sa.Text()),
        sa.Column("validation_message", sa.Text()),
        sa.Column("raw_data", postgresql.JSONB(astext_type=sa.Text())),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        schema="base",
    )

    op.create_table(
        "inbound_completed",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("period_id", sa.BigInteger(), sa.ForeignKey("meta.periods.period_id"), nullable=False),
        sa.Column("upload_seq", sa.Integer(), nullable=False),
        sa.Column("source_row_id", sa.BigInteger(), sa.ForeignKey("source.inbound_rows.id")),
        sa.Column("course_line", sa.Text()),
        sa.Column("area_name", sa.Text()),
        sa.Column("province_name", sa.Text()),
        sa.Column("city_name", sa.Text()),
        sa.Column("district_name", sa.Text()),
        sa.Column("bd_name", sa.Text()),
        sa.Column("acquisition_type", sa.Text()),
        sa.Column("inbound_date", sa.Date()),
        sa.Column("inbound_qty", sa.Numeric(18, 2)),
        sa.Column("achieved_revenue", sa.Numeric(18, 2)),
        sa.Column("matched_schedule_id", sa.BigInteger(), sa.ForeignKey("base.period_class_schedule.schedule_id")),
        sa.Column("matched_class_key", sa.Text()),
        sa.Column("matched_class_seq", sa.Integer()),
        sa.Column("matched_class_name", sa.Text()),
        sa.Column("is_in_class_period", sa.Boolean()),
        sa.Column("final_inbound_qty", sa.Numeric(18, 2)),
        sa.Column("final_achieved_revenue", sa.Numeric(18, 2)),
        sa.Column("validation_status", sa.Text()),
        sa.Column("validation_message", sa.Text()),
        sa.Column("raw_data", postgresql.JSONB(astext_type=sa.Text())),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        schema="base",
    )

    op.create_table(
        "monthly_snapshot_metrics",
        sa.Column("metric_id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("period_id", sa.BigInteger(), sa.ForeignKey("meta.periods.period_id"), nullable=False),
        sa.Column("upload_seq", sa.Integer(), nullable=False),
        sa.Column("dimension_level", sa.Text(), nullable=False),
        sa.Column("dimension_key", sa.Text(), nullable=False),
        sa.Column("dimension_name", sa.Text(), nullable=False),
        sa.Column("course_line", sa.Text()),
        sa.Column("class_key", sa.Text()),
        sa.Column("class_name", sa.Text()),
        sa.Column("area_name", sa.Text()),
        sa.Column("province_name", sa.Text()),
        sa.Column("city_name", sa.Text()),
        sa.Column("bd_name", sa.Text()),
        sa.Column("acquisition_type", sa.Text()),
        sa.Column("project_reliability", sa.Text()),
        sa.Column("target_revenue", sa.Numeric(18, 2)),
        sa.Column("inbound_qty", sa.Numeric(18, 2)),
        sa.Column("achieved_revenue", sa.Numeric(18, 2)),
        sa.Column("base_reserve_qty", sa.Numeric(18, 2)),
        sa.Column("base_forecast_revenue", sa.Numeric(18, 2)),
        sa.Column("base_total_reserve_qty", sa.Numeric(18, 2)),
        sa.Column("base_total_revenue", sa.Numeric(18, 2)),
        sa.Column("base_achievement_rate", sa.Numeric(18, 6)),
        sa.Column("stretch_reserve_qty", sa.Numeric(18, 2)),
        sa.Column("stretch_forecast_revenue", sa.Numeric(18, 2)),
        sa.Column("stretch_total_reserve_qty", sa.Numeric(18, 2)),
        sa.Column("stretch_total_revenue", sa.Numeric(18, 2)),
        sa.Column("stretch_achievement_rate", sa.Numeric(18, 6)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint(
            "period_id",
            "upload_seq",
            "dimension_level",
            "dimension_key",
            name="uq_fact_period_seq_level_key",
        ),
        schema="fact",
    )

    op.create_index("idx_upload_batches_period_seq", "upload_batches", ["period_id", "upload_seq"], schema="meta")
    op.create_index(
        "idx_table_instances_period_seq_type",
        "upload_table_instances",
        ["period_id", "upload_seq", "table_type"],
        schema="meta",
    )
    op.create_index("idx_reserve_period_seq", "reserve_detail_rows", ["period_id", "upload_seq"], schema="source")
    op.create_index("idx_class_period_seq", "monthly_class_rows", ["period_id", "upload_seq"], schema="source")
    op.create_index("idx_target_period_seq", "monthly_target_rows", ["period_id", "upload_seq"], schema="source")
    op.create_index("idx_inbound_period_seq", "inbound_rows", ["period_id", "upload_seq"], schema="source")
    op.create_index("idx_schedule_period_course", "period_class_schedule", ["period_id", "course_line"], schema="base")
    op.create_index(
        "idx_fact_period_seq_level",
        "monthly_snapshot_metrics",
        ["period_id", "upload_seq", "dimension_level"],
        schema="fact",
    )
    op.create_index(
        "idx_fact_compare",
        "monthly_snapshot_metrics",
        ["period_id", "dimension_level", "dimension_key", "upload_seq"],
        schema="fact",
    )


def downgrade() -> None:
    op.drop_index("idx_fact_compare", table_name="monthly_snapshot_metrics", schema="fact")
    op.drop_index("idx_fact_period_seq_level", table_name="monthly_snapshot_metrics", schema="fact")
    op.drop_index("idx_schedule_period_course", table_name="period_class_schedule", schema="base")
    op.drop_index("idx_inbound_period_seq", table_name="inbound_rows", schema="source")
    op.drop_index("idx_target_period_seq", table_name="monthly_target_rows", schema="source")
    op.drop_index("idx_class_period_seq", table_name="monthly_class_rows", schema="source")
    op.drop_index("idx_reserve_period_seq", table_name="reserve_detail_rows", schema="source")
    op.drop_index("idx_table_instances_period_seq_type", table_name="upload_table_instances", schema="meta")
    op.drop_index("idx_upload_batches_period_seq", table_name="upload_batches", schema="meta")

    op.drop_table("monthly_snapshot_metrics", schema="fact")
    op.drop_table("inbound_completed", schema="base")
    op.drop_table("monthly_target_completed", schema="base")
    op.drop_table("monthly_class_completed", schema="base")
    op.drop_table("reserve_detail_completed", schema="base")
    op.drop_table("period_class_schedule", schema="base")
    op.drop_table("inbound_rows", schema="source")
    op.drop_table("monthly_target_rows", schema="source")
    op.drop_table("monthly_class_rows", schema="source")
    op.drop_table("reserve_detail_rows", schema="source")
    op.drop_table("upload_table_instances", schema="meta")
    op.drop_table("upload_batches", schema="meta")
    op.drop_table("periods", schema="meta")

    op.execute("DROP SCHEMA IF EXISTS fact")
    op.execute("DROP SCHEMA IF EXISTS base")
    op.execute("DROP SCHEMA IF EXISTS source")
    op.execute("DROP SCHEMA IF EXISTS meta")
