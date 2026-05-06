"""
Entrypoint: python -m coaching.pulse

Reads JSON context from stdin, runs the pulse module, prints JSON result.
"""
from ..core import load_context, run_and_print

run_and_print("pulse", load_context())
