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
        "summary": "Updated the main entry point and added helper utilities.",
        "changes": [
            "Modified src/main.py to print a formatted timestamp.",
            "Added src/utils/helpers.py with format_timestamp and slugify.",
        ],
        "risks": [],
        "next_actions": ["Add unit tests for the new helpers."],
        "questions": [],
        "files_touched": ["src/main.py", "src/utils/helpers.py"],
    }
    assert audit(collect_output, parse_output, summarize_output) is True


def test_audit_fails_on_hallucinated_files():
    collect_output = {}
    parse_output = {
        "files_changed": ["src/main.py"],
        "lines_added": 1,
        "lines_removed": 0,
    }
    summarize_output = {
        "summary": "Some change description here.",
        "changes": ["Updated src/main.py."],
        "risks": [],
        "next_actions": [],
        "questions": [],
        "files_touched": ["src/nonexistent.js"],
    }
    with pytest.raises(ValueError, match="hallucinated"):
        audit(collect_output, parse_output, summarize_output)


def test_audit_fails_on_empty_changes():
    collect_output = {}
    parse_output = {
        "files_changed": ["src/main.py"],
        "lines_added": 1,
        "lines_removed": 0,
    }
    summarize_output = {
        "summary": "Some change description here.",
        "changes": [],
        "risks": [],
        "next_actions": [],
        "questions": [],
        "files_touched": ["src/main.py"],
    }
    with pytest.raises(ValueError, match="required field"):
        audit(collect_output, parse_output, summarize_output)


def test_audit_fails_on_short_change_items():
    collect_output = {}
    parse_output = {
        "files_changed": ["src/main.py"],
        "lines_added": 1,
        "lines_removed": 0,
    }
    summarize_output = {
        "summary": "Some change description here.",
        "changes": ["ok", "."],
        "risks": [],
        "next_actions": [],
        "questions": [],
        "files_touched": ["src/main.py"],
    }
    with pytest.raises(ValueError, match="too short"):
        audit(collect_output, parse_output, summarize_output)


def test_audit_fails_when_high_risk_but_empty_risks_list():
    collect_output = {}
    parse_output = {
        "files_changed": ["src/main.py"],
        "lines_added": 1,
        "lines_removed": 0,
    }
    summarize_output = {
        "summary": "Some change description here.",
        "changes": ["Updated src/main.py."],
        "risks": [],
        "next_actions": [],
        "questions": [],
        "files_touched": ["src/main.py"],
    }
    risk_output = {"risk_level": "high", "flags": [{"severity": "high", "category": "test", "detail": "x"}]}
    with pytest.raises(ValueError, match="ignored risk signals"):
        audit(collect_output, parse_output, summarize_output, risk_output)
