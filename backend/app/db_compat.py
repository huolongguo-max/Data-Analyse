from __future__ import annotations

from sqlalchemy import BigInteger, CheckConstraint, Integer, JSON, Text, text
from sqlalchemy.dialects.postgresql import JSONB

from app.config import settings

DATABASE_SCHEMAS = ("meta", "source", "base", "fact")
IS_SQLITE = settings.is_sqlite

BIGINT_TYPE = BigInteger().with_variant(Integer(), "sqlite")
JSON_TYPE = JSON().with_variant(JSONB(astext_type=Text()), "postgresql")
CURRENT_TIMESTAMP_DEFAULT = text("CURRENT_TIMESTAMP")


def db_schema(schema_name: str) -> str | None:
    return None if IS_SQLITE else schema_name


def table_args(*items: object, schema: str) -> tuple[object, ...]:
    if IS_SQLITE:
        return items
    return (*items, {"schema": schema})


def table_kwargs(schema: str) -> dict[str, str]:
    if IS_SQLITE:
        return {}
    return {"schema": schema}


def fk(target: str) -> str:
    if not IS_SQLITE:
        return target

    parts = target.split(".")
    if len(parts) == 3 and parts[0] in DATABASE_SCHEMAS:
        return ".".join(parts[1:])
    return target


def mmdd_check_constraint(name: str) -> CheckConstraint:
    if IS_SQLITE:
        sql = (
            "source_record_mmdd IS NULL OR "
            "(length(source_record_mmdd) = 4 AND source_record_mmdd GLOB '[0-9][0-9][0-9][0-9]')"
        )
    else:
        sql = "source_record_mmdd IS NULL OR source_record_mmdd ~ '^[0-9]{4}$'"
    return CheckConstraint(sql, name=name)


def qualified_table_name(schema_name: str, table_name: str) -> str:
    actual_schema = db_schema(schema_name)
    if actual_schema:
        return f"{actual_schema}.{table_name}"
    return table_name
