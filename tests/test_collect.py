import unittest
from unittest.mock import patch

import pytest

from agents.collect import collect


class TestCollect:
    @patch("agents.collect.subprocess.run")
    def test_collect_returns_valid_schema(self, mock_run):
        mock_run.side_effect = [
            type("R", (), {"stdout": "/repo\n"})(),
            type("R", (), {"stdout": "diff --git a/f.txt b/f.txt\n"})(),
        ]

        result = collect()

        assert isinstance(result, dict)
        assert result["git_diff_raw"] == "diff --git a/f.txt b/f.txt"
        assert "shell_history_raw" in result
        assert "timestamp" in result
        assert result["repo_root"] == "/repo"

    @patch("agents.collect.subprocess.run")
    def test_collect_raises_on_empty_diff(self, mock_run):
        mock_run.side_effect = [
            type("R", (), {"stdout": "/repo\n"})(),
            type("R", (), {"stdout": ""})(),
        ]

        with pytest.raises(ValueError, match="No staged changes found"):
            collect()
