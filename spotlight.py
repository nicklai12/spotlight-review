#!/usr/bin/env python3
import argparse
import json
import sys
from pathlib import Path

import yaml

from agents.collect import collect
from agents.parse import parse
from agents.summarize import summarize
from agents.audit import audit
from agents.format import format_output


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    config_path = Path(__file__).with_name("spotlight.config.yaml")
    with config_path.open(encoding="utf-8") as f:
        config = yaml.safe_load(f)

    try:
        collect_output = collect()
        parse_output = parse(collect_output)
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)

    if args.dry_run:
        print(json.dumps(parse_output, ensure_ascii=False, indent=2))
        sys.exit(0)

    try:
        summarize_output = summarize(parse_output, model=config["model"])
        audit(collect_output, parse_output, summarize_output)
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)

    print(format_output(summarize_output, parse_output))


if __name__ == "__main__":
    main()
