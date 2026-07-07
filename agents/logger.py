"""Logger for spotlight runs and weekly statistics."""
import json
import sys
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path

LOG_DIR = Path.home() / ".spotlight"
LOG_FILE = LOG_DIR / "runs.jsonl"


def log_run(entry: dict) -> None:
    try:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        with LOG_FILE.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception as e:
        print(f"Warning: failed to log run: {e}", file=sys.stderr)


def get_weekly_stats() -> dict:
    cutoff = datetime.now() - timedelta(days=7)
    entries = []
    try:
        if LOG_FILE.exists():
            with LOG_FILE.open("r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        entry = json.loads(line)
                        if datetime.fromisoformat(entry["run_id"]) >= cutoff:
                            entries.append(entry)
    except Exception:
        pass

    total = len(entries)
    completed = [e for e in entries if e.get("status") == "completed"]
    failed = [e for e in entries if e.get("status") == "failed"]
    skipped = [e for e in entries if e.get("status") == "skipped"]
    audit_passed = sum(1 for e in completed if e.get("audit_passed") is True)
    audit_pass_rate = round(audit_passed / len(completed), 2) if completed else 0.0
    avg_files = round(sum(e.get("files_changed", 0) for e in entries) / total, 2) if total else 0.0
    failure_msgs = [e.get("error_msg", "") for e in failed if e.get("error_msg")]
    most_common = Counter(failure_msgs).most_common(1)[0][0][:50] if failure_msgs else ""
    return {
        "total_runs": total,
        "completed_runs": len(completed),
        "failed_runs": len(failed),
        "skipped_runs": len(skipped),
        "audit_pass_rate": audit_pass_rate,
        "avg_files_changed": avg_files,
        "most_common_failure": most_common,
    }
