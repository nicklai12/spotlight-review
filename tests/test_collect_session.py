import os
import shutil
from pathlib import Path

from agents.collect_session import collect_session, _detect_source


def test_collect_session_finds_latest_file(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    projects_dir = tmp_path / ".claude" / "projects"
    projects_dir.mkdir(parents=True)
    old = projects_dir / "session_old.jsonl"
    new = projects_dir / "session_new.jsonl"
    old.write_text('{"x": 1}\n')
    new.write_text('{"x": 2}\n')
    os.utime(old, (0, 1000))
    os.utime(new, (0, 2000))

    result = collect_session()

    assert result["session_file"] == str(new)
    assert result["session_id"] == "session_new"


def test_collect_session_parses_valid_lines(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    projects_dir = tmp_path / ".claude" / "projects"
    projects_dir.mkdir(parents=True)
    session = projects_dir / "session_20260617.jsonl"
    session.write_text('{}\n{}\n{}\n')

    result = collect_session()

    assert len(result["session_raw"]) == 3


def test_collect_session_skips_invalid_lines(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    projects_dir = tmp_path / ".claude" / "projects"
    projects_dir.mkdir(parents=True)
    session = projects_dir / "session_20260617.jsonl"
    session.write_text('{}\n{}\nnot json\n')

    result = collect_session()

    assert len(result["session_raw"]) == 2


def test_collect_session_detects_codex(tmp_path):
    codex_dir = tmp_path / ".codex" / "sessions" / "2026" / "01" / "01"
    codex_dir.mkdir(parents=True)
    (codex_dir / "rollout-abc123.jsonl").write_text('{"type":"user_message"}\n')
    config = {
        "claude_session_dir": str(tmp_path / "no_claude"),
        "codex_session_dir": str(tmp_path / ".codex" / "sessions"),
        "cursor_workspace_dir": str(tmp_path / "no_cursor"),
    }
    assert _detect_source(config) == "codex"


def test_collect_session_uses_specified_source(tmp_path):
    claude_dir = tmp_path / ".claude" / "projects"
    claude_dir.mkdir(parents=True)
    (claude_dir / "session.jsonl").write_text('{"role":"human"}\n')
    codex_dir = tmp_path / ".codex" / "sessions"
    codex_dir.mkdir(parents=True)
    fixture = Path(__file__).parent.parent / "fixtures" / "example_codex_session.jsonl"
    shutil.copy(fixture, codex_dir / "rollout-abc.jsonl")
    config = {
        "claude_session_dir": str(claude_dir),
        "codex_session_dir": str(codex_dir),
    }
    result = collect_session(source="codex", config=config)
    assert result["source_type"] == "codex"
