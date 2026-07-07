"""Pre-flight safety checks before running the summary pipeline."""
import os
import subprocess


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
    diff = subprocess.run(
        ["git", "diff", "HEAD"], capture_output=True, text=True
    )
    if not diff.stdout.strip():
        raise ValueError("No changes detected. Nothing to summarize.")

    # Guard 3: scale limit
    names = subprocess.run(
        ["git", "diff", "HEAD", "--name-only"], capture_output=True, text=True
    )
    file_count = len(names.stdout.strip().split("\n")) if names.stdout.strip() else 0
    limit = config.get("max_files_limit", 50)
    if file_count > limit:
        raise ValueError(
            f"Diff contains {file_count} files (limit: {limit}). "
            f"Use 'git diff HEAD -- <specific_path>' to narrow scope."
        )
