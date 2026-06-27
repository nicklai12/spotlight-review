# Spotlight Review

Spotlight Review 是一個命令列工具，用來自動摘要目前 git 工作區的變更。它會讀取 `git diff` 與最近的 shell 歷史，透過 LLM 產生繁體中文的變更摘要，並以 Markdown 格式輸出。

## 功能

- 自動收集 `git diff HEAD` 與最近 50 行 shell 歷史
- 解析 diff，取得變更檔案、新增/刪除行數與 diff 片段
- 使用 OpenAI 模型產生變更摘要
- 自動稽核摘要與原始 diff 的一致性
- 輸出結構化的 Markdown 報告（Summary / Changes / Risks / Next Actions / Questions）

## 安裝

一鍵安裝：

```bash
curl -sSL https://raw.githubusercontent.com/nicklai12/spotlight-review/v2-five-section-release/install.sh | bash
```

安裝後設定 API key：

```bash
export OPENAI_API_KEY=your_key_here
```

然後在任意 git repo 執行：

```bash
spotlight          # 產生完整 Markdown 報告
spotlight --dry-run # 只執行收集與解析，不呼叫 LLM
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

### 僅執行收集與解析（不呼叫 LLM）

```bash
spotlight --dry-run
```

這會印出解析後的 JSON，方便檢查資料是否正確。

## 設定檔

`spotlight.config.yaml` 控制工具行為：

```yaml
model: "gpt-4o-mini"      # 使用的 OpenAI 模型
language: "zh-TW"         # 輸出語言
history_lines: 50         # 讀取的 shell 歷史行數
output: "stdout"          # 輸出目標
```

目前 `model` 會傳入 `summarize()`，其他欄位保留給未來擴充。

## 流水線說明

1. `collect()` — 收集 `git diff` 與 shell 歷史
2. `parse()` — 解析 diff 結構
3. `--dry-run` 時到此結束並輸出 JSON
4. `summarize()` — 呼叫 LLM 產生 JSON，欄位包含 `summary`、`changes`、`risks`、`next_actions`、`questions`、`files_touched`
5. `audit()` — 驗證必填欄位、比對 `files_touched` 與 `files_changed` 防幻覺、檢查 `changes` 項目品質，並確認 diff 有實際行數變更
6. `format_output()` — 格式化為 Markdown

任何步驟失敗都會印出錯誤訊息到 `stderr`，並以 exit code `1` 結束。

## 輸出格式

最終 Markdown 報告包含以下區塊：

- **Summary** – 整個 session 的簡短概述
- **Changes** – 具體的程式碼變更
- **Risks** – 潛在風險或需要注意的地方
- **Next Actions** – 建議的後續行動
- **Questions** – 仍待釐清的問題

文末會附上 diff 統計：`{lines_added}++ / {lines_removed}-- across {files_changed} file(s)`。

## 開發與測試

```bash
python -m pytest
```

測試位於 `tests/`，涵蓋 `collect`、`parse` 與 `audit` 三個 agent。

## 專案結構

```
spotlight-review/
├── agents/                # 各階段 agent（不應在此寫控制邏輯）
│   ├── collect.py
│   ├── parse.py
│   ├── summarize.py
│   ├── audit.py
│   └── format.py
├── tests/                 # 單元測試
├── spotlight.py           # CLI 入口與流水線控制
├── spotlight.config.yaml  # 設定檔
├── requirements.txt       # 相依套件
└── install.sh             # 一鍵安裝腳本
```

## 注意事項

- 需要在 git repository 內執行，且工作區要有變更（`git diff HEAD` 不為空）。
- 摘要品質取決於所選模型與 diff 內容。
- 請勿將 `OPENAI_API_KEY` 直接寫入程式碼或設定檔。
