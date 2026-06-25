# Spotlight Review

Spotlight Review 是一個命令列工具，用來自動摘要目前 git 工作區的變更。它會讀取 `git diff` 與最近的 shell 歷史，透過 LLM 產生繁體中文的變更摘要，並以 Markdown 格式輸出。

## 功能

- 自動收集 `git diff HEAD` 與最近 50 行 shell 歷史
- 解析 diff，取得變更檔案、新增/刪除行數與 diff 片段
- 使用 OpenAI 模型產生變更摘要
- 自動稽核摘要與原始 diff 的一致性
- 輸出結構化的 Markdown 報告

## 安裝

```bash
pip install -r requirements.txt
```

相依套件只有兩個：

- `openai`
- `pyyaml`

## 使用方法

### 設定 API Key

Spotlight 需要 OpenAI API key：

```bash
export OPENAI_API_KEY="sk-..."
```

### 執行完整流水線

在任意 git repo 內執行：

```bash
python spotlight.py
```

輸出會以 Markdown 格式印到 `stdout`。

### 僅執行收集與解析（不呼叫 LLM）

```bash
python spotlight.py --dry-run
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
4. `summarize()` — 呼叫 LLM 產生摘要
5. `audit()` — 檢查摘要內容與 diff 是否一致
6. `format_output()` — 格式化為 Markdown

任何步驟失敗都會印出錯誤訊息到 `stderr`，並以 exit code `1` 結束。

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
└── requirements.txt       # 相依套件
```

## 注意事項

- 需要在 git repository 內執行，且工作區要有變更（`git diff HEAD` 不為空）。
- 摘要品質取決於所選模型與 diff 內容。
- 請勿將 `OPENAI_API_KEY` 直接寫入程式碼或設定檔。
