# Spotlight Review

Spotlight Review 是一個命令列工具，用來自動摘要目前 git 工作區的變更。它會讀取 `git diff` 與最近的 shell 歷史，透過 LLM 產生繁體中文的變更摘要，並以 Markdown 格式輸出。

## 功能

- 啟動前護欄：檢查 git repo、OPENAI_API_KEY、diff 規模上限
- 自動收集 `git diff HEAD` 與最近 50 行 shell 歷史
- 解析 diff，取得變更檔案、新增/刪除行數與 diff 片段
- 風險評估：根據檔案數、行數變更、lockfile、migration/schema 判斷 `auto` / `warn` / `skip`
- 使用 OpenAI 模型產生變更摘要
- 自動稽核摘要與原始 diff 的一致性
- 輸出結構化的 Markdown 報告（Summary / Changes / Risks / Next Actions / Questions）
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
spotlight --dry-run # 執行到解析與風險評估，不呼叫 LLM
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

### 僅執行收集、解析與風險評估（不呼叫 LLM）

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
model: "gpt-4o-mini"      # 使用的 OpenAI 模型
language: "zh-TW"         # 輸出語言
history_lines: 50         # 讀取的 shell 歷史行數
output: "stdout"          # 輸出目標
max_files_limit: 50       # diff 涉及檔案數上限
```

目前 `model` 會傳入 `summarize()`，`max_files_limit` 會傳入 `preflight()`，其他欄位保留給未來擴充。

## 流水線說明

Spotlight 依以下 SOP 順序執行：

1. 初始化 `run_id`
2. `preflight()` — 檢查 git repo、API key、diff 規模；失敗則 exit `1`
3. `collect()` — 收集 `git diff` 與 shell 歷史
4. `parse()` — 解析 diff 結構
5. `triage()` — 評估複雜度，產生 `auto` / `warn` / `skip` 建議
   - `skip`：印出原因並以 exit `0` 結束（非錯誤）
   - `warn`：繼續執行，最終輸出會附加警告橫幅
6. `--dry-run` 時到此結束並輸出 JSON
7. `summarize()` — 呼叫 LLM 產生 JSON，欄位包含 `summary`、`changes`、`risks`、`next_actions`、`questions`、`files_touched`
8. `audit()` — 驗證必填欄位、比對 `files_touched` 與 `files_changed` 防幻覺、檢查 `changes` 項目品質，並確認 diff 有實際行數變更
9. `format_output()` — 格式化為 Markdown

每個關鍵步驟都會透過 `log_run()` 寫入 `~/.spotlight/runs.jsonl`。任何非預期失敗都會印出錯誤訊息到 `stderr`，並以 exit code `1` 結束。

## 輸出格式

最終 Markdown 報告包含以下區塊：

- **Summary** – 整個 session 的簡短概述
- **Changes** – 具體的程式碼變更
- **Risks** – 潛在風險或需要注意的地方
- **Next Actions** – 建議的後續行動
- **Questions** – 仍待釐清的問題

文末會附上 diff 統計：`{lines_added}++ / {lines_removed}-- across {files_changed} file(s)`。

若 triage 建議為 `warn`，輸出頂部會插入：

```markdown
> ⚠️  Large or complex diff. Summary may be incomplete.
```

## 開發與測試

```bash
python -m pytest
```

測試位於 `tests/`，涵蓋 `collect`、`parse`、`audit`、`preflight`、`triage`、`logger` 六個 agent。

## 專案結構

```
spotlight-review/
├── agents/                # 各階段 agent（不應在此寫控制邏輯）
│   ├── collect.py
│   ├── parse.py
│   ├── summarize.py
│   ├── audit.py
│   ├── format.py
│   ├── preflight.py       # 啟動前護欄
│   ├── triage.py          # 風險評估
│   └── logger.py          # 執行日誌與週統計
├── tests/                 # 單元測試
├── spotlight.py           # CLI 入口與流水線控制
├── spotlight.config.yaml  # 設定檔
├── requirements.txt       # 相依套件
└── install.sh             # 一鍵安裝腳本
```

## 注意事項

- 需要在 git repository 內執行，且工作區要有變更（`git diff HEAD` 不為空）。
- diff 涉及檔案數超過 `max_files_limit` 時，`preflight()` 會失敗。
- diff 包含 migration/schema 路徑時，`triage()` 會建議 `skip`。
- 摘要品質取決於所選模型與 diff 內容。
- 請勿將 `OPENAI_API_KEY` 直接寫入程式碼或設定檔。
