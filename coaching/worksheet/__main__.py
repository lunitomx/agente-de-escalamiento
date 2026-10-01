"""Enable `python3 -m coaching.worksheet` invocation."""

from coaching.core.failsafe import run_safely
from coaching.worksheet import _main

run_safely(_main)
