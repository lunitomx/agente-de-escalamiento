#!/usr/bin/env python3
"""Qualify the Codex-only RaiSE workspace contract without provisioning optional runtimes."""

from __future__ import annotations
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ALLOWED = {
    "workspace-hermes_config_missing",
    "workspace-runtime_python_missing",
    "workspace-runtime_command_outside_workspace",
}


def main() -> int:
    manifest = ROOT / ".raise" / "manifest.yaml"
    config = ROOT / ".raise" / "config.toml"
    if not manifest.is_file() or not config.is_file():
        print("Status: fail")
        print("Reason: missing RaiSE project contract")
        return 1
    if not (ROOT / ".venv" / "bin" / "python").is_file():
        print("Status: fail")
        print("Reason: primary project venv missing")
        return 1
    if (ROOT / ".venv-mcp").exists() or (ROOT / ".hermes").exists():
        print("Status: fail")
        print("Reason: optional runtime was provisioned")
        return 1
    result = subprocess.run(
        ["uv", "run", "rai", "doctor", "--json"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError:
        print("Status: fail")
        print("Reason: RaiSE doctor did not emit JSON")
        return 1
    errors = {
        item["check_id"]
        for item in payload.get("results", [])
        if item.get("status") == "error"
    }
    unexpected = errors - ALLOWED
    if unexpected:
        print("Status: fail")
        print(f"Reason: unexpected doctor errors: {sorted(unexpected)}")
        return 1
    if errors != ALLOWED:
        print("Status: fail")
        print(
            f"Reason: expected legacy profile findings: {sorted(ALLOWED)}; got: {sorted(errors)}"
        )
        return 1
    print("Status: pass")
    print("Contract: codex-only")
    print("Optional legacy workspace findings: 3")
    print("Provisioned secondary runtimes: 0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
