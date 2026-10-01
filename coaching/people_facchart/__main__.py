"""Enable ``python3 -m coaching.people_facchart`` invocation."""

from coaching.core.failsafe import run_safely
from coaching.people_facchart import _main

run_safely(_main)
