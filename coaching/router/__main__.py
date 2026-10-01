"""Enable `python3 -m coaching.router` invocation."""

from coaching.core.failsafe import run_safely
from coaching.router import _main

run_safely(_main)
