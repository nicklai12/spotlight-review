# Spotlight Review

Spotlight Review 是一個命令列工具，用來自動摘要最近的 Claude Code session。它會讀取 `~/.claude/projects/` 下的 session log（`.jsonl`），透過 LLM 產生繁體中文的 agent 行為報告，並以 Markdown 格式輸出。

## 功能

- 啟動前護欄：檢查 git repo、OPENAI_API_KEY、Claude session 目錄與單一 session 大小上限
- 自動收集最新的 Claude Code session log
- 解析 session 事件：讀取/修改的檔案、執行的 bash 指令、工具呼叫次數、對話輪數、session 時長
- 規則式風險標記：`risk_flag()` 根據敏感路徑、破壞性指令、權限提升、範圍外存取等產生 flags
- 風險審計：`audit()` 檢查 high risk session 的 LLM 摘要是否遺漏風險
- 使用 OpenAI 模型產生 agent 行為摘要
- 輸出結構化的 Markdown 報告（Summary / Changes / Risks / Next Actions / Questions / Files Touched）
- 執行日誌：每次執行狀態寫入 `~/.spotlight/runs.jsonl`
- 週統計：`spotlight --stats` 顯示最近 7 天執行概況

## 安裝

一鍵安裝：

```bash
curl -sSL https://raw.githubusercontent.com/nicklai12/spotlight-review/main/install.sh | bash
```

安裝後設定 API key：

```bash
export OPENAI_API_KEY=your_key_here
```

然後在任意 git repo 執行：

```bash
spotlight           # 產生完整 Markdown 報告
spotlight --dry-run # 執行到解析與風險標記，不呼叫 LLM
spotlight --stats   # 顯示最近 7 天統計
```

## 使用方法

### 設定 API Key

Spotlight 需要 OpenAI API key：

```bash
export OPENAI_API_KEY="sk-..."
```

### 執行完整流水線

在任意 git repo 內執行：

```bash
spotlight
```

輸出會以 Markdown 格式印到 `stdout`。

### 僅執行收集、解析與風險標記（不呼叫 LLM）

```bash
spotlight --dry-run
```

這會印出解析後的 JSON，方便檢查資料是否正確。

### 查看最近 7 天統計

```bash
spotlight --stats
```

輸出範例：

```text
Spotlight — Last 7 Days
───────────────────────
Total runs:       12
Completed:        9
Failed:           2
Skipped:          1
Audit pass rate:  100%
Avg files/run:    4.2
Common failure:   None
```

## 設定檔

`spotlight.config.yaml` 控制工具行為：

```yaml
model: "gpt-4o-mini"              # 使用的 OpenAI 模型
language: "zh-TW"                 # 輸出語言
claude_session_dir: "~/.claude/projects"  # Claude session log 目錄
max_session_lines: 5000           # 單一 session 檔案行數上限
```

目前 `model` 會傳入 `summarize()`，`claude_session_dir` 與 `max_session_limit` 會傳入 `preflight()`，其他欄位保留給未來擴充。

## 流水線說明

Spotlight 依以下 SOP 順序執行：

1. 初始化 `run_id`
2. `preflight()` — 檢查 git repo、API key、Claude session 目錄與 session 大小；失敗則 exit `1`
3. `collect_session()` — 收集最新的 Claude Code session log
4. `parse_events()` — 解析 session 事件，產出 Schema 2（含 `files_read`、`files_written`、`bash_commands` 等）與相容用的 Schema 1（`files_changed`、`lines_added`、`lines_removed`）
5. `triage()` — 評估複雜度，產生 `auto` / `warn` / `skip` 建議
   - `skip`：印出原因並以 exit `0` 結束（非錯誤）
   - `warn`：繼續執行，最終輸出會附加警告橫幅
6. `--dry-run` 時到此結束並輸出 JSON
7. `risk_flag()` — 規則式掃描敏感路徑與高風險指令，產出 `risk_level` 與 `flags`
   - 若 `risk_level == "high"`，會在 `stderr` 印出 ⚠️ 警告，但不中斷流程
8. `summarize()` — 把 `parse_output` 與 `risk_output` 送進 LLM，產生 JSON，欄位包含 `summary`、`changes`、`risks`、`next_actions`、`questions`、`files_touched`
9. `audit()` — 驗證必填欄位、比對 `files_touched` 與實際檔案防幻覺、檢查 `changes` 項目品質，並確認 high risk session 的 `risks` 不為空
10. `format_output()` — 格式化為 Markdown

每個關鍵步驟都會透過 `log_run()` 寫入 `~/.spotlight/runs.jsonl`。任何非預期失敗都會印出錯誤訊息到 `stderr`，並以 exit code `1` 結束。

## 輸出格式

最終 Markdown 報告包含以下區塊：

- **Summary** – 整個 session 的簡短概述
- **Changes** – agent 具體執行的操作
- **Risks** – 根據 `risk_flag` 標記的潛在風險
- **Next Actions** – 建議的後續行動
- **Questions** – 仍待釐清的問題
- **Files Touched** – agent 讀取或修改的檔案路徑

文末會附上統計：`{lines_added}++ / {lines_removed}-- across {files_changed} file(s)`。

若 triage 建議為 `warn`，輸出頂部會插入：

```markdown
> ⚠️  Large or complex diff. Summary may be incomplete.
```

## 開發與測試

```bash
python -m pytest
```

測試位於 `tests/`，涵蓋 `collect_session`、`parse_events`、`risk_flag`、`summarize`、`audit`、`preflight`、`triage`、`logger` 等 agent。

## 專案結構

```
spotlight-review/
├── agents/                # 各階段 agent（不應在此寫控制邏輯）
│   ├── collect_session.py # 收集最新 Claude Code session log
│   ├── parse_events.py    # 解析 session 事件
│   ├── risk_flag.py       # 規則式風險標記
│   ├── summarize.py       # LLM 摘要
│   ├── audit.py           # 摘要與風險一致性稽核
│   ├── format.py          # Markdown 格式化
│   ├── preflight.py       # 啟動前護欄
│   ├── triage.py          # 複雜度評估
│   ├── logger.py          # 執行日誌與週統計
│   ├── collect.py         # （legacy）git diff 收集，已不使用
│   └── parse.py           # （legacy）diff 解析，已不使用
├── tests/                 # 單元測試
├── fixtures/              # 測試用 session 資料
├── spotlight.py           # CLI 入口與流水線控制
├── spotlight.config.yaml  # 設定檔
├── requirements.txt       # 相依套件
└── install.sh             # 一鍵安裝腳本
```

## 注意事項

- 需要在 git repository 內執行。
- 單一 session 檔案行數超過 `max_session_lines` 時，`preflight()` 會失敗。
- session 包含 migration/schema 路徑或大量檔案時，`triage()` 會建議 `skip` 或 `warn`。
- `lines_added` / `lines_removed` 是從 `Write` / `Edit` 工具輸入估算的近似值，不是 git diff 精確值。
- 摘要品質取決於所選模型與 session 內容。
- 請勿將 `OPENAI_API_KEY` 直接寫入程式碼或設定檔。
