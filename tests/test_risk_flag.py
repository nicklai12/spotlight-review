import pytest

from agents.risk_flag import risk_flag


def test_flag_sensitive_path():
    result = risk_flag({"files_read": ["/home/user/.ssh/config"]})
    assert result["risk_level"] == "high"
    assert any(f["category"] == "sensitive_path" and f["severity"] == "critical" for f in result["flags"])
    assert "/home/user/.ssh/config" in result["flagged_paths"]


def test_flag_destructive_command():
    result = risk_flag({"bash_commands": ["rm -rf /tmp/old_project"]})
    assert any(f["category"] == "destructive_command" and f["severity"] == "critical" for f in result["flags"])
    assert "rm -rf /tmp/old_project" in result["flagged_commands"]


def test_flag_permission_escalation():
    result = risk_flag({"bash_commands": ["sudo apt-get install python3"]})
    assert result["risk_level"] == "medium"
    assert any(f["category"] == "permission_escalation" and f["severity"] == "warn" for f in result["flags"])


def test_flag_high_tool_volume():
    result = risk_flag({"tool_call_count": 60})
    assert result["risk_level"] == "low"
    assert any(f["category"] == "high_tool_volume" and f["severity"] == "info" for f in result["flags"])


def test_no_flags_returns_low():
    result = risk_flag({"files_read": [], "files_written": [], "bash_commands": [], "tool_call_count": 0})
    assert result["risk_level"] == "low"
    assert result["flags"] == []
    assert result["flagged_commands"] == []
    assert result["flagged_paths"] == []
