"""Ensure .scaleup/ is on sys.path so coaching.* imports resolve from repo root."""
import sys
from pathlib import Path

# Add .scaleup/ to path so `from coaching.summary import run` works
# when pytest is invoked from the repo root.
_scaleup = Path(__file__).parent
if str(_scaleup) not in sys.path:
    sys.path.insert(0, str(_scaleup))
