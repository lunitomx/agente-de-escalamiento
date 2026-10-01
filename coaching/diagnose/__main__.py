"""Enable `python3 -m coaching.diagnose` invocation."""

from coaching.core.failsafe import run_safely
from coaching.diagnose import _main

run_safely(_main)
