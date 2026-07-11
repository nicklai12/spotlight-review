import os
from datetime import datetime

from agents.sources.claude_code import ClaudeCodeAdapter
from agents.sources.codex_cli import CodexCLIAdapter
from agents.sources.cursor import CursorAdapter


ADAPTERS = {
    "claude_code": ClaudeCodeAdapter,
    "codex": CodexCLIAdapter,
    "cursor": CursorAdapter,
}

def collect_session(session_path=None, source="auto", config=None):
    config = config or {}
    if source == "auto":
        source = _detect_source(config)
    if source not in ADAPTERS:
        raise ValueError(f"Unknown source: {source}. Use: {', '.join(ADAPTERS)}")
    adapter_class = ADAPTERS[source]
    adapter = adapter_class(**_get_adapter_kwargs(source, config))
    if session_path:
        session_raw = adapter.read_session(session_path)
        return {
            "session_file": session_path,
            "session_raw": session_raw,
            "session_id": os.path.splitext(os.path.basename(session_path))[0],
            "timestamp": datetime.utcnow().isoformat(),
            "source_type": adapter.SOURCE_TYPE,
        }
    return adapter.collect()


def _detect_source(config):
    claude_dir = os.path.expanduser(config.get("claude_session_dir", "~/.claude/projects"))
    if os.path.exists(claude_dir) and any(f.endswith(".jsonl") for _, _, files in os.walk(claude_dir) for f in files):
        return "claude_code"
    codex_dir = os.path.expanduser(config.get("codex_session_dir", "~/.codex/sessions"))
    if os.path.exists(codex_dir) and any(f.endswith(".jsonl") for _, _, files in os.walk(codex_dir) for f in files):
        return "codex"
    import platform
    if platform.system() == "Darwin":
        cursor_dir = "~/Library/Application Support/Cursor/User/workspaceStorage"
    else:
        cursor_dir = "~/.config/Cursor/User/workspaceStorage"
    cursor_dir = os.path.expanduser(config.get("cursor_workspace_dir") or cursor_dir)
    if os.path.exists(cursor_dir) and any(name == "state.vscdb" for _, _, files in os.walk(cursor_dir) for name in files):
        return "cursor"
    raise ValueError("No AI coding session found. Use --source to specify.")


def _get_adapter_kwargs(source, config):
    if source == "claude_code":
        return {"session_dir": config.get("claude_session_dir", "~/.claude/projects")}
    if source == "codex":
        return {"session_dir": config.get("codex_session_dir", "~/.codex/sessions")}
    if source == "cursor":
        return {"workspace_dir": config.get("cursor_workspace_dir")}
    return {}
