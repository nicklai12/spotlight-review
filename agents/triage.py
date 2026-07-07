"""Assess diff complexity and recommend handling strategy."""


def triage(parse_output: dict) -> dict:
    files = parse_output.get("files_changed", [])
    added = parse_output.get("lines_added", 0)
    removed = parse_output.get("lines_removed", 0)
    total_lines = added + removed

    score = 0
    if len(files) > 10:
        score += 2
    if total_lines > 500:
        score += 2
    if any(f.endswith((".lock", ".sum")) for f in files):
        score += 1
    if any("migration" in f or "schema" in f for f in files):
        score += 4

    if score == 0:
        return {
            "verdict": "auto",
            "reason": "Small, focused diff. Safe to auto-summarize.",
            "risk_level": "low",
        }

    if score <= 3:
        return {
            "verdict": "warn",
            "reason": "Large or complex diff. Summary may be incomplete.",
            "risk_level": "medium",
        }

    reasons = []
    if len(files) > 10:
        reasons.append(f"{len(files)} files")
    if total_lines > 500:
        reasons.append(f"{total_lines} line changes")
    if any(f.endswith((".lock", ".sum")) for f in files):
        reasons.append("lockfile changes")
    if any("migration" in f or "schema" in f for f in files):
        reasons.append("migration/schema changes")

    return {
        "verdict": "skip",
        "reason": f"Diff contains {', '.join(reasons)}. Manual review recommended.",
        "risk_level": "high",
    }
