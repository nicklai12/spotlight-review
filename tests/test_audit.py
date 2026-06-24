import pytest

from agents.audit import audit


def test_audit_passes_valid_input():
    collect_output = {}
    parse_output = {
        "files_changed": ["src/main.py"],
        "lines_added": 5,
        "lines_removed": 2,
    }
    summarize_output = {
        "what_changed": "Updated main entry point logic.",
        "files_touched": ["src/main.py"],
    }
    assert audit(collect_output, parse_output, summarize_output) is True


def test_audit_fails_on_hallucinated_files():
    collect_output = {}
    parse_output = {"files_changed": ["real.py"], "lines_added": 1, "lines_removed": 0}
    summarize_output = {
        "what_changed": "Some change description here.",
        "files_touched": ["fake.js"],
    }
    with pytest.raises(ValueError, match="hallucinated"):
        audit(collect_output, parse_output, summarize_output)


def test_audit_fails_on_empty_what_changed():
    collect_output = {}
    parse_output = {"files_changed": ["a.py"], "lines_added": 1, "lines_removed": 0}
    summarize_output = {"what_changed": "", "files_touched": ["a.py"]}
    with pytest.raises(ValueError):
        audit(collect_output, parse_output, summarize_output)
