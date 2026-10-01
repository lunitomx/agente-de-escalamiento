"""Enable ``python -m coaching.evidence`` invocation."""

from coaching.core.failsafe import run_safely
from coaching.evidence import _main

run_safely(_main)
