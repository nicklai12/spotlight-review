# Spotlight Review — System Map

## Purpose

Spotlight Review 是一個 CLI 工具，用於把 AI coding agent（Claude Code / Codex CLI / Cursor）的 session log 轉換成可審計的繁中交接報告。它強調「session 內容盡量留在本機」，只把結構化摘要送到 LLM 進行生成。

---

## System Context

```mermaid
flowchart TB
    subgraph User["開發者環境"]
        U["使用者"]
        Repo["Git repository\n（執行目錄）"]
    end

    subgraph Spotlight["Spotlight Review"]
        CLI["spotlight.py\nCLI 入口 / 流水線控制"]
        Agents["agents/\n各階段處理模組"]
        Adapters["agents/sources/\nSource Adapter"]
    end

    subgraph LocalData["本機資料"]
        Claude["~/.claude/projects/*.jsonl\nClaude Code session"]
        Codex["~/.codex/sessions/*.jsonl\nCodex CLI session"]
        Cursor["Cursor workspaceStorage\nstate.vscdb"]
        RunsLog["~/.spotlight/runs.jsonl\n執行日誌"]
    end

    subgraph External["外部服務"]
        OpenAI["OpenAI API\n(gpt-4o-mini 等)"]
    end

    subgraph Output["輸出"]
        Stdout["stdout\nMarkdown / PR / Handoff"]
    end

    U -->|執行 spotlight| CLI
    CLI -->|讀取| Agents
    Agents -->|讀取最新 session| Adapters
    Adapters --> Claude
    Adapters --> Codex
    Adapters --> Cursor
    Agents -.->|結構化摘要| OpenAI
    OpenAI -.->|生成摘要| Agents
    CLI -->|寫入| RunsLog
    CLI --> Stdout
    Repo -.->|preflight 驗證 git| CLI
```

---

## Pipeline Data Flow

```mermaid
flowchart LR
    A[啟動] --> B["preflight()\n檢查 git / API key / session 大小"]
    B -->|失敗| Z["exit 1"]
    B --> C["collect_session()\n自動偵測或依 --source 選擇 adapter"]
    C --> D["parse_events()\n解析事件統計"]
    D --> E{"triage()\n複雜度評估"}
    E -->|skip| S["exit 0\n印出原因"]
    E -->|auto / warn| F{"--dry-run?"}
    F -->|是| J["輸出 JSON\n結束"]
    F -->|否| G["risk_flag()\n規則式風險標記"]
    G --> H["summarize()\nLLM 生成摘要"]
    H --> I["audit()\n欄位與風險一致性稽核"]
    I -->|失敗| Z
    I --> K["format_output / format_pr / format_handoff()\n依 --format 格式化"]
    K --> L["stdout 輸出\n寫入 runs.jsonl"]
    E -->|warn| K
    style Z fill:#ffcccc
    style S fill:#fff2cc
```

---

## Component Breakdown

| 元件 | 檔案 | 職責 |
|------|------|------|
| CLI 入口與控制 | `spotlight.py` | 解析 CLI 參數、載入 config、協調流水線、記錄執行狀態 |
| 啟動護欄 | `agents/preflight.py` | 確認在 git repo 內、OPENAI_API_KEY 存在、session 檔案與大小限制 |
| Session 收集器 | `agents/collect_session.py` | 自動偵測來源或依設定分派對應 adapter |
| Source Adapter 介面 | `agents/sources/base.py` | 定義統一 adapter 介面與 Schema 1 輸出 |
| Claude Code Adapter | `agents/sources/claude_code.py` | 讀取 `~/.claude/projects/**/*.jsonl` |
| Codex CLI Adapter | `agents/sources/codex_cli.py` | 讀取 `~/.codex/sessions/**/*.jsonl` |
| Cursor Adapter | `agents/sources/cursor.py` | 讀取 Cursor `state.vscdb` 中的 composer data |
| 事件解析 | `agents/parse_events.py` | 把 Schema 1 轉成 Schema 2：檔案讀寫、bash 指令、統計、風險輸入 |
| 複雜度分類 | `agents/triage.py` | 依檔案數、行數、lockfile、migration/schema 給出 auto/warn/skip 建議 |
| 風險標記 | `agents/risk_flag.py` | 規則式掃描敏感路徑、破壞性指令、權限提升、範圍外存取 |
| LLM 摘要 | `agents/summarize.py` | 把解析結果與風險標記送入 OpenAI，產生 JSON 摘要 |
| 摘要稽核 | `agents/audit.py` | 驗證必填欄位、比對 files_touched 與實際檔案、確認 high risk 有風險描述 |
| 格式化輸出 | `agents/format.py` | 輸出 markdown / pr / handoff 三種格式 |
| 執行日誌 | `agents/logger.py` | 寫入與讀取 `~/.spotlight/runs.jsonl`，支援 `--stats` |
| Legacy（已不使用）| `agents/collect.py` / `agents/parse.py` | 早期基於 git diff 的收集與解析 |

---

## Data Schema 對照

### Schema 1：Source Adapter 輸出（`BaseSourceAdapter.collect`）

```mermaid
classDiagram
    class Schema1 {
        +string session_file
        +list~dict~ session_raw
        +string session_id
        +string timestamp
        +string source_type
    }
```

### Schema 2：parse_events 輸出

```mermaid
classDiagram
    class Schema2 {
        +list files_read
        +list files_written
        +list bash_commands
        +int tool_call_count
        +int estimated_turns
        +int duration_seconds
        +list assistant_messages
        +list files_changed
        +int lines_added
        +int lines_removed
    }
```

### summarize 輸出（LLM JSON）

```mermaid
classDiagram
    class SummaryOutput {
        +string summary
        +list changes
        +list risks
        +list next_actions
        +list questions
        +list files_touched
    }
```

---

## File Map

```
spotlight-review/
├── spotlight.py              # CLI 入口 / 流水線控制
├── spotlight.config.yaml     # 設定檔
├── requirements.txt          # Python 相依
├── install.sh                # 一鍵安裝腳本
├── system-map.md             # 本文檔
├── spec.md                   # 技術規格書
├── agents/
│   ├── sources/              # Source adapter
│   │   ├── base.py
│   │   ├── claude_code.py
│   │   ├── codex_cli.py
│   │   └── cursor.py
│   ├── collect_session.py    # 來源分發器
│   ├── parse_events.py       # 事件解析
│   ├── risk_flag.py          # 規則式風險標記
│   ├── summarize.py          # LLM 摘要
│   ├── audit.py              # 摘要稽核
│   ├── format.py             # 輸出格式化
│   ├── preflight.py          # 啟動護欄
│   ├── triage.py             # 複雜度評估
│   ├── logger.py             # 執行日誌
│   ├── collect.py            # (legacy) git diff 收集
│   └── parse.py              # (legacy) diff 解析
├── tests/                    # 單元測試
└── fixtures/                 # 測試用 session 資料
```

---

## External Dependencies

| 相依 | 用途 |
|------|------|
| `openai` | 呼叫 OpenAI Chat Completions API |
| `pyyaml` | 讀取 `spotlight.config.yaml` |
| `git`（系統指令）| `preflight` 驗證是否在 git repository 內 |
| `python` ≥ 3.10 | 使用 `list[dict]`、`dict \| None` 等語法 |

---

## Trust Boundary

```mermaid
flowchart TB
    subgraph LocalOnly["本機處理，不離開本機"]
        A["讀取 session log"]
        B["parse_events 結構化"]
        C["risk_flag 規則標記"]
        D["audit 一致性檢查"]
    end

    subgraph ToLLM["傳送至 OpenAI"]
        E["files_read / files_written"]
        F["bash_commands 前 20 條"]
        G["工具統計與風險標記"]
        H["assistant_messages 前 5 則節錄"]
    end

    subgraph Persist["本機持久化"]
        I["~/.spotlight/runs.jsonl\n（執行狀態，不含 session 內容）"]
    end

    A --> B --> C --> D
    D --> E
    D --> F
    D --> G
    D --> H
    E --> ToLLM
    F --> ToLLM
    G --> ToLLM
    H --> ToLLM
    D --> I
```

> 注意：Spotlight **不會主動遮罩 credential、token 或密碼**。建議先用 `--dry-run` 確認會送往 LLM 的內容。
