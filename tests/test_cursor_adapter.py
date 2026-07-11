import shutil
from pathlib import Path

from agents.sources.cursor import CursorAdapter


FIXTURE = Path(__file__).parent.parent / "fixtures" / "example_cursor_state.db"


def _setup_workspace(tmp_path):
    workspace = tmp_path / "workspaceStorage"
    db_dir = workspace / "abc123"
    db_dir.mkdir(parents=True)
    db_path = db_dir / "state.vscdb"
    shutil.copy(FIXTURE, db_path)
    return workspace


def test_cursor_adapter_reads_user_bubbles(tmp_path):
    workspace = _setup_workspace(tmp_path)
    adapter = CursorAdapter(workspace_dir=str(workspace))
    result = adapter.collect()
    user_entries = [e for e in result["session_raw"] if e["role"] == "human"]
    assert len(user_entries) == 2
    assert all(e["content"] for e in user_entries)


def test_cursor_adapter_reads_assistant_bubbles(tmp_path):
    workspace = _setup_workspace(tmp_path)
    adapter = CursorAdapter(workspace_dir=str(workspace))
    result = adapter.collect()
    assistant_entries = [e for e in result["session_raw"] if e["role"] == "assistant"]
    assert len(assistant_entries) == 2
    assert all(e["content"] for e in assistant_entries)


def test_cursor_adapter_returns_correct_source_type(tmp_path):
    workspace = _setup_workspace(tmp_path)
    adapter = CursorAdapter(workspace_dir=str(workspace))
    result = adapter.collect()
    assert result["source_type"] == "cursor"
    assert result["session_file"].endswith("::test-composer-001")
