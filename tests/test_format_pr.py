"""Tests for PR and handoff formatters."""

import pytest

from agents.format import format_handoff, format_pr


MOCK_SUMMARY = {
    "summary": (
        "本次 session 中，agent 協助重構了 src/utils.py，"
        "將重複的日期格式化與 slug 處理邏輯提取為獨立輔助函式，"
        "並新增 src/helpers.py 模組以集中共用功能。"
    ),
    "changes": [
        "重構 src/utils.py，將重複的 format_timestamp 與 slugify 邏輯提取為輔助函式引用，減少程式碼重複。",
        "新增 src/helpers.py，集中放置 format_timestamp 與 slugify 兩個可共用的輔助函式。",
        "更新 tests/test_utils.py 的測試案例，改為從 src.helpers 匯入輔助函式並驗證 batch_process 行為。",
        "執行 python -m pytest tests/ 驗證所有測試通過。",
    ],
    "risks": [
        "⚠️ [warn] sensitive_path：agent 執行了 cat ~/.ssh/config，讀取 SSH 設定檔，可能洩漏主機別名、使用者名稱或金鑰路徑等敏感資訊。"
    ],
    "next_actions": [
        "確認 cat ~/.ssh/config 的存取是否為開發者授權，必要時輪換相關 SSH 金鑰。",
        "為 src/helpers.py 的輔助函式補充更完整的單元測試，例如非 ASCII 字元與多個連續空白的 slugify 處理。",
    ],
    "questions": [
        "cat ~/.ssh/config 的讀取是 agent 誤觸，還是開發者主動要求的操作？"
    ],
    "files_touched": ["src/utils.py", "src/helpers.py", "tests/test_utils.py"],
}

MOCK_PARSE = {
    "files_written": ["src/utils.py", "src/helpers.py", "tests/test_utils.py"],
}


def test_format_pr_contains_all_sections():
    output = format_pr(MOCK_SUMMARY, MOCK_PARSE, None)
    expected_headings = [
        "## Summary",
        "## Changes",
        "## Risk Flags 🚩",
        "## Reviewer Checklist ✅",
        "## Open Questions ❓",
    ]
    for heading in expected_headings:
        assert heading in output


def test_format_pr_risk_flags_with_critical():
    risk_output = {
        "risk_level": "critical",
        "flags": [
            {
                "severity": "critical",
                "category": "sensitive_path",
                "detail": "Agent 讀取了 ~/.ssh/config",
            }
        ],
    }
    output = format_pr(MOCK_SUMMARY, MOCK_PARSE, risk_output)
    assert "🔴" in output


def test_format_pr_no_risk_shows_default_message():
    output = format_pr(MOCK_SUMMARY, MOCK_PARSE, None)
    assert "_No significant risks identified._" in output


def test_format_handoff_contains_all_sections():
    output = format_handoff(MOCK_SUMMARY, MOCK_PARSE, None)
    expected_headings = [
        "## 🎯 這次在做什麼",
        "## ✅ 已完成的事情",
        "## ⚠️ 需要注意的風險",
        "## 📋 待辦清單",
        "## ❓ 未解決的問題",
        "## 📁 涉及的檔案",
    ]
    for heading in expected_headings:
        assert heading in output
