# Spotlight Review

把 Claude / Codex / Cursor 的 agent session 轉成可審計的繁中交接報告：做了什麼、風險是什麼、下一步該做什麼。

## 功能

- 啟動前護欄：檢查 git repo、OPENAI_API_KEY、session 目錄與單一 session 大小上限
- 自動偵測或手動指定 AI coding session 來源（Claude Code / Codex CLI / Cursor）
- 透過 `agents/sources/` 的統一 adapter 介面收集與轉換 session 資料
- 解析 session 事件：讀取/修改的檔案、執行的 bash 指令、工具呼叫次數、對話輪數、session 時長
- 規則式風險標記：`risk_flag()` 根據敏感路徑、破壞性指令、權限提升、範圍外存取等產生 flags
- 風險審計：`audit()` 檢查 high risk session 的 LLM 摘要是否遺漏風險
- 使用 OpenAI 模型產生 agent 行為摘要
- 輸出結構化的 Markdown 報告（Summary / Changes / Risks / Next Actions / Questions / Files Touched）
- 執行日誌：每次執行狀態寫入 `~/.spotlight/runs.jsonl`
- 週統計：`spotlight --stats` 顯示最近 7 天執行概況

## Data handling

Spotlight 的設計原則是：**你的 session 內容盡量留在本機，能少送就少送**。

### 讀取哪些本機檔案

只讀取各 AI coding 工具寫在本機的 session log，不讀取原始程式碼內容：

- **Claude Code**：`~/.claude/projects/**/*.jsonl`
- **Codex CLI**：`~/.codex/sessions/**/*.jsonl`
- **Cursor**：`~/Library/Application Support/Cursor/User/workspaceStorage/**/state.vscdb`（macOS）或 `~/.config/Cursor/User/workspaceStorage/**/state.vscdb`（Linux）

### 傳送哪些內容到 LLM

`summarize()` 前**不會**傳送完整原始 session log。只會傳送結構化後的摘要欄位：

- 讀取/修改的檔案路徑（`files_read`、`files_written`）
- 前 20 條 bash 指令（`bash_commands`）
- 工具呼叫次數、對話輪數、session 時長
- `risk_flag()` 產生的風險等級與標記項目
- 前 5 則 assistant 訊息節錄（每則最多 500 字元）

### 遮罩與注意事項

- Spotlight **不會主動遮罩 credential、token 或密碼**。如果你的 bash 指令或 assistant 訊息中含有敏感值，它們仍可能隨著上述欄位被傳送。
- 建議在執行前先用 `spotlight --dry-run` 查看會被傳送的內容，確認沒有敏感資訊後再跑完整流程。

### 本機保留哪些紀錄

每次執行會寫入 `~/.spotlight/runs.jsonl`，內容僅包含：

- `run_id`（ISO 時間戳）
- 執行狀態：`started` / `running` / `completed` / `failed` / `skipped`
- 目前步驟、`verdict`、`files_changed`、`lines_delta`
- `audit_passed` 與錯誤訊息

**不會**儲存原始 session 內容、檔案路徑、bash 指令或 LLM 原始輸出。

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
spotlight                       # 自動偵測來源，產生完整 Markdown 報告
spotlight --source claude_code  # 指定使用 Claude Code
spotlight --source codex        # 指定使用 Codex CLI
spotlight --source cursor       # 指定使用 Cursor
spotlight --session /path/to/session.jsonl --source claude_code  # 直接指定 session 檔案
spotlight --dry-run             # 執行到解析與風險標記，不呼叫 LLM
spotlight --stats               # 顯示最近 7 天統計
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
source: "auto"                    # 自動偵測來源：auto / claude_code / codex / cursor
model: "gpt-4o-mini"              # 使用的 OpenAI 模型
language: "zh-TW"                 # 輸出語言
claude_session_dir: "~/.claude/projects"  # Claude Code session log 目錄
codex_session_dir: "~/.codex/sessions"    # Codex CLI session log 目錄
cursor_workspace_dir: null        # Cursor workspaceStorage 目錄；null 會依 OS 自動偵測
max_session_lines: 5000           # 單一 session 檔案行數上限
```

`model` 會傳入 `summarize()`，`claude_session_dir` / `codex_session_dir` / `cursor_workspace_dir` 與 `max_session_lines` 會傳入 `preflight()` 與 `collect_session()`，`source` 控制 `collect_session()` 要使用的 adapter。

## 流水線說明

Spotlight 依以下 SOP 順序執行：

1. 初始化 `run_id`
2. `preflight()` — 檢查 git repo、API key、session 目錄與 session 大小；失敗則 exit `1`
3. `collect_session()` — 根據 `source` 設定或自動偵測，呼叫對應的 source adapter 收集最新 session
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

## 輸出範例

```markdown
## Summary

本次 session 針對用戶註冊流程重構：將密碼驗證邏輯從 `views.py` 抽離到 `validators.py`，
並新增 `UserService.register()` 的單元測試。整體範圍明確，變更集中在 auth 模組。

## Changes

- 新增 `app/auth/validators.py`，內含 `validate_password_strength()` 與 `validate_email_format()`。
- 重構 `app/auth/views.py`：移除內嵌驗證邏輯，改呼叫新的 validator functions。
- 更新 `app/auth/services.py` 的 `UserService.register()`，統一使用新 validator。
- 新增 `tests/auth/test_validators.py` 與 `tests/auth/test_services.py` 共 14 個測試案例。
- 執行 `pytest tests/auth/` 確認全部通過。

## Risks

- [WARN] `scope_creep`: Agent 讀取了工作目錄外的檔案：`/Users/alice/.ssh/config`
- [WARN] `permission_escalation`: Agent 使用了需要權限提升的指令：`sudo systemctl restart postgres`

## Next Actions

- [ ] 審閱 `app/auth/views.py` 的重構是否遺漏邊界條件。
- [ ] 確認 `sudo systemctl restart postgres` 是否為必要操作。
- [ ] 檢查 `.ssh/config` 被讀取的原因，必要時移除該次存取權限。

## Questions

- `validators.py` 的錯誤訊息是否已納入 i18n 處理？
- 密碼強度規則是否與現行資安政策一致？

## Files Touched

- `app/auth/validators.py` (written)
- `app/auth/views.py` (written)
- `app/auth/services.py` (written)
- `tests/auth/test_validators.py` (written)
- `tests/auth/test_services.py` (written)

468++ / 192-- across 5 file(s)
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
│   ├── sources/           # 各 AI 工具的 source adapter
│   │   ├── base.py        # 統一 adapter 介面 BaseSourceAdapter
│   │   ├── claude_code.py # Claude Code adapter
│   │   ├── codex_cli.py   # Codex CLI adapter
│   │   └── cursor.py      # Cursor adapter
│   ├── collect_session.py # 來源分發器：自動偵測或依設定呼叫 adapter
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

## 疑難排解

### 安裝時出現 `fatal: not a git repository`

如果執行一鍵安裝指令後看到：

```text
[spotlight] Updating existing installation...
fatal: not a git repository (or any of the parent directories): .git
```

表示 `~/.spotlight` 目錄已經存在，但它不是一個 Git 倉庫。最簡單的解決方式是刪除現有目錄後重新安裝：

```bash
rm -rf ~/.spotlight
curl -sSL https://raw.githubusercontent.com/nicklai12/spotlight-review/main/install.sh | bash
```

## 注意事項

- 需要在 git repository 內執行。
- `source: "auto"` 會依以下順序偵測：Claude Code（`~/.claude/projects/` 有 `.jsonl`）→ Codex CLI（`~/.codex/sessions/` 有 `.jsonl`）→ Cursor（workspace DB 存在）。
- 單一 session 檔案行數超過 `max_session_lines` 時，`preflight()` 會失敗。
- session 包含 migration/schema 路徑或大量檔案時，`triage()` 會建議 `skip` 或 `warn`。
- `lines_added` / `lines_removed` 是從 `Write` / `Edit` 工具輸入估算的近似值，不是 git diff 精確值。
- 摘要品質取決於所選模型與 session 內容。
- 請勿將 `OPENAI_API_KEY` 直接寫入程式碼或設定檔。
