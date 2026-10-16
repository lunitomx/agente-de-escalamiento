"""Skip regression tests whose evidence lives only in a local, ignored folder.

Some E59/E61/E62 regression tests read review evidence under ``work/`` that
derives from the licensed book corpus and is deliberately not versioned.  In a
clean clone those files do not exist, so the test cannot say anything: it
skips with an explicit reason.  If git tracks the file, the test never skips;
a missing tracked file fails as before.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from validators.versioned_files import is_versioned


def require_local_evidence(repo_root: Path, relative: str) -> Path:
    path = repo_root / relative
    if not path.exists() and not is_versioned(repo_root, relative):
        pytest.skip(
            f"evidencia local no versionada ausente: {relative} "
            "(deriva del corpus con licencia y vive solo en la copia que la generó)"
        )
    return path
