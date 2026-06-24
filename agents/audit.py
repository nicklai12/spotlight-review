"""Audit upstream outputs for consistency and completeness."""


def audit(collect_output: dict, parse_output: dict, summarize_output: dict) -> bool:
    what_changed = summarize_output.get("what_changed", "")
    if len(what_changed) < 10:
        raise ValueError("Audit failed: what_changed is too short or missing")

    files_touched = summarize_output.get("files_touched")
    if not isinstance(files_touched, list) or len(files_touched) == 0:
        raise ValueError("Audit failed: files_touched is missing or empty")

    real_files = set(parse_output.get("files_changed", []))
    claimed_files = set(files_touched)
    if not real_files & claimed_files:
        raise ValueError(
            "Audit failed: LLM hallucinated files.\n"
            f" Real files: {parse_output.get('files_changed', [])}\n"
            f" LLM claimed: {files_touched}"
        )

    if parse_output.get("lines_added", 0) + parse_output.get("lines_removed", 0) <= 0:
        raise ValueError("Audit failed: no lines added or removed")

    return True
