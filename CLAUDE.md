# Security Weekly MCP

MCP Server 架構的資安週報與術語庫管理系統。

## 專案結構

```
security-weekly-mcp/
├── packages/
│   ├── glossary/         # 術語庫 (security-glossary-tw)
│   │   ├── src/
│   │   ├── terms/        # 術語 YAML 檔案
│   │   ├── meta/         # 分類定義
│   │   └── pending/      # 待審術語
│   │
│   └── mcp-server/       # MCP Server
│       └── src/security_weekly_mcp/
│           ├── server.py # 主程式
│           └── tools/    # MCP 工具
│               ├── glossary.py
│               ├── news.py
│               └── report.py
│
├── config/               # 共用配置
│   ├── sources.yaml      # 資料來源
│   └── writing_style.yaml
│
├── templates/typst/      # Typst 模板
│   ├── weekly_report.typ # 主模板
│   └── components/       # 元件
│
└── output/reports/       # 產生的週報
```

## MCP 工具

| 工具 | 功能 |
|------|------|
| `search_term` | 搜尋術語庫 |
| `get_term_definition` | 取得術語定義 |
| `validate_terminology` | 驗證用詞規範 |
| `add_term_links` | 為文本加術語連結 |
| `list_pending_terms` | 列出待審術語 |
| `fetch_security_news` | 收集資安新聞 (RSS) |
| `fetch_vulnerabilities` | 收集漏洞 (NVD + CISA KEV) |
| `list_news_sources` | 列出新聞來源 |
| `generate_report_draft` | 產生週報結構化資料 |
| `compile_report_pdf` | 編譯 Typst → PDF |
| `list_reports` | 列出已產生的週報 |

## 開發指令

```bash
# 安裝依賴
uv sync

# 測試 MCP Server
uv run --package security-weekly-mcp-server python -c "from security_weekly_mcp.server import app; print(app.name)"

# 啟動 MCP Server (開發模式)
uv run --package security-weekly-mcp-server mcp dev packages/mcp-server/src/security_weekly_mcp/server.py

# 執行測試
uv run pytest
```

## Claude Code 設定

在 `~/.claude/mcp_settings.json` 加入：

```json
{
  "mcpServers": {
    "security-weekly-tw": {
      "command": "uv",
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
