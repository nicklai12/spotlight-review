import json
from pathlib import Path

from agents.parse_events import parse_events


def _load_fixture(name="example_session.jsonl"):
    fixture = Path(__file__).parent.parent / "fixtures" / name
    session_raw = []
    for line in fixture.read_text(encoding="utf-8").splitlines():
        try:
            session_raw.append(json.loads(line.strip()))
        except json.JSONDecodeError:
            pass
    return {"session_raw": session_raw}


def test_parse_events_extracts_files_read():
    result = parse_events(_load_fixture())
    assert "src/utils.py" in result["files_read"]
    assert "tests/test_utils.py" in result["files_read"]


def test_parse_events_counts_tool_calls():
    result = parse_events(_load_fixture())
    assert result["tool_call_count"] >= 6


def test_parse_events_calculates_duration():
    result = parse_events(_load_fixture())
    assert isinstance(result["duration_seconds"], int)
    assert result["duration_seconds"] > 0


def test_parse_events_handles_real_claude_log():
    result = parse_events(_load_fixture("example_real_session.jsonl"))
    assert result["tool_call_count"] == 4
    assert result["estimated_turns"] == 2
    assert "/workspaces/spotlight-review/src/utils.py" in result["files_read"]
    assert "/workspaces/spotlight-review/src/helpers.py" in result["files_written"]
    assert "/workspaces/spotlight-review/src/utils.py" in result["files_written"]
    assert "python -m pytest tests/" in result["bash_commands"]
    assert result["files_changed"] == ["/workspaces/spotlight-review/src/helpers.py", "/workspaces/spotlight-review/src/utils.py"]
    assert result["lines_added"] > 0
    assert result["lines_removed"] > 0
    assert any("重複邏輯" in m for m in result["assistant_messages"])
    assert isinstance(result["duration_seconds"], int)
    assert result["duration_seconds"] > 0


def test_parse_events_backward_compatible_with_fixture():
    result = parse_events(_load_fixture("example_session.jsonl"))
    assert result["tool_call_count"] >= 6
    assert result["estimated_turns"] >= 2
    assert result["duration_seconds"] > 0
    assert "src/utils.py" in result["files_read"]
    assert result["files_changed"]
    assert result["lines_added"] >= 0
    assert result["lines_removed"] >= 0
