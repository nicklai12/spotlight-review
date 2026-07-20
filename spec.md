# Spotlight Review — Specification

## 1. Overview

Spotlight Review 是一款 CLI 工具，用於把 AI coding agent（Claude Code / Codex CLI / Cursor）的 session log 轉換成繁體中文審計報告。核心目標：

- **可審計**：產出結構化的 session 摘要（Summary / Changes / Risks / Next Actions / Questions / Files Touched）。
- **安全優先**：session 原始內容盡量留在本機，送往 LLM 的資料僅限結構化摘要欄位。
- **多來源支援**：透過統一 adapter 介面支援 Claude Code、Codex CLI、Cursor。
- **多格式輸出**：支援 `markdown`（預設）、`pr`（GitHub PR 描述）、`handoff`（工作交接備忘錄）。

---

## 2. Functional Requirements

### 2.1 CLI 功能

| 功能 | 指令 | 說明 |
|------|------|------|
| 自動偵測來源並產生報告 | `spotlight` | 預設輸出 markdown |
| 指定來源 | `spotlight --source {auto\|claude_code\|codex\|cursor}` | 強制使用特定 adapter |
| 指定 session 檔案 | `spotlight --session /path/to/session.jsonl --source claude_code` | 直接讀取指定檔案 |
| 選擇輸出格式 | `spotlight --format {markdown\|pr\|handoff}` | 預設 `markdown` |
| 不呼叫 LLM | `spotlight --dry-run` | 只執行收集、解析、風險標記，輸出 JSON |
| 查看統計 | `spotlight --stats` | 顯示最近 7 天執行概況 |

### 2.2 Pipeline 階段

1. **初始化**：產生 `run_id`（ISO 8601 UTC 時間戳），寫入 `started` 狀態。
2. **preflight**：檢查 git repo、OPENAI_API_KEY、session 目錄與大小上限；失敗則 exit `1`。
3. **collect_session**：根據 `--source` 或自動偵測選擇 adapter，收集最新 session。
4. **parse_events**：把原始 session 解析成 Schema 2，含檔案讀寫、bash 指令、工具統計等。
5. **triage**：評估複雜度，給出 `auto` / `warn` / `skip`。
   - `skip`：印出原因，exit `0`（非錯誤）。
   - `warn`：繼續執行，最終輸出頂部附加警告橫幅。
6. **risk_flag**（`--dry-run` 時仍執行）：規則式掃描，產出風險等級與標記。
7. **summarize**（僅非 dry-run）：將結構化資料送入 LLM，產生 JSON 摘要。
8. **audit**（僅非 dry-run）：驗證摘要欄位、比對 files_touched、檢查 high risk 一致性。
9. **format**：依 `--format` 輸出對應格式。
10. **logger**：每個關鍵步驟寫入 `~/.spotlight/runs.jsonl`。

---

## 3. Non-Functional Requirements

- **資料最小化**：送往 LLM 的內容僅限結構化摘要，不含完整 session log。
- **本機優先**：原始 session 內容、檔案路徑、bash 指令不寫入執行日誌。
- **可測試性**：每個 agent 都有對應單元測試。
- **錯誤透明**：非預期失敗印出錯誤訊息到 `stderr`，exit code `1`。
- **簡潔性**：不加入未使用的抽象或配置彈性。

---

## 4. Data Schemas

### 4.1 Schema 1：Source Adapter 輸出

由 `BaseSourceAdapter.collect()` 產生，作為 `parse_events` 的輸入。

```python
{
    "session_file": str,      # 原始來源路徑（檔案路徑或 db_path::composer_id）
    "session_raw": [dict],    # 統一格式的 event list
    "session_id": str,        # 檔案名稱（去掉副檔名）
    "timestamp": str,         # ISO 8601 UTC
    "source_type": str,       # "claude_code" / "codex" / "cursor"
}
```

`session_raw` 中每個 event dict 統一包含以下 key（不存在則填 `None`）：

```python
{
    "role": "human" | "assistant" | "tool_use" | None,
    "tool": str | None,       # e.g. "bash", "read_file", "write_file", "str_replace"
    "path": str | None,       # 檔案路徑
    "command": str | None,    # bash 指令
    "content": any | None,    # 訊息內容
    "timestamp": str | None,  # ISO 8601
}
```

### 4.2 Schema 2：parse_events 輸出

```python
{
    "files_read": [str],            # 讀取的檔案路徑（可重複）
    "files_written": [str],         # 修改/寫入的檔案路徑（可重複）
    "bash_commands": [str],         # 執行的 bash 指令（最多 100 條）
    "tool_call_count": int,         # 工具呼叫次數
    "estimated_turns": int,         # 對話輪數估算
    "duration_seconds": int | None, # session 時長（秒）
    "assistant_messages": [str],    # assistant 訊息節錄（每則最多 500 字元）
    "files_changed": [str],         # 唯一化的 files_written
    "lines_added": int,             # 估算的新增行數
    "lines_removed": int,           # 估算的刪除行數
}
```

### 4.3 summarize 輸出（LLM JSON）

```python
{
    "summary": str,       # 1-2 句繁體中文整體說明
    "changes": [str],     # agent 具體執行的操作
    "risks": [str],       # 值得注意的行為
    "next_actions": [str],# 建議人類後續行動
    "questions": [str],   # 仍待釐清的問題
    "files_touched": [str]# 用於驗證的檔案路徑
}
```

### 4.4 risk_flag 輸出

```python
{
    "risk_level": "low" | "medium" | "high",
    "flags": [
        {
            "severity": "critical" | "warn" | "info",
            "category": str,
            "detail": str
        }
    ],
    "flagged_commands": [str],
    "flagged_paths": [str]
}
```

### 4.5 runs.jsonl 日誌欄位

```python
{
    "run_id": str,           # ISO 8601 UTC
    "status": "started" | "running" | "completed" | "failed" | "skipped",
    "step": str,
    "verdict": "pending" | "auto" | "warn" | "skip",
    "files_changed": int,
    "lines_delta": int,
    "audit_passed": bool | None,
    "error_msg": str,
    # 其他透過 kwargs 帶入的欄位
}
```

---

## 5. Pipeline Stages Detail

### 5.1 preflight

執行條件檢查：

1. 在 git repository 內（`git rev-parse --git-dir` 成功）。
2. 環境變數 `OPENAI_API_KEY` 已設定。
3. `claude_session_dir` 存在 `.jsonl` 檔案。
4. 最新 session 檔案行數不超過 `max_session_lines`。

> 目前實作只檢查 Claude Code session 目錄，無論 `--source` 設定為何。

### 5.2 collect_session

- `--source auto` 時依序偵測：Claude Code → Codex CLI → Cursor。
- `--source <adapter>` 時直接實例化對應 adapter。
- `--session <path>` 時，使用指定 adapter 的 `read_session()` 讀取該檔案。
- Adapter 統一繼承 `BaseSourceAdapter`。

### 5.3 parse_events

解析重點：

- 識別 human turn、assistant 訊息、tool_use block。
- 將 `Read` / `Write` / `Edit` / `Bash` 工具對應到 `read_file` / `write_file` / `str_replace` / `bash`。
- `write_file` 與 `str_replace` 分別估算 `lines_added` / `lines_removed`。
- 以第一筆與最後一筆 timestamp 計算 `duration_seconds`。
- 若完全沒有 tool call 與 human turn，拋出 `ValueError`。

### 5.4 triage

評分規則：

| 條件 | 加分 |
|------|------|
| `files_changed` > 10 | +2 |
| `lines_added + lines_removed` > 500 | +2 |
| 包含 `.lock` / `.sum` 檔案 | +1 |
| 路徑包含 `migration` / `schema` | +4 |

結果：

| 分數 | verdict | 原因 |
|------|---------|------|
| 0 | auto | Small, focused diff. |
| 1-3 | warn | Large or complex diff. |
| ≥4 | skip | 列出具體原因，建議人工審閱。 |

### 5.5 risk_flag

風險規則：

#### Sensitive Path（critical）

- 路徑包含 `/.ssh/`、`/.aws/`、`/etc/passwd`、`/etc/shadow`。
- 路徑包含 `/.env`（且非 `.env.example`、且在工作目錄外）。

#### Destructive Command（critical）

- `rm -rf`
- `DROP TABLE`
- `> /dev/`
- `dd if=`

#### Permission Escalation（warn）

- `sudo `
- `chmod 777`
- `chown root`

#### Scope Creep（warn）

- 讀取或寫入 `workdir`（以所有 `files_written` 的最長共同前綴估算）之外的檔案。

#### High Tool Volume（info）

- `tool_call_count` > 50。

風險等級由最高 severity 決定：`critical` → high、`warn` → medium、否則 low。

### 5.6 summarize

- 使用 OpenAI Chat Completions API。
- 模型由 `spotlight.config.yaml` 的 `model` 欄位指定。
- Prompt 固定為繁體中文，要求回傳純 JSON、不加 markdown code block。
- 傳送資料：
  - `files_read`、`files_written`
  - `bash_commands` 前 20 條
  - `tool_call_count`、`estimated_turns`、`duration_seconds`
  - `risk_flag` 產生的風險等級與標記
  - `assistant_messages` 前 5 則
- 根據 `--format` 加入額外提示（`FORMAT_HINTS`）。

### 5.7 audit

驗證項目：

1. `summary` 為字串且長度 ≥ 10。
2. `changes` 為非空 list。
3. `files_touched` 為非空 list。
4. `files_touched` 與 `parse_output["files_changed"]` 必須有交集（防幻覺）。
5. `changes` 每個項目長度 ≥ 5。
6. `lines_added + lines_removed` > 0。
7. 若 `risk_level == "high"`，`risks` 不得為空。

任一項目失敗拋出 `ValueError`，CLI 會記錄 `failed` 並 exit `1`。

### 5.8 format

三種輸出格式：

| 格式 | 用途 | 主要區段 |
|------|------|---------|
| `markdown` | 預設繁中審計報告 | Summary / Changes / Risks / Next Actions / Questions / Files Touched |
| `pr` | GitHub PR 描述 | `# [feat]` / Summary / Changes / Risk Flags 🚩 / Reviewer Checklist ✅ / Open Questions ❓ |
| `handoff` | 工作交接備忘錄 | 🎯 這次在做什麼 / ✅ 已完成 / ⚠️ 風險 / 📋 待辦 / ❓ 問題 / 📁 涉及的檔案 |

---

## 6. CLI Interface

```
spotlight [-h] [--dry-run] [--source {auto,claude_code,codex,cursor}]
          [--format {markdown,pr,handoff}] [--session SESSION_PATH]
          [--stats]
```

### Exit Codes

| Code | 意義 |
|------|------|
| 0 | 成功完成，或 triage 建議 skip |
| 1 | preflight 失敗、pipeline 意外錯誤、audit 失敗 |

---

## 7. Configuration

`spotlight.config.yaml`：

```yaml
source: "auto"                    # auto / claude_code / codex / cursor
model: "gpt-4o-mini"              # OpenAI 模型
language: "zh-TW"                 # 預期輸出語言（目前 prompts 已固定繁中）
history_lines: 50                 # 保留欄位，目前未使用
output: "stdout"                  # 保留欄位，目前未使用
max_files_limit: 50               # 保留欄位，目前未使用
claude_session_dir: "~/.claude/projects"
codex_session_dir: "~/.codex/sessions"
cursor_workspace_dir: null        # null = 依 OS 自動偵測
max_session_lines: 5000           # 單一 session 行數上限
```

### 環境變數

| 變數 | 說明 |
|------|------|
| `OPENAI_API_KEY` | 必要。OpenAI API key。 |

---

## 8. Logging

- 每次執行會寫入 `~/.spotlight/runs.jsonl`。
- 記錄內容僅包含執行狀態、統計數字、`audit_passed`、錯誤訊息。
- **不儲存**原始 session 內容、檔案路徑、bash 指令或 LLM 原始輸出。
- `--stats` 讀取該檔案，統計最近 7 天資料。

---

## 9. Security & Data Handling

### 9.1 本機讀取範圍

只讀取各 AI 工具寫在本機的 session log：

- Claude Code：`~/.claude/projects/**/*.jsonl`
- Codex CLI：`~/.codex/sessions/**/*.jsonl`
- Cursor：`state.vscdb`

### 9.2 送往 LLM 的資料

- 檔案路徑（`files_read`、`files_written`）
- bash 指令前 20 條
- 工具統計、風險標記
- assistant 訊息前 5 則節錄

### 9.3 注意事項

- **不主動遮罩 credential、token、密碼**。建議執行 `--dry-run` 確認內容。
- 不會傳送原始程式碼內容或完整 session log。

---

## 10. Testing

使用 `pytest`：

```bash
python -m pytest
```

測試覆蓋：

- `test_preflight.py`：git / API key / session 大小 / session 不存在
- `test_audit.py`：欄位驗證、幻覺檔案、空 changes、high risk 一致性
- `test_format_pr.py`：PR / handoff 格式區段與風險 emoji
- `test_collect_session.py`：來源偵測與 adapter 分派
- `test_parse_events.py`：事件解析與統計
- `test_risk_flag.py`：風險規則
- `test_triage.py`：複雜度評分
- `test_logger.py`：日誌與統計
- adapter tests：`test_codex_adapter.py`、`test_cursor_adapter.py`

---

## 11. Known Limitations

1. **preflight 只檢查 Claude session 目錄**：即使指定 `--source codex` 或 `--source cursor`，仍會先檢查 `claude_session_dir` 是否有 `.jsonl`。
2. **Config 保留欄位未使用**：`history_lines`、`output`、`max_files_limit` 目前無實際作用。
3. **lines_added / lines_removed 為估算值**：基於 `Write` / `Edit` 工具輸入的字串行數，非 git diff 精確值。
4. **Cursor adapter 資訊較少**：目前僅擷取 bubble text，未解析工具呼叫細節。
5. **語言設定未完全生效**：`language` 欄位存在，但 prompts 已固定為繁體中文。
6. **Auto-detect 順序固定**：Claude Code → Codex CLI → Cursor，無法自訂優先順序。

---

## 12. Future Considerations

- 讓 `preflight` 根據實際 `--source` 檢查對應來源目錄。
- 啟用 `language` 設定，支援多語言輸出。
- 移除或實作 `history_lines`、`output`、`max_files_limit` 保留欄位。
- 加強 Cursor adapter，解析 composer 內的工具呼叫與檔案變更。
- 支援更多輸出目標（例如檔案、GitHub PR 自動發布）。
- 引入可自訂風險規則的設定檔。
