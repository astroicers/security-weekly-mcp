# Security Weekly MCP

MCP Server 架構的資安週報與術語庫管理系統。

## 專案結構

```
security-weekly-mcp/
├── packages/
│   ├── glossary/         # 術語庫 (437 個術語)
│   │   ├── terms/        # 術語 YAML 檔案
│   │   ├── meta/         # 分類定義
│   │   └── pending/      # 待審術語
│   │
│   └── mcp-server/       # MCP Server
│       └── src/security_weekly_mcp/
│           ├── server.py # 主程式
│           └── tools/    # MCP 工具模組
│
├── config/               # 共用配置
│   ├── sources.yaml      # 資料來源
│   └── writing_style.yaml
│
├── templates/typst/      # Typst 模板（簡約現代風格）
│   ├── weekly_report.typ # 主模板
│   └── components/       # 元件
│
└── output/reports/       # 產生的週報
```

## MCP 工具

共 11 個工具：

### 術語庫工具

| 工具 | 功能 |
|------|------|
| `search_term` | 搜尋術語庫 |
| `get_term_definition` | 取得術語定義 |
| `validate_terminology` | 驗證用詞規範 |
| `add_term_links` | 為文本加術語連結 |
| `list_pending_terms` | 列出待審術語 |

### 新聞收集工具

| 工具 | 功能 |
|------|------|
| `fetch_security_news` | 收集資安新聞 (RSS) |
| `fetch_vulnerabilities` | 收集漏洞 (NVD + CISA KEV) |
| `list_news_sources` | 列出新聞來源 |

### 週報工具

| 工具 | 功能 |
|------|------|
| `generate_report_draft` | 產生週報結構化資料 |
| `compile_report_pdf` | 編譯 Typst → PDF |
| `list_reports` | 列出已產生的週報 |

## 開發

```bash
# 安裝依賴
uv sync

# 測試 MCP Server
uv run --package security-weekly-mcp-server python -c "from security_weekly_mcp.server import app; print(app.name)"

# 啟動 MCP Server
uv run --package security-weekly-mcp-server python -m security_weekly_mcp.server

# 執行測試
uv run pytest
```

## Claude Code 設定

在 `~/.claude/settings.json` 加入：

```json
{
  "mcpServers": {
    "security-weekly-tw": {
      "command": "/home/ubuntu/.local/bin/uv",
      "args": [
        "run",
        "--directory",
        "/home/ubuntu/projects/security-weekly-mcp",
        "--package",
        "security-weekly-mcp-server",
        "python",
        "-m",
        "security_weekly_mcp.server"
      ]
    }
  }
}
```

## 授權

MIT License
