"""
Entrypoint: python -m coaching.dashboard

Reads JSON context from stdin, runs the dashboard module, prints JSON result.
"""
from ..core import load_context, run_and_print

run_and_print("dashboard", load_context())
