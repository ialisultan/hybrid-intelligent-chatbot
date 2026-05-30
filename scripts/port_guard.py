#!/usr/bin/env python3
"""Check whether a TCP port is free before starting a dev server."""

from __future__ import annotations

import subprocess
import sys

HINTS: dict[str, dict[str, str]] = {
    "backend": {
        "running": "The backend may already be running:",
        "check": "  curl http://localhost:{port}/health",
        "stop": "make stop-backend",
        "start": "make run",
    },
    "streamlit": {
        "running": "The Streamlit UI may already be running:",
        "check": "  open http://localhost:{port}",
        "stop": "make stop-streamlit",
        "start": "make streamlit",
    },
}


def listeners(port: int) -> list[dict[str, str]]:
    try:
        out = subprocess.check_output(
            ["lsof", "-nP", f"-iTCP:{port}", "-sTCP:LISTEN"],
            text=True,
            stderr=subprocess.DEVNULL,
        )
    except subprocess.CalledProcessError:
        return []

    rows: list[dict[str, str]] = []
    for line in out.strip().splitlines()[1:]:
        parts = line.split()
        if len(parts) >= 2:
            rows.append({"command": parts[0], "pid": parts[1]})
    return rows


def main() -> int:
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    service = sys.argv[2] if len(sys.argv) > 2 else "backend"
    hints = HINTS.get(service, HINTS["backend"])

    occupiers = listeners(port)
    if not occupiers:
        return 0

    print(f"ERROR: Port {port} is already in use.", file=sys.stderr)
    for row in occupiers:
        print(f"  {row['command']} (pid {row['pid']})", file=sys.stderr)
    print(file=sys.stderr)
    print(hints["running"], file=sys.stderr)
    print(hints["check"].format(port=port), file=sys.stderr)
    print(file=sys.stderr)
    print("To free the port and start a new server:", file=sys.stderr)
    print(f"  {hints['stop']}", file=sys.stderr)
    print(f"  {hints['start']}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
