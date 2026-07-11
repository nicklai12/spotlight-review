import json
import os

from agents.sources.base import BaseSourceAdapter


class CodexCLIAdapter(BaseSourceAdapter):
    SOURCE_TYPE = "codex"

    def __init__(self, session_dir: str = "~/.codex/sessions"):
        self.session_dir = os.path.expanduser(session_dir)

    def find_latest_session(self) -> str:
        jsonl_files = []
        for root, _, files in os.walk(self.session_dir):
            for name in files:
                if name.endswith(".jsonl"):
                    jsonl_files.append(os.path.join(root, name))
        if not jsonl_files:
            raise ValueError(f"No Codex sessions in {self.session_dir}")
        return max(jsonl_files, key=lambda p: os.path.getmtime(p))

    def read_session(self, source_path: str) -> list[dict]:
        session_raw = []
        keys = ("role", "tool", "path", "command", "content", "timestamp")
        with open(source_path, encoding="utf-8") as f:
            for line in f:
                try:
                    event = json.loads(line.strip())
                except json.JSONDecodeError:
                    continue
                t, tool = event.get("type"), event.get("tool_name")
                inp = event.get("input", {})
                entry = dict.fromkeys(keys)
                entry["content"] = event.get("content")
                entry["timestamp"] = event.get("timestamp")
                if t == "user_message":
                    entry["role"] = "human"
                elif t == "assistant_message":
                    entry["role"] = "assistant"
                elif t == "tool_call" and tool == "shell":
                    entry["role"] = "tool_use"
                    entry["tool"] = "bash"
                    entry["command"] = inp.get("cmd")
                elif t == "tool_call" and tool in ("read_file", "write_file"):
                    entry["role"] = "tool_use"
                    entry["tool"] = tool
                    entry["path"] = inp.get("path")
                else:
                    continue
                session_raw.append(entry)
        return session_raw
