import os
from pathlib import Path

from agents.collect_session import collect_session


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
