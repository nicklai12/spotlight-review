import json
from datetime import datetime, timedelta

import pytest

from agents import logger


@pytest.fixture
def log_path(tmp_path, monkeypatch):
    log_dir = tmp_path / ".spotlight"
    log_file = log_dir / "runs.jsonl"
    monkeypatch.setattr(logger, "LOG_DIR", log_dir)
    monkeypatch.setattr(logger, "LOG_FILE", log_file)
    return log_file


def _entry(**overrides):
    defaults = {
        "run_id": datetime.now().isoformat(),
        "status": "started",
        "step": "preflight",
        "verdict": "pending",
        "files_changed": 0,
        "lines_delta": 0,
        "audit_passed": None,
        "error_msg": "",
    }
    defaults.update(overrides)
    return defaults


def test_log_run_creates_file(log_path):
    logger.log_run(_entry())
    assert log_path.exists()
    with log_path.open("r", encoding="utf-8") as f:
        parsed = json.loads(f.readline().strip())
    assert parsed["status"] == "started"


def test_log_run_appends_multiple(log_path):
    for _ in range(3):
        logger.log_run(_entry())
    with log_path.open("r", encoding="utf-8") as f:
        lines = [line for line in f if line.strip()]
    assert len(lines) == 3


def test_get_weekly_stats_calculates_correctly(log_path):
    base = datetime.now()
    logger.log_run(_entry(status="completed", step="audit", verdict="auto", files_changed=5, lines_delta=100, audit_passed=True))
    logger.log_run(_entry(run_id=(base - timedelta(minutes=1)).isoformat(), status="completed", step="audit", verdict="auto", files_changed=3, lines_delta=50, audit_passed=True))
    logger.log_run(_entry(run_id=(base - timedelta(minutes=2)).isoformat(), status="completed", step="audit", verdict="warn", files_changed=15, lines_delta=600, audit_passed=False))
    logger.log_run(_entry(run_id=(base - timedelta(minutes=3)).isoformat(), status="failed", step="preflight", error_msg="Not inside a git repository"))

    stats = logger.get_weekly_stats()
    assert stats["total_runs"] == 4
    assert stats["completed_runs"] == 3
    assert stats["failed_runs"] == 1
    assert stats["skipped_runs"] == 0
    assert stats["audit_pass_rate"] == 0.67
