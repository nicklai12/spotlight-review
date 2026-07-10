"""Rule-based risk auditing for parsed session events."""


def _common_prefix(paths):
    if not paths:
        return ""
    prefix = paths[0]
    for p in paths[1:]:
        while not p.startswith(prefix):
            prefix = prefix[:-1]
            if not prefix:
                return ""
    if prefix and not prefix.endswith("/"):
        prefix = prefix[: prefix.rfind("/") + 1] if "/" in prefix else ""
    return prefix


def risk_flag(parse_output):
    try:
        data = parse_output if isinstance(parse_output, dict) else {}
        read = list(data.get("files_read", []) or [])
        written = list(data.get("files_written", []) or [])
        cmds = list(data.get("bash_commands", []) or [])
        count = int(data.get("tool_call_count", 0) or 0)
        flags, fcmds, fpaths = [], [], []
        workdir = _common_prefix(written)

        for path in set(read + written):
            sens = (
                "/.ssh/" in path
                or "/.aws/" in path
                or "/etc/passwd" in path
                or "/etc/shadow" in path
            )
            if "/.env" in path and "/.env.example" not in path and not path.startswith(workdir):
                sens = True
            if sens:
                flags.append({"severity": "critical", "category": "sensitive_path", "detail": f"Agent accessed sensitive path: {path}"})
                fpaths.append(path)

        for cmd in cmds:
            if cmd.startswith("rm -rf") or "DROP TABLE" in cmd or "> /dev/" in cmd or "dd if=" in cmd:
                flags.append({"severity": "critical", "category": "destructive_command", "detail": f"Agent executed potentially destructive command: {cmd}"})
                fcmds.append(cmd)
            if "sudo " in cmd or "chmod 777" in cmd or "chown root" in cmd:
                flags.append({"severity": "warn", "category": "permission_escalation", "detail": f"Agent used permission escalation command: {cmd}"})
                fcmds.append(cmd)

        if written:
            for path in set(read + written):
                if not path.startswith(workdir):
                    flags.append({"severity": "warn", "category": "scope_creep", "detail": f"Agent accessed path outside working directory: {path}"})
                    fpaths.append(path)

        if count > 50:
            flags.append({"severity": "info", "category": "high_tool_volume", "detail": f"Session made {count} tool calls. Review for efficiency."})

        sev = {f["severity"] for f in flags}
        level = "high" if "critical" in sev else "medium" if "warn" in sev else "low"
        return {"risk_level": level, "flags": flags, "flagged_commands": list(dict.fromkeys(fcmds)), "flagged_paths": list(dict.fromkeys(fpaths))}
    except Exception:
        return {"risk_level": "low", "flags": [], "flagged_commands": [], "flagged_paths": []}
