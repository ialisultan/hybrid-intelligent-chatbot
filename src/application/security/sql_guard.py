"""Read-only SQL validation for NL-to-SQL execution."""

import re

from src.domain.exceptions.base import DatabaseError

_FORBIDDEN_KEYWORDS = re.compile(
    r"\b("
    r"INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|TRUNCATE|GRANT|REVOKE|COPY|"
    r"MERGE|EXEC|EXECUTE|CALL|REPLACE|INTO|UPSERT|ATTACH|DETACH|PRAGMA|"
    r"VACUUM|REINDEX|CLUSTER|COMMENT|SECURITY|OWNER"
    r")\b",
    re.IGNORECASE,
)

_WRITE_HINTS = re.compile(
    r"\b(FOR\s+UPDATE|LOCK\s+IN\s+SHARE\s+MODE)\b",
    re.IGNORECASE,
)

_COMMENT_PATTERN = re.compile(r"(--|/\*)")


def validate_read_only_sql(sql: str) -> str:
    """Validate and normalize a read-only SQL statement.

    Raises DatabaseError when the query is not a safe single read-only statement.
    """
    normalized = sql.strip().rstrip(";").strip()
    if not normalized:
        raise DatabaseError("Empty SQL query")

    if _COMMENT_PATTERN.search(normalized):
        raise DatabaseError("SQL comments are not allowed")

    if ";" in normalized:
        raise DatabaseError("Multiple SQL statements are not allowed")

    upper = normalized.upper()
    if not (upper.startswith("SELECT") or upper.startswith("WITH")):
        raise DatabaseError("Only SELECT or WITH (read) queries are allowed")

    if _WRITE_HINTS.search(normalized):
        raise DatabaseError("Query contains non-read-only clauses")

    if _FORBIDDEN_KEYWORDS.search(normalized):
        raise DatabaseError("Query contains forbidden SQL keywords")

    return normalized
