from unittest.mock import MagicMock, patch

import pytest

from agents.preflight import preflight


def _make_mock(returncode=0, stdout="", stderr=""):
    result = MagicMock()
    result.returncode = returncode
    result.stdout = stdout
    result.stderr = stderr
    return result


def test_preflight_passes_valid_environment(monkeypatch, tmp_path):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    session_dir = tmp_path / ".claude" / "projects"
    session_dir.mkdir(parents=True)
    (session_dir / "session_20260617.jsonl").write_text("{}\n" * 10)

    def fake_run(args, **kwargs):
        if args == ["git", "rev-parse", "--git-dir"]:
            return _make_mock(returncode=0)
        return _make_mock()

    config = {"claude_session_dir": str(session_dir), "max_session_lines": 5000}
    with patch("agents.preflight.subprocess.run", side_effect=fake_run):
        assert preflight(config) is None


def test_preflight_fails_not_in_git_repo(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")

    def fake_run(args, **kwargs):
        if args == ["git", "rev-parse", "--git-dir"]:
            return _make_mock(returncode=128)
        return _make_mock()

    with patch("agents.preflight.subprocess.run", side_effect=fake_run):
        with pytest.raises(ValueError, match="git repository"):
            preflight({"max_files_limit": 50})


def test_preflight_fails_no_api_key(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    def fake_run(args, **kwargs):
        if args == ["git", "rev-parse", "--git-dir"]:
            return _make_mock(returncode=0)
        return _make_mock()

    with patch("agents.preflight.subprocess.run", side_effect=fake_run):
        with pytest.raises(ValueError, match="OPENAI_API_KEY"):
            preflight({"max_files_limit": 50})


def test_preflight_fails_session_too_large(monkeypatch, tmp_path):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    session_dir = tmp_path / ".claude" / "projects"
    session_dir.mkdir(parents=True)
    (session_dir / "session_20260617.jsonl").write_text("{}\n" * 5001)

    def fake_run(args, **kwargs):
        if args == ["git", "rev-parse", "--git-dir"]:
            return _make_mock(returncode=0)
        return _make_mock()

    config = {"claude_session_dir": str(session_dir), "max_session_lines": 5000}
    with patch("agents.preflight.subprocess.run", side_effect=fake_run):
        with pytest.raises(ValueError, match="too large"):
            preflight(config)


def test_preflight_fails_not_found_session(monkeypatch, tmp_path):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    session_dir = tmp_path / ".claude" / "projects"
    session_dir.mkdir(parents=True)

    def fake_run(args, **kwargs):
        if args == ["git", "rev-parse", "--git-dir"]:
            return _make_mock(returncode=0)
        return _make_mock()

    config = {"claude_session_dir": str(session_dir), "max_session_lines": 5000}
    with patch("agents.preflight.subprocess.run", side_effect=fake_run):
        with pytest.raises(ValueError, match="session files"):
            preflight(config)
