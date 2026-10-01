"""Enable `python3 -m coaching.summary` invocation."""

from coaching.core.failsafe import run_safely
from coaching.summary import _main

run_safely(_main)
