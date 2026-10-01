"""Enable ``python3 -m coaching.execution_habits`` invocation."""

from coaching.core.failsafe import run_safely
from coaching.execution_habits import _main

run_safely(_main)
