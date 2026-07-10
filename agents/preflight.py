"""Pre-flight safety checks before running the summary pipeline."""
import os
import subprocess
from pathlib import Path


def preflight(config: dict) -> None:
    # Guard 1: environment integrity
    git_check = subprocess.run(
        ["git", "rev-parse", "--git-dir"], capture_output=True
    )
    if git_check.returncode != 0:
        raise ValueError("Not inside a git repository")

    if not os.environ.get("OPENAI_API_KEY", "").strip():
        raise ValueError("OPENAI_API_KEY is not set")

    # Guard 2: workspace state
    claude_session_dir = Path(config["claude_session_dir"]).expanduser()
    session_files = list(claude_session_dir.rglob("*.jsonl"))
    if not session_files:
        raise ValueError(
            f"No Claude Code session files found in {claude_session_dir}"
        )

    # Guard 3: scale limit
    latest = max(session_files, key=lambda p: p.stat().st_mtime)
    line_count = sum(1 for _ in open(latest, encoding="utf-8"))
    limit = config.get("max_session_lines", 5000)
    if line_count > limit:
        raise ValueError(
            f"Session file is too large ({line_count} lines, limit: {limit})"
        )
