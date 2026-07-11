import json
import os

from agents.sources.base import BaseSourceAdapter


_TYPE_TO_ROLE = {"user": "human", "assistant": "assistant", "tool_use": "tool_use"}


def _map_role(raw: dict) -> str | None:
    role = raw.get("role")
    if role:
        return role
    return _TYPE_TO_ROLE.get(raw.get("type"))


def _extract_content(raw: dict):
    if "content" in raw:
        return raw["content"]
    message = raw.get("message")
    if isinstance(message, dict):
        return message.get("content")
    if isinstance(message, str):
        return message
    return None

class ClaudeCodeAdapter(BaseSourceAdapter):
    SOURCE_TYPE = "claude_code"

    def __init__(self, session_dir: str = "~/.claude/projects"):
        self.session_dir = os.path.expanduser(session_dir)

    def find_latest_session(self) -> str:
        jsonl_files = []
        for root, _, files in os.walk(self.session_dir):
            for name in files:
                if name.endswith(".jsonl"):
                    jsonl_files.append(os.path.join(root, name))
        if not jsonl_files:
            raise ValueError(
                f"No Claude Code session files found in {self.session_dir}/"
            )
        return max(jsonl_files, key=lambda p: os.path.getmtime(p))

    def read_session(self, source_path: str) -> list[dict]:
        session_raw = []
        keys = ("role", "tool", "path", "command", "content", "timestamp")
        with open(source_path, encoding="utf-8") as f:
            for line in f:
                try:
                    raw = json.loads(line.strip())
                except json.JSONDecodeError:
                    continue
                entry = dict.fromkeys(keys)
                entry.update(raw)
                entry["role"] = _map_role(raw)
                entry["content"] = _extract_content(raw)
                entry["timestamp"] = raw.get("timestamp")
                session_raw.append(entry)
        return session_raw
