"""Parse raw git diff into a structured summary."""

import re


def parse(collect_output: dict) -> dict:
    diff_raw = collect_output.get("git_diff_raw", "")

    files_changed = re.findall(r"^diff --git a/.*? b/(.+)$", diff_raw, flags=re.MULTILINE)
    if not files_changed:
        raise ValueError("Parse failed: no files found in diff")

    lines_added = 0
    lines_removed = 0
    for line in diff_raw.splitlines():
        if line.startswith("+") and not line.startswith("+++"):
            lines_added += 1
        elif line.startswith("-") and not line.startswith("---"):
            lines_removed += 1

    hunks = []
    for block in re.split(r"(?=^diff --git )", diff_raw, flags=re.MULTILINE):
        if not block.strip():
            continue
        match = re.match(r"^diff --git a/.*? b/(.+)$", block, flags=re.MULTILINE)
        if not match:
            continue
        snippet = block
        if len(snippet) > 2000:
            snippet = snippet[:2000] + "\n...[truncated]"
        hunks.append({"file": match.group(1), "diff_snippet": snippet})

    return {
        "files_changed": files_changed,
        "lines_added": lines_added,
        "lines_removed": lines_removed,
        "hunks": hunks,
    }
