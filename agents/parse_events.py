"""Parse session_raw into structured behavior events."""

from datetime import datetime


_REAL_TOOL_MAP = {
    "Read": "read_file",
    "Write": "write_file",
    "Edit": "str_replace",
    "Bash": "bash",
}


def _line_count(text: str) -> int:
    if not text or not text.strip():
        return 0
    return text.count("\n") + 1


def _extract_text(content) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = [
            block["text"]
            for block in content
            if isinstance(block, dict) and block.get("type") == "text" and "text" in block
        ]
        return "\n".join(parts)
    return ""


def _assistant_content(event: dict):
    message = event.get("message")
    if isinstance(message, dict):
        return message.get("content")
    return event.get("content")


def _is_human_turn(event: dict) -> bool:
    if event.get("role") == "human":
        return True
    if event.get("type") != "user":
        return False
    if event.get("origin", {}).get("kind") == "human":
        return True
    message = event.get("message", {})
    if message.get("role") != "user":
        return False
    content = message.get("content")
    if isinstance(content, str):
        return True
    if isinstance(content, list) and any(
        not (isinstance(b, dict) and b.get("type") == "tool_result")
        for b in content
    ):
        return True
    return False


def _tool_blocks(event: dict):
    if event.get("role") == "tool_use":
        yield event
        return
    if event.get("type") != "assistant":
        return
    content = _assistant_content(event)
    if not isinstance(content, list):
        return
    for block in content:
        if isinstance(block, dict) and block.get("type") == "tool_use":
            yield block


def _parse_tool_block(block: dict):
    if block.get("role") == "tool_use":
        return block.get("tool"), block.get("path"), block.get("command"), {}
    if block.get("type") == "tool_use":
        name = block.get("name")
        tool = _REAL_TOOL_MAP.get(name)
        inp = block.get("input") or {}
        return tool, inp.get("file_path"), inp.get("command"), inp
    return None, None, None, {}


def parse_events(collect_output: dict) -> dict:
    session_raw = collect_output.get("session_raw", [])

    files_read = []
    files_written = []
    bash_commands = []
    tool_call_count = 0
    estimated_turns = 0
    assistant_messages = []
    lines_added = 0
    lines_removed = 0

    for event in session_raw:
        if _is_human_turn(event):
            estimated_turns += 1

        if event.get("role") == "assistant" or event.get("type") == "assistant":
            text = _extract_text(_assistant_content(event))
            if text:
                assistant_messages.append(text[:500])

        for block in _tool_blocks(event):
            tool, path, command, inp = _parse_tool_block(block)
            if not tool:
                continue
            tool_call_count += 1
            if tool == "read_file" and path:
                files_read.append(path)
            elif tool in ("write_file", "str_replace") and path:
                files_written.append(path)
                if tool == "write_file":
                    lines_added += _line_count(inp.get("content", ""))
                else:
                    lines_added += _line_count(inp.get("new_string", ""))
                    lines_removed += _line_count(inp.get("old_string", ""))
            elif tool == "bash" and command:
                bash_commands.append(command)

    bash_commands = bash_commands[:100]
    files_changed = list(dict.fromkeys(files_written))

    timestamps = [e.get("timestamp") for e in session_raw if e.get("timestamp")]
    if len(timestamps) >= 2:
        t0 = datetime.fromisoformat(timestamps[0])
        t1 = datetime.fromisoformat(timestamps[-1])
        duration_seconds = int((t1 - t0).total_seconds())
    else:
        duration_seconds = None

    if tool_call_count == 0 and estimated_turns == 0:
        raise ValueError("Session appears to have no tool calls or human turns")

    return {
        "files_read": files_read,
        "files_written": files_written,
        "bash_commands": bash_commands,
        "tool_call_count": tool_call_count,
        "estimated_turns": estimated_turns,
        "duration_seconds": duration_seconds,
        "assistant_messages": assistant_messages,
        "files_changed": files_changed,
        "lines_added": lines_added,
        "lines_removed": lines_removed,
    }
