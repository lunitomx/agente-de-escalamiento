"""CLI entry point for coaching.qualifier."""

from __future__ import annotations

from coaching.core.failsafe import run_safely

from . import _main

if __name__ == "__main__":
    run_safely(_main)
