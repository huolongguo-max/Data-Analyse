"""add uploaded files and align sheet constraints

Revision ID: 20260611_0002
Revises: 20260609_0001
Create Date: 2026-06-11 21:30:00
"""

from typing import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260611_0002"
down_revision: str | None = "20260609_0001"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "uploaded_files",
        sa.Column("file_id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("batch_id", sa.BigInteger(), sa.ForeignKey("meta.upload_batches.batch_id"), nullable=False),
        sa.Column("period_id", sa.BigInteger(), sa.ForeignKey("meta.periods.period_id"), nullable=False),
        sa.Column("upload_seq", sa.Integer(), nullable=False),
        sa.Column("file_role", sa.Text(), nullable=False),
        sa.Column("original_filename", sa.Text(), nullable=False),
        sa.Column("stored_filename", sa.Text(), nullable=False),
        sa.Column("file_path", sa.Text(), nullable=False),
        sa.Column("file_sha256", sa.Text(), nullable=False),
        sa.Column("file_size_bytes", sa.BigInteger(), nullable=False),
        sa.Column("content_type", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint(
            "file_role IN ('original_workbook', 'completed_workbook')",
            name="ck_uploaded_files_role",
        ),
        sa.UniqueConstraint("batch_id", "file_role", name="uq_uploaded_files_batch_role"),
        schema="meta",
    )
    op.create_index(
        "idx_uploaded_files_period_seq_role",
        "uploaded_files",
        ["period_id", "upload_seq", "file_role"],
        unique=False,
        schema="meta",
    )
    op.create_index(
        "idx_uploaded_files_sha256",
        "uploaded_files",
        ["file_sha256"],
        unique=False,
        schema="meta",
    )

    op.drop_constraint("ck_table_instances_sheet_name", "upload_table_instances", schema="meta", type_="check")
    op.drop_constraint("ck_table_instances_sheet_type_match", "upload_table_instances", schema="meta", type_="check")
    op.create_check_constraint(
        "ck_table_instances_sheet_name",
        "upload_table_instances",
        "sheet_name IN ('储备明细表', '每月班期表', '每月目标表', '已进线表')",
        schema="meta",
    )
    op.create_check_constraint(
        "ck_table_instances_sheet_type_match",
        "upload_table_instances",
        "((sheet_name = '储备明细表' AND table_type = 'reserve_detail') "
        "OR (sheet_name = '每月班期表' AND table_type = 'monthly_class') "
        "OR (sheet_name IN ('每月目标表', '已进线表') AND table_type = 'monthly_target') "
        "OR (sheet_name = '已进线表' AND table_type = 'inbound'))",
        schema="meta",
    )


def downgrade() -> None:
    op.drop_constraint("ck_table_instances_sheet_type_match", "upload_table_instances", schema="meta", type_="check")
    op.drop_constraint("ck_table_instances_sheet_name", "upload_table_instances", schema="meta", type_="check")
    op.create_check_constraint(
        "ck_table_instances_sheet_name",
        "upload_table_instances",
        "sheet_name IN ('鍌ㄥ鏄庣粏琛?, '姣忔湀鐝湡琛?, '姣忔湀鐩爣琛?, '宸茶繘绾胯〃')",
        schema="meta",
    )
    op.create_check_constraint(
        "ck_table_instances_sheet_type_match",
        "upload_table_instances",
        "((sheet_name = '鍌ㄥ鏄庣粏琛? AND table_type = 'reserve_detail') "
        "OR (sheet_name = '姣忔湀鐝湡琛? AND table_type = 'monthly_class') "
        "OR (sheet_name = '姣忔湀鐩爣琛? AND table_type = 'monthly_target') "
        "OR (sheet_name = '宸茶繘绾胯〃' AND table_type = 'inbound'))",
        schema="meta",
    )

    op.drop_index("idx_uploaded_files_sha256", table_name="uploaded_files", schema="meta")
    op.drop_index("idx_uploaded_files_period_seq_role", table_name="uploaded_files", schema="meta")
    op.drop_table("uploaded_files", schema="meta")
