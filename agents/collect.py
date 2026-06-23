"""Collect raw git diff and shell history from the execution environment."""

import os
import subprocess
from datetime import datetime
from pathlib import Path


def _run_git(args: list[str]) -> str:
    result = subprocess.run(args, capture_output=True, text=True)
    return result.stdout.strip()


def _read_history() -> str:
    for path in (Path.home() / ".zsh_history", Path.home() / ".bash_history"):
        try:
            lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
            return "\n".join(lines[-50:])
        except (FileNotFoundError, IsADirectoryError):
            continue
    return ""


def collect() -> dict:
    repo_root = _run_git(["git", "rev-parse", "--show-toplevel"])
    if not repo_root:
        raise ValueError("Not inside a git repository")

    git_diff_raw = _run_git(["git", "diff", "HEAD"])
    if not git_diff_raw:
        raise ValueError("No staged changes found")

    return {
        "git_diff_raw": git_diff_raw,
        "shell_history_raw": _read_history(),
        "timestamp": datetime.utcnow().isoformat(),
        "repo_root": repo_root,
    }
