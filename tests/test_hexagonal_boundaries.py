"""Application layer must not import LangChain or SQLAlchemy."""

import ast
from pathlib import Path

import pytest

pytestmark = pytest.mark.unit

FORBIDDEN_ROOTS = ("langchain", "sqlalchemy")
APPLICATION_ROOT = Path(__file__).resolve().parents[1] / "src" / "application"


def _forbidden_imports(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    violations: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root = alias.name.split(".")[0]
                if root in FORBIDDEN_ROOTS:
                    violations.append(f"{path}: import {alias.name}")
        elif isinstance(node, ast.ImportFrom) and node.module:
            root = node.module.split(".")[0]
            if root in FORBIDDEN_ROOTS:
                violations.append(f"{path}: from {node.module}")
    return violations


def test_application_layer_has_no_framework_leaks():
    py_files = list(APPLICATION_ROOT.rglob("*.py"))
    assert py_files, "expected application Python modules"
    all_violations: list[str] = []
    for path in py_files:
        all_violations.extend(_forbidden_imports(path))
    assert not all_violations, "framework imports in application layer:\n" + "\n".join(
        all_violations
    )
