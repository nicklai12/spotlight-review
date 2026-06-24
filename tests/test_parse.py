import pytest
from pathlib import Path

from agents.parse import parse


@pytest.fixture
def example_diff() -> str:
    return Path("fixtures/example_01.diff").read_text(encoding="utf-8")


def test_parse_files_changed(example_diff):
    result = parse({"git_diff_raw": example_diff})
    assert result["files_changed"] == ["src/utils/helpers.py", "src/main.py"]


def test_parse_line_counts(example_diff):
    result = parse({"git_diff_raw": example_diff})
    assert result["lines_added"] > 0
    assert result["lines_removed"] > 0


def test_parse_empty_diff_raises():
    with pytest.raises(ValueError, match="Parse failed: no files found in diff"):
        parse({"git_diff_raw": ""})
