#!/usr/bin/env python3
import argparse
import json
import sys
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

import yaml
from agents.audit import audit
from agents.collect_session import collect_session
from agents.format import format_output
from agents.logger import get_weekly_stats, log_run
from agents.parse_events import parse_events
from agents.preflight import preflight
from agents.risk_flag import risk_flag
from agents.summarize import summarize
from agents.triage import triage


def _base(run_id, **kwargs):
    return {"run_id": run_id, "status": "started", "step": "preflight",
            "verdict": "pending", "files_changed": 0, "lines_delta": 0,
            "audit_passed": None, "error_msg": "", **kwargs}


def _fail(run_id, step, error, **kwargs):
    log_run(_base(run_id, status="failed", step=step, error_msg=str(error), **kwargs))
    print(error, file=sys.stderr)
    sys.exit(1)


@contextmanager
def _step(run_id, step, **kwargs):
    log_run(_base(run_id, status="running", step=step, **kwargs))
    try:
        yield
    except Exception as e:
        _fail(run_id, step, e, **kwargs)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--source",
                        choices=["auto", "claude_code", "codex", "cursor"],
                        default="auto",
                        help="Session source (default: auto-detect)")
    parser.add_argument("--session", dest="session_path",
                        help="Direct path to session file")
    if "--stats" in sys.argv:
        s = get_weekly_stats()
        print(f"Spotlight — Last 7 Days\n───────────────────────\nTotal runs:       {s['total_runs']}\nCompleted:        {s['completed_runs']}\nFailed:           {s['failed_runs']}\nSkipped:          {s['skipped_runs']}\nAudit pass rate:  {s['audit_pass_rate']:.0%}\nAvg files/run:    {s['avg_files_changed']:.1f}\nCommon failure:   {s['most_common_failure'] or 'None'}\n")
        sys.exit(0)
    args = parser.parse_args()
    config_path = Path(__file__).resolve().with_name("spotlight.config.yaml")
    with config_path.open(encoding="utf-8") as f:
        config = yaml.safe_load(f)
    run_id = datetime.utcnow().isoformat()
    log_run(_base(run_id))
    try:
        preflight(config)
    except Exception as e:
        _fail(run_id, "preflight", e)
    with _step(run_id, "collect"):
        collect_output = collect_session(source=args.source, config=config,
                                         session_path=args.session_path)
    with _step(run_id, "parse"):
        parse_output = parse_events(collect_output)
    files_changed = len(parse_output["files_written"])
    lines_delta = parse_output.get("lines_added", 0) + parse_output.get("lines_removed", 0)
    log_run(_base(run_id, status="running", step="triage", files_changed=files_changed, lines_delta=lines_delta))
    triage_result = triage(parse_output)
    if triage_result["verdict"] == "skip":
        print(f"[spotlight] Skipped: {triage_result['reason']}", file=sys.stderr)
        log_run(_base(run_id, status="skipped", step="triage", verdict="skip", files_changed=files_changed, lines_delta=lines_delta))
        sys.exit(0)
    if args.dry_run:
        print(json.dumps(parse_output, ensure_ascii=False, indent=2))
        sys.exit(0)
    verdict = triage_result["verdict"]
    log_run(_base(run_id, status="running", step="risk_flag", files_changed=files_changed, lines_delta=lines_delta))
    risk_output = risk_flag(parse_output)
    if risk_output["risk_level"] == "high": print("[spotlight] ⚠️  High risk session detected. Review carefully.", file=sys.stderr)
    with _step(run_id, "summarize", verdict=verdict, files_changed=files_changed, lines_delta=lines_delta):
        summarize_output = summarize(parse_output, model=config["model"], risk_output=risk_output)
    with _step(run_id, "audit", verdict=verdict, files_changed=files_changed, lines_delta=lines_delta, audit_passed=False):
        audit(collect_output, parse_output, summarize_output, risk_output=risk_output)
    markdown = format_output(summarize_output, parse_output)
    if verdict == "warn":
        markdown = f"> ⚠️  {triage_result['reason']}\n\n" + markdown
    log_run(_base(run_id, status="completed", step="done", verdict=verdict, files_changed=files_changed, lines_delta=lines_delta, audit_passed=True))
    print(markdown)


if __name__ == "__main__":
    main()
