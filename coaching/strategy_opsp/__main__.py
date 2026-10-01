"""Enable `python3 -m coaching.strategy_opsp` invocation."""

from coaching.core.failsafe import run_safely
from coaching.strategy_opsp import _main

run_safely(_main)
