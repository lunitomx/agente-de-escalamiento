"""
Entrypoint: python -m coaching.export

Reads JSON context from stdin, runs the export module, prints JSON result.
"""
from ..core import load_context, run_and_print

run_and_print("export", load_context())
