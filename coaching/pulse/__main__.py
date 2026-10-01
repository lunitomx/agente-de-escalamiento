"""
Entrypoint: python -m coaching.pulse

Reads JSON context from stdin, runs the pulse module, prints JSON result.
"""

from ..core import load_context, run_and_print
from ..core.failsafe import run_safely

run_safely(lambda: run_and_print("pulse", load_context()))
