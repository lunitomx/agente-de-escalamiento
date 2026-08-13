"""S47.7: sync_live_clone.sh keeps the working clone and the clone that
serves the live ~/.claude/skills symlinks from silently drifting apart."""

import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "sync_live_clone.sh"


def run(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["bash", str(SCRIPT), *args],
        capture_output=True,
        text=True,
        timeout=10,
    )


def _init_repo(path: Path, remote_url: str) -> None:
    subprocess.run(["git", "init", "-q", str(path)], check=True)
    subprocess.run(
        ["git", "-C", str(path), "remote", "add", "origin", remote_url], check=True
    )
    subprocess.run(
        ["git", "-C", str(path), "config", "user.email", "t@example.com"], check=True
    )
    subprocess.run(["git", "-C", str(path), "config", "user.name", "Test"], check=True)
    (path / "README.md").write_text("x\n")
    subprocess.run(["git", "-C", str(path), "add", "README.md"], check=True)
    subprocess.run(["git", "-C", str(path), "commit", "-q", "-m", "init"], check=True)


def test_script_exists_and_is_executable():
    assert SCRIPT.exists()
    assert SCRIPT.stat().st_mode & 0o111


def test_missing_argument_shows_usage():
    result = run()
    assert result.returncode == 2
    assert "Uso:" in result.stderr


def test_nonexistent_live_clone_errors():
    result = run("/nonexistent/path/does-not-exist")
    assert result.returncode == 1
    assert "no es un repositorio git" in result.stderr


def test_mismatched_remotes_refuses_to_sync(tmp_path):
    live = tmp_path / "live"
    _init_repo(live, "https://github.com/example/other-repo.git")
    result = run(str(live))
    assert result.returncode == 1
    assert "no coinciden" in result.stderr
