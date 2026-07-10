"""Summarize parsed diff using an LLM."""

import json
import os

import openai


def _format_flags(risk_output: dict) -> str:
    if not risk_output or not risk_output.get("flags"):
        return "無"
    return "\n".join(
        f"- [{f['severity'].upper()}] {f['category']}: {f['detail']}"
        for f in risk_output["flags"]
    )


def summarize(parse_output: dict, model: str = "gpt-4o-mini", risk_output: dict | None = None) -> dict:
    client = openai.OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

    system_prompt = (
        "你是一個 coding session 分析助手，專門幫助開發者理解 AI coding agent 做了什麼。\n"
        "你只輸出 JSON，不輸出任何其他文字，不加 markdown code block。"
    )
    user_prompt = f"""你是一個 AI coding agent 行為分析助手。
以下是一個 Claude Code session 的行為記錄。
請分析 agent 做了什麼、產生了什麼風險、建議人類下一步如何行動。

=== 行為統計 ===
讀取的檔案：{parse_output["files_read"]}
修改的檔案：{parse_output["files_written"]}
執行的指令（前20條）：{parse_output["bash_commands"][:20]}
工具呼叫總次數：{parse_output["tool_call_count"]}
對話輪數：{parse_output["estimated_turns"]}
Session 時長：{parse_output["duration_seconds"]} 秒

=== 風險審計結果 ===
整體風險等級：{risk_output.get("risk_level", "unknown") if risk_output else "未執行"}
標記項目：
{_format_flags(risk_output)}

=== Agent 說了什麼（節錄）===
{chr(10).join(parse_output["assistant_messages"][:5])}

請回傳以下 JSON 格式（不加 markdown code block）：
{{
  "summary": "用繁體中文，1-2 句說明這個 agent session 整體做了什麼",
  "changes": [
    "agent 具體執行的操作（結合 files_written 和 bash_commands 說明）"
  ],
  "risks": [
    "根據風險審計結果，列出值得人類注意的行為（若無風險可寫空列表）"
  ],
  "next_actions": [
    "建議人類接下來應該做什麼（例如：審閱 agent 修改的檔案、確認 bash 指令無誤）"
  ],
  "questions": [
    "這個 session 後仍待釐清的問題（例如：某個指令的目的不明）"
  ],
  "files_touched": [
    "agent 有意義地讀取或修改的檔案路徑（用於驗證）"
  ]
}}
"""

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )

    raw_response = response.choices[0].message.content
    try:
        return json.loads(raw_response)
    except json.JSONDecodeError as exc:
        raise ValueError(f"LLM returned invalid JSON: {raw_response}") from exc
