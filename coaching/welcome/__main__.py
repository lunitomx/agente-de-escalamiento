"""Enable `python3 -m coaching.welcome` invocation."""

from coaching.core.failsafe import run_safely
from coaching.welcome import _main

run_safely(_main)
