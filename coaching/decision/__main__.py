"""Enable ``python -m coaching.decision`` invocation."""

from coaching.core.failsafe import run_safely
from coaching.decision import _main

run_safely(_main)
