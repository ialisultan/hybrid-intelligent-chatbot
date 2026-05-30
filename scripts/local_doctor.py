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
    check_host = "127.0.0.1" if settings.postgres_host in {"postgres", "localhost"} else settings.postgres_host
    postgres_up = check_postgres(check_host, settings.postgres_port)

    if target == "doctor":
        print("Local setup diagnostics:")
        print("  venv: OK")
        print(f"  .env keys: {len(env_keys)} ({', '.join(env_keys) if env_keys else 'none'})")
        print(f"  postgres ({check_host}:{settings.postgres_port}): {'OK' if postgres_up else 'DOWN'}")
        print(f"  vector backend: {settings.vector_store_backend}")
        if len(env_keys) < 3:
            print("  hint: consider copying .env.example for full local config")

    if target in {"doctor", "check", "migrate-local", "seed-local"} and not postgres_up:
        print(
            f"ERROR: PostgreSQL is not reachable at {check_host}:{settings.postgres_port}.\n"
            "Start it with: make postgres-up",
            file=sys.stderr,
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
