from unittest.mock import MagicMock, patch

import pytest

from agents.preflight import preflight


def _make_mock(returncode=0, stdout="", stderr=""):
    result = MagicMock()
    result.returncode = returncode
    result.stdout = stdout
    result.stderr = stderr
    return result


def test_preflight_passes_valid_environment(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")

    def fake_run(args, **kwargs):
        if args == ["git", "rev-parse", "--git-dir"]:
            return _make_mock(returncode=0)
        if args == ["git", "diff", "HEAD"]:
            return _make_mock(stdout="some diff content")
        if args == ["git", "diff", "HEAD", "--name-only"]:
            return _make_mock(stdout="\n".join(f"src/file{i}.py" for i in range(49)))
        return _make_mock()

    with patch("agents.preflight.subprocess.run", side_effect=fake_run):
        assert preflight({"max_files_limit": 50}) is None


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


def test_preflight_fails_too_many_files(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    files = [f"src/file{i}.py" for i in range(51)]

    def fake_run(args, **kwargs):
        if args == ["git", "rev-parse", "--git-dir"]:
            return _make_mock(returncode=0)
        if args == ["git", "diff", "HEAD"]:
            return _make_mock(stdout="some diff content")
        if args == ["git", "diff", "HEAD", "--name-only"]:
            return _make_mock(stdout="\n".join(files))
        return _make_mock()

    with patch("agents.preflight.subprocess.run", side_effect=fake_run):
        with pytest.raises(ValueError, match="limit: 50"):
            preflight({"max_files_limit": 50})
