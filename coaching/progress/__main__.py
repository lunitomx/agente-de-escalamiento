"""Enable `python3 -m coaching.progress` invocation."""

from coaching.core.failsafe import run_safely
from coaching.progress import _main

run_safely(_main)
