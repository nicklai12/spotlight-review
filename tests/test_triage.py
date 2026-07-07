from agents.triage import triage


def test_triage_small_diff_returns_auto():
    parse_output = {
        "files_changed": ["src/a.py", "src/b.py"],
        "lines_added": 30,
        "lines_removed": 20,
    }
    result = triage(parse_output)
    assert result["verdict"] == "auto"
    assert result["risk_level"] == "low"


def test_triage_large_diff_returns_warn():
    parse_output = {
        "files_changed": [f"src/file{i}.py" for i in range(15)],
        "lines_added": 120,
        "lines_removed": 80,
    }
    result = triage(parse_output)
    assert result["verdict"] == "warn"
    assert result["risk_level"] == "medium"


def test_triage_migration_file_returns_skip():
    parse_output = {
        "files_changed": ["db/migrations/001_init.py"],
        "lines_added": 50,
        "lines_removed": 10,
    }
    result = triage(parse_output)
    assert result["verdict"] == "skip"
    assert result["risk_level"] == "high"
    assert "migration" in result["reason"].lower()


def test_triage_lockfile_adds_score():
    parse_output = {
        "files_changed": ["poetry.lock"],
        "lines_added": 400,
        "lines_removed": 200,
    }
    result = triage(parse_output)
    assert result["verdict"] in ("warn", "skip")
