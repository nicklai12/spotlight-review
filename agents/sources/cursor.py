import json
import os
import platform
import sqlite3

from agents.sources.base import BaseSourceAdapter


class CursorAdapter(BaseSourceAdapter):
    SOURCE_TYPE = "cursor"

    def __init__(self, workspace_dir: str = None):
        if workspace_dir:
            self.workspace_dir = os.path.expanduser(workspace_dir)
        elif platform.system() == "Darwin":
            self.workspace_dir = os.path.expanduser(
                "~/Library/Application Support/Cursor/User/workspaceStorage"
            )
        else:
            self.workspace_dir = os.path.expanduser(
                "~/.config/Cursor/User/workspaceStorage"
            )

    def find_latest_session(self) -> str:
        db_files = []
        for root, _, files in os.walk(self.workspace_dir):
            for name in files:
                if name == "state.vscdb":
                    db_files.append(os.path.join(root, name))
        if not db_files:
            raise ValueError(f"No Cursor workspace DB in {self.workspace_dir}")
        db_path = max(db_files, key=lambda p: os.path.getmtime(p))
        data = self._load_composer_data(db_path)
        composer_id = self._get_latest_composer_id(data)
        return f"{db_path}::{composer_id}"

    def read_session(self, source_path: str) -> list[dict]:
        db_path, composer_id = source_path.split("::", 1)
        data = self._load_composer_data(db_path)
        session = next(
            (c for c in data.get("allComposers", [])
             if c.get("composerId") == composer_id),
            None,
        )
        if session is None:
            raise ValueError(f"Composer session {composer_id} not found")
        session_raw = []
        keys = ("role", "tool", "path", "command", "content", "timestamp")
        for bubble in session.get("bubbles", []):
            entry = dict.fromkeys(keys)
            entry["content"] = bubble.get("text")
            entry["timestamp"] = bubble.get("createdAt")
            bubble_type = bubble.get("type")
            if bubble_type == 1:
                entry["role"] = "human"
            elif bubble_type == 2:
                entry["role"] = "assistant"
            else:
                continue
            session_raw.append(entry)
        return session_raw

    def _load_composer_data(self, db_path: str) -> dict:
        conn = sqlite3.connect(db_path)
        row = conn.execute(
            "SELECT value FROM ItemTable WHERE key = 'composer.composerData'"
        ).fetchone()
        conn.close()
        if not row:
            raise ValueError("composer.composerData not found in Cursor DB")
        return json.loads(row[0])

    def _get_latest_composer_id(self, data: dict) -> str:
        composers = data.get("allComposers", [])
        if not composers:
            raise ValueError("No composer sessions found in Cursor DB")
        latest = max(composers, key=lambda c: c.get("createdAt", ""))
        return latest.get("composerId") or composers[0].get("composerId")
