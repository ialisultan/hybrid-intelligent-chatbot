"""Local dev preflight checks for make targets."""

from __future__ import annotations

import socket
import sys
from pathlib import Path


def check_postgres(host: str, port: int) -> bool:
    try:
        with socket.create_connection((host, port), timeout=2):
            return True
    except OSError:
        return False


def check_sqlite(path: str) -> bool:
    db_path = Path(path)
    if not db_path.is_absolute():
        db_path = Path.cwd() / db_path
    if db_path.exists():
        return True
    try:
        db_path.parent.mkdir(parents=True, exist_ok=True)
        return db_path.parent.is_dir()
    except OSError:
        return False


def main() -> None:
    target = sys.argv[1] if len(sys.argv) > 1 else "doctor"
    root = Path(__file__).resolve().parents[1]
    venv_python = root / ".venv" / "bin" / "python"
    env_file = root / ".env"

    if not venv_python.exists():
        print("ERROR: .venv not found. Run: make setup", file=sys.stderr)
        sys.exit(1)

    env_keys: list[str] = []
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            if line and not line.startswith("#") and "=" in line:
                env_keys.append(line.split("=", 1)[0])

    sys.path.insert(0, str(root))
    from src.infrastructure.config import get_settings

    get_settings.cache_clear()
    settings = get_settings()
    using_sqlite = settings.is_sqlite

    if using_sqlite:
        db_ok = check_sqlite(settings.sqlite_path)
        db_label = f"sqlite ({settings.sqlite_path})"
    else:
        check_host = (
            "127.0.0.1"
            if settings.postgres_host in {"postgres", "localhost"}
            else settings.postgres_host
        )
        db_ok = check_postgres(check_host, settings.postgres_port)
        db_label = f"postgres ({check_host}:{settings.postgres_port})"

    if target == "doctor":
        print("Local setup diagnostics:")
        print("  venv: OK")
        print(f"  .env keys: {len(env_keys)} ({', '.join(env_keys) if env_keys else 'none'})")
        print(f"  database {db_label}: {'OK' if db_ok else 'DOWN'}")
        print(f"  sql dialect: {settings.sql_dialect}")
        print(f"  vector backend: {settings.vector_store_backend}")
        if settings.vector_store_backend == "qdrant":
            qdrant_host = (
                "127.0.0.1"
                if settings.qdrant_host in {"qdrant", "localhost"}
                else settings.qdrant_host
            )
            qdrant_ok = check_postgres(qdrant_host, settings.qdrant_port)
            print(f"  qdrant ({qdrant_host}:{settings.qdrant_port}): {'OK' if qdrant_ok else 'DOWN'}")
        elif settings.vector_store_backend == "pinecone":
            pinecone_ok = bool(settings.pinecone_api_key.strip() and settings.pinecone_index.strip())
            print(f"  pinecone config: {'OK' if pinecone_ok else 'MISSING KEYS'}")
        if len(env_keys) < 3:
            print("  hint: consider copying .env.example for full local config")

    if target in {"doctor", "check", "migrate-local", "seed-local"} and not db_ok:
        if using_sqlite:
            print(
                f"ERROR: SQLite database path is not usable: {settings.sqlite_path}",
                file=sys.stderr,
            )
        else:
            check_host = (
                "127.0.0.1"
                if settings.postgres_host in {"postgres", "localhost"}
                else settings.postgres_host
            )
            print(
                f"ERROR: PostgreSQL is not reachable at {check_host}:{settings.postgres_port}.\n"
                "Start it with: make postgres-up\n"
                "Or use SQLite (default): remove DATABASE_URL from .env or set "
                "DATABASE_URL=sqlite+aiosqlite:///data/local.db",
                file=sys.stderr,
            )
        sys.exit(1)


if __name__ == "__main__":
    main()
