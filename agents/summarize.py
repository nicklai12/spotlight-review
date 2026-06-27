"""Summarize parsed diff using an LLM."""

import json
import os

import openai


def summarize(parse_output: dict, model: str = "gpt-4o-mini") -> dict:
    client = openai.OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

    hunks_text = "\n".join(h["diff_snippet"] for h in parse_output["hunks"])

    system_prompt = (
        "你是一個 coding session 分析助手，專門幫助開發者理解 AI coding agent 做了什麼。\n"
        "你只輸出 JSON，不輸出任何其他文字，不加 markdown code block。"
    )
    user_prompt = f"""你剛剛完成了一個 coding session。以下是 git diff 資料。
請分析後，回傳 JSON 格式的 session 報告。

變更檔案：{parse_output["files_changed"]}
新增行數：{parse_output["lines_added"]}
刪除行數：{parse_output["lines_removed"]}

Diff 內容：
{hunks_text}

請回傳以下 JSON 格式（嚴格按照格式，不加任何 markdown）：
{{
  "summary": "用繁體中文寫 1-2 句，說明這個 session 整體做了什麼",
  "changes": [
    "具體變更 1（說明改了什麼、在哪個檔案）",
    "具體變更 2"
  ],
  "risks": [
    "潛在風險或需注意的地方，若無則回傳空列表"
  ],
  "next_actions": [
    "建議的下一步行動，若無則回傳空列表"
  ],
  "questions": [
    "這次 session 後仍待釐清的問題，若無則回傳空列表"
  ],
  "files_touched": [
    "實際有意義的檔案路徑（用於驗證，必須是真實存在於 diff 中的）"
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
