import sqlalchemy as sa

from app.database import Base
from app.db_compat import db_schema, qualified_table_name
from app.models import MonthlySnapshotMetric, Period, PeriodClassSchedule, UploadBatch, UploadTableInstance
from app.models.source import InboundRow, MonthlyClassRow, MonthlyTargetRow, ReserveDetailRow


EXPECTED_TABLES = {
    qualified_table_name("meta", "periods"),
    qualified_table_name("meta", "upload_batches"),
    qualified_table_name("meta", "uploaded_files"),
    qualified_table_name("meta", "upload_table_instances"),
    qualified_table_name("source", "reserve_detail_rows"),
    qualified_table_name("source", "monthly_class_rows"),
    qualified_table_name("source", "monthly_target_rows"),
    qualified_table_name("source", "inbound_rows"),
    qualified_table_name("base", "period_class_schedule"),
    qualified_table_name("base", "reserve_detail_completed"),
    qualified_table_name("base", "monthly_class_completed"),
    qualified_table_name("base", "monthly_target_completed"),
    qualified_table_name("base", "inbound_completed"),
    qualified_table_name("fact", "monthly_snapshot_metrics"),
}


def test_expected_tables_are_registered() -> None:
    assert EXPECTED_TABLES.issubset(Base.metadata.tables.keys())


def test_period_table_uses_meta_schema() -> None:
    assert Period.__table__.schema == db_schema("meta")
    constraint_names = {constraint.name for constraint in Period.__table__.constraints}
    assert "uq_periods_period_code" in constraint_names


def test_upload_batch_unique_constraint_matches_spec() -> None:
    constraint_names = {constraint.name for constraint in UploadBatch.__table__.constraints}
    assert "uq_upload_batches_period_seq" in constraint_names
    assert "ck_upload_batches_source_period_year" in constraint_names
    assert "ck_upload_batches_source_period_month" in constraint_names
    assert "ck_upload_batches_source_record_mmdd" in constraint_names
    assert "source_period_year" in UploadBatch.__table__.c
    assert "source_period_month" in UploadBatch.__table__.c
    assert "source_record_mmdd" in UploadBatch.__table__.c


def test_table_instance_constraints_match_spec() -> None:
    constraint_names = {constraint.name for constraint in UploadTableInstance.__table__.constraints}
    assert "uq_table_instances_period_seq_type" in constraint_names
    assert "ck_table_instances_type" in constraint_names
    assert "ck_table_instances_sheet_name" in constraint_names
    assert "ck_table_instances_sheet_type_match" in constraint_names
    assert "sheet_name" in UploadTableInstance.__table__.c


def test_schedule_and_fact_indexes_match_spec() -> None:
    schedule_index_names = {index.name for index in PeriodClassSchedule.__table__.indexes}
    fact_index_names = {index.name for index in MonthlySnapshotMetric.__table__.indexes}

    assert "idx_schedule_period_course" in schedule_index_names
    assert "idx_fact_period_seq_level" in fact_index_names
    assert "idx_fact_compare" in fact_index_names


def test_category_columns_are_plain_text_without_hardcoded_enums() -> None:
    category_columns = [
        ReserveDetailRow.__table__.c.acquisition_type,
        ReserveDetailRow.__table__.c.project_reliability,
        ReserveDetailRow.__table__.c.course_line,
        MonthlyClassRow.__table__.c.course_line,
        MonthlyClassRow.__table__.c.enrollment_status,
        MonthlyTargetRow.__table__.c.target_level,
        InboundRow.__table__.c.acquisition_type,
    ]

    for column in category_columns:
        assert isinstance(column.type, sa.Text)
