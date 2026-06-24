"""Summarize parsed diff using an LLM."""

import json
import os

import openai


def summarize(parse_output: dict, model: str = "gpt-4o-mini") -> dict:
    client = openai.OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

    hunks_text = "\n".join(h["diff_snippet"] for h in parse_output["hunks"])

    system_prompt = "你是一個程式碼變更分析助手。\n你只輸出 JSON，不輸出任何其他文字。"
    user_prompt = f"""分析以下 git diff 資料，回傳 JSON 格式的摘要。

變更檔案：{parse_output["files_changed"]}
新增行數：{parse_output["lines_added"]}
刪除行數：{parse_output["lines_removed"]}

Diff 內容：
{hunks_text}

請回傳以下 JSON 格式（不要加 markdown code block）：
{{
  "what_changed": "用繁體中文說明改了什麼（1-3句）",
  "why_inferred": "推斷這次改動的目的（不確定可留空字串）",
  "files_touched": ["實際有意義的檔案路徑列表"]
}}
"""

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )

    raw = response.choices[0].message.content
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"LLM returned invalid JSON: {raw}") from exc
