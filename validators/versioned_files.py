"""List what git versions, so checks ignore local ignored leftovers (S86.37).

A repository check must give the same answer in Eduardo's working checkout
and in a clean clone.  Files that ``.gitignore`` excludes (local agent skills,
old work folders) are not part of the product and must not tip a check.

"Versioned" here means tracked, or untracked but not ignored: a new file that
a developer has not added yet still counts, so a bad case cannot hide by
simply not being staged.  Without git the whole disk is read, which is
stricter, never laxer.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path, PurePosixPath


def _git_list(repo_root: Path, *args: str) -> list[str] | None:
    try:
        completed = subprocess.run(
            ["git", "-C", str(repo_root), "ls-files", "-z", *args],
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError:
        return None
    if completed.returncode != 0:
        return None
    return [entry for entry in completed.stdout.split("\0") if entry]


def _disk_files(repo_root: Path, subdir: str) -> list[str]:
    base = repo_root / subdir
    found: list[str] = []
    for current, dirs, files in os.walk(base, followlinks=False):
        here = Path(current)
        names = list(files) + [name for name in dirs if (here / name).is_symlink()]
        found.extend((here / name).relative_to(repo_root).as_posix() for name in names)
    return found


def versioned_files(repo_root: Path, subdir: str) -> tuple[PurePosixPath, ...]:
    """Files under ``subdir`` that git tracks or would track, present on disk."""
    listed = _git_list(
        repo_root, "--cached", "--others", "--exclude-standard", "--", subdir
    )
    if listed is None:
        listed = _disk_files(repo_root, subdir)
    present = {
        entry
        for entry in listed
        if (repo_root / entry).exists() or (repo_root / entry).is_symlink()
    }
    return tuple(PurePosixPath(entry) for entry in sorted(present))


def is_versioned(repo_root: Path, relative: str) -> bool:
    """True when git tracks ``relative`` (even if it was deleted on disk)."""
    listed = _git_list(repo_root, "--cached", "--", relative)
    return bool(listed)
