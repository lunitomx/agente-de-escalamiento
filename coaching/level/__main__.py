"""Enable `python3 -m coaching.level` invocation."""

from coaching.core.failsafe import run_safely
from coaching.level import _main

run_safely(_main)
