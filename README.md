# Security Weekly MCP

MCP Server 架構的資安週報與術語庫管理系統。

## 專案結構

```
security-weekly-mcp/
├── packages/
│   ├── glossary/         # 術語庫 (security-glossary-tw)
│   └── mcp-server/       # MCP Server
├── config/               # 共用配置
├── templates/typst/      # Typst 模板
└── output/reports/       # 產生的週報
```

## 功能

### MCP 工具

| 工具 | 功能 |
|------|------|
| `search_term` | 搜尋術語庫 |
| `validate_terminology` | 驗證用詞規範 |
| `fetch_security_news` | 收集資安新聞 |
| `fetch_vulnerabilities` | 收集漏洞資訊 |
| `compile_report_pdf` | 產生 PDF 週報 |

## 開發

```bash
# 安裝依賴
uv sync

# 啟動 MCP Server (開發模式)
uv run mcp dev packages/mcp-server/src/security_weekly_mcp/server.py

# 執行測試
uv run pytest
```

## 授權

MIT License
