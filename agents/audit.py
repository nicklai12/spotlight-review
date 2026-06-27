"""Audit upstream outputs for consistency and completeness."""


def audit(collect_output: dict, parse_output: dict, summarize_output: dict) -> bool:
    summary = summarize_output.get("summary")
    if not isinstance(summary, str) or len(summary) < 10:
        raise ValueError("Audit failed: required field 'summary' is missing or empty")

    changes = summarize_output.get("changes")
    if not isinstance(changes, list) or len(changes) == 0:
        raise ValueError("Audit failed: required field 'changes' is missing or empty")

    files_touched = summarize_output.get("files_touched")
    if not isinstance(files_touched, list) or len(files_touched) == 0:
        raise ValueError("Audit failed: required field 'files_touched' is missing or empty")

    real = set(parse_output["files_changed"])
    claimed = set(files_touched)
    if not real & claimed:
        raise ValueError(
            "Audit failed: LLM hallucinated files.\n"
            f" Real files: {list(real)}\n"
            f" LLM claimed: {list(claimed)}"
        )

    if any(len(str(item)) < 5 for item in changes):
        raise ValueError("Audit failed: changes list contains items that are too short")

    if parse_output.get("lines_added", 0) + parse_output.get("lines_removed", 0) <= 0:
        raise ValueError("Audit failed: no actual line changes detected in diff")

    return True
