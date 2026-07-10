"""Collect the latest Claude Code session file."""

import json
import sys
from datetime import datetime
from pathlib import Path


def collect_session(session_path=None):
    if session_path is None:
        for i, arg in enumerate(sys.argv):
            if arg == "--session" and i + 1 < len(sys.argv):
                session_path = sys.argv[i + 1]
                break

    if session_path:
        session_file = Path(session_path).expanduser().resolve()
    else:
        projects_dir = Path.home() / ".claude" / "projects"
        jsonl_files = list(projects_dir.rglob("*.jsonl"))
        if not jsonl_files:
            raise ValueError("No Claude Code session files found in ~/.claude/projects/")
        session_file = max(jsonl_files, key=lambda p: p.stat().st_mtime)

    with open(session_file, encoding="utf-8") as f:
        lines = f.readlines()

    session_raw = []
    for line in lines:
        try:
            session_raw.append(json.loads(line.strip()))
        except json.JSONDecodeError:
            pass

    if not session_raw:
        raise ValueError("Session file is empty or all lines are invalid JSON")

    session_id = session_file.stem or "session_unknown"

    return {
        "session_file": str(session_file),
        "session_raw": session_raw,
        "session_id": session_id,
        "timestamp": datetime.utcnow().isoformat(),
    }
