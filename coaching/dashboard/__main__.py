"""
Entrypoint: python -m coaching.dashboard

Reads JSON context from stdin, runs the dashboard module, prints JSON result.
"""

from ..core import load_context, run_and_print
from ..core.failsafe import run_safely

run_safely(lambda: run_and_print("dashboard", load_context()))
