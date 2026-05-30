"""SQL guard unit tests."""

import pytest

pytestmark = pytest.mark.unit

from src.application.security.sql_guard import validate_read_only_sql
from src.domain.exceptions.base import DatabaseError


def test_accepts_select():
    sql = validate_read_only_sql("SELECT id FROM customers")
    assert sql == "SELECT id FROM customers"


def test_accepts_with_cte():
    sql = validate_read_only_sql(
        "WITH recent AS (SELECT id FROM orders) SELECT * FROM recent"
    )
    assert sql.startswith("WITH")


def test_rejects_insert():
    with pytest.raises(DatabaseError, match="Only SELECT or WITH"):
        validate_read_only_sql("INSERT INTO customers VALUES (1)")


def test_rejects_delete():
    with pytest.raises(DatabaseError, match="Only SELECT or WITH"):
        validate_read_only_sql("DELETE FROM customers")


def test_rejects_merge():
    with pytest.raises(DatabaseError, match="Only SELECT or WITH|forbidden"):
        validate_read_only_sql("MERGE INTO customers USING src ON true")


def test_rejects_exec():
    with pytest.raises(DatabaseError, match="Only SELECT or WITH|forbidden"):
        validate_read_only_sql("EXEC sp_executesql N'SELECT 1'")


def test_rejects_stacked_statements():
    with pytest.raises(DatabaseError, match="Multiple SQL"):
        validate_read_only_sql("SELECT 1; DROP TABLE customers")


def test_rejects_semicolon_injection():
    with pytest.raises(DatabaseError, match="Multiple SQL"):
        validate_read_only_sql("SELECT 1; SELECT 2")


def test_rejects_comments():
    with pytest.raises(DatabaseError, match="comments"):
        validate_read_only_sql("SELECT 1 -- drop table")


def test_rejects_block_comments():
    with pytest.raises(DatabaseError, match="comments"):
        validate_read_only_sql("SELECT /* hidden */ 1")


def test_rejects_for_update():
    with pytest.raises(DatabaseError, match="non-read-only"):
        validate_read_only_sql("SELECT * FROM orders FOR UPDATE")


def test_strips_trailing_semicolon():
    sql = validate_read_only_sql("SELECT 1;")
    assert sql == "SELECT 1"
