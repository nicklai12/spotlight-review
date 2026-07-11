from pathlib import Path

from agents.sources.codex_cli import CodexCLIAdapter


FIXTURE = Path(__file__).parent.parent / "fixtures" / "example_codex_session.jsonl"


def test_codex_adapter_maps_user_message():
    adapter = CodexCLIAdapter()
    session_raw = adapter.read_session(str(FIXTURE))
    user_entries = [e for e in session_raw if e["role"] == "human"]
    assert len(user_entries) == 2
    assert all(e["content"] for e in user_entries)
    assert all(e["tool"] is None for e in user_entries)


def test_codex_adapter_maps_shell_tool_call():
    adapter = CodexCLIAdapter()
    session_raw = adapter.read_session(str(FIXTURE))
    shell_entries = [e for e in session_raw if e["tool"] == "bash"]
    assert len(shell_entries) == 1
    assert shell_entries[0]["role"] == "tool_use"
    assert shell_entries[0]["command"] == "python -m pytest tests/"


def test_codex_adapter_skips_token_count():
    adapter = CodexCLIAdapter()
    session_raw = adapter.read_session(str(FIXTURE))
    assert len(session_raw) == 7
    assert all("total_tokens" not in e for e in session_raw)
