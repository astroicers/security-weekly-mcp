# Security Weekly MCP

MCP Server 架構的資安週報與術語庫管理系統。

## 專案架構

```
security-weekly-mcp/                    # Monorepo (uv workspace)
├── packages/
│   ├── glossary/                       # 術語庫 (Git Submodule)
│   │   ├── src/security_glossary_tw/   # → astroicers/security-glossary-tw
│   │   │   ├── glossary.py            # Glossary 主類
│   │   │   ├── models.py              # Pydantic 資料模型
│   │   │   ├── matcher.py             # TermMatcher - 術語模糊匹配
│   │   │   └── validator.py           # TermValidator - 用詞驗證
│   │   ├── terms/                      # 術語 YAML 檔案 (7 個分類)
│   │   ├── meta/                       # 元資料 (categories, style_guide)
│   │   └── pending/                    # 待審術語
│   │
│   └── mcp-server/                     # MCP Server 套件
│       └── src/security_weekly_mcp/
│           ├── server.py               # MCP Server 主程式
│           ├── __main__.py             # CLI 入口
│           └── tools/                  # MCP 工具模組
│               ├── glossary.py         # 術語庫工具 (6 個)
│               ├── news.py             # 新聞收集工具 (3 個)
│               └── report.py           # 週報工具 (3 個)
│
├── config/                             # 共用配置
│   ├── sources.yaml                    # 13+ 個資料來源設定
│   └── writing_style.yaml              # 寫作風格指南
│
├── templates/typst/                    # Typst 週報模板
│   ├── weekly_report.typ               # 主模板 (需修復語法)
│   └── components/                     # 可重用元件
│
├── output/reports/                     # 產生的週報
│   ├── SEC-WEEKLY-YYYY-WW.json        # 結構化資料
│   ├── SEC-WEEKLY-YYYY-WW.typ         # Typst 原始檔
│   └── SEC-WEEKLY-YYYY-WW.pdf         # PDF 輸出
│
├── pyproject.toml                      # Workspace 配置
└── uv.lock                             # 依賴鎖定
```

## MCP 工具 (13 個)

### 術語庫工具

| 工具 | 功能 | 用途 |
|------|------|------|
| `search_term` | 模糊搜尋術語庫 | 查詢英/中文術語 |
| `get_term_definition` | 取得完整術語定義 | 深入了解術語 |
| `validate_terminology` | 驗證用詞規範 | 檢查禁止用詞 |
| `add_term_links` | 為文本加術語連結 | Markdown/HTML 輸出 |
| `list_pending_terms` | 列出待審術語 | 術語審核流程 |
| `extract_terms` | 從文本自動提取術語 | **週報產生自動填充** |

### 新聞收集工具

| 工具 | 功能 | 資料來源 |
|------|------|----------|
| `fetch_security_news` | 收集資安新聞 | RSS (13+ 來源) |
| `fetch_vulnerabilities` | 收集漏洞資訊 | NVD + CISA KEV |
| `list_news_sources` | 列出新聞來源 | sources.yaml |
| `suggest_searches` | 產生搜尋建議 | search_templates.yaml |

### 週報工具

| 工具 | 功能 | 輸出格式 |
|------|------|----------|
| `generate_report_draft` | 產生週報結構化資料 | JSON |
| `compile_report_pdf` | 編譯 Typst → PDF | PDF |
| `list_reports` | 列出已產生的週報 | 清單 |

## 週報產生完整流程

```
┌─────────────────────────────────────────────────────────────┐
│                    1. 資料收集階段                           │
├─────────────────────────────────────────────────────────────┤
│  fetch_security_news      → 收集 RSS 資安新聞               │
│  fetch_vulnerabilities    → 收集 NVD + CISA KEV 漏洞        │
│                                                             │
│  過濾條件：                                                  │
│  - CVSS ≥ 7.0                                               │
│  - 時間範圍：7 天                                            │
│  - 關鍵字加權：Taiwan, 台灣, 金融, 製造, 政府               │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                   1.5 WebSearch 補充階段                     │
├─────────────────────────────────────────────────────────────┤
│  suggest_searches         → 產生搜尋建議                     │
│                                                             │
│  Claude Code 執行 WebSearch：                                │
│  - site:twcert.org.tw 資安通報                              │
│  - 台灣 資安事件 {year}                                     │
│  - site:informationsecurity.com.tw                          │
│                                                             │
│  Claude Code 執行 WebFetch：                                 │
│  - TWCERT/CC 最新消息                                       │
│  - 數位發展部資安公告                                        │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                    2. 內容整理階段                           │
├─────────────────────────────────────────────────────────────┤
│  Claude AI 分析新聞/漏洞，產生：                             │
│  - 重大資安事件 (events)                                    │
│  - 關鍵漏洞清單 (vulnerabilities)                           │
│  - 威脅趨勢 (threat_trends)                                 │
│  - 行動建議 (action_items)                                  │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                    3. 術語處理階段                           │
├─────────────────────────────────────────────────────────────┤
│  extract_terms            → 自動提取週報中的術語             │
│  validate_terminology     → 檢查用詞是否符合規範             │
│  add_term_links           → 為術語加上連結                   │
│                                                             │
│  輸出：terms[] 陣列（含定義、URL）                          │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                    4. 週報產生階段                           │
├─────────────────────────────────────────────────────────────┤
│  generate_report_draft    → 產生結構化 JSON                  │
│                                                             │
│  report_data = {                                            │
│    title, report_id, period, publish_date,                  │
│    summary: {total_events, total_vulnerabilities, level},   │
│    events[], vulnerabilities[], threat_trends,              │
│    action_items[], terms[], references[]                    │
│  }                                                          │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                    5. PDF 編譯階段                           │
├─────────────────────────────────────────────────────────────┤
│  compile_report_pdf       → 使用 Typst 編譯 PDF              │
│                                                             │
│  依賴：~/.local/bin/typst (v0.12.0+)                        │
│  輸出：output/reports/SEC-WEEKLY-YYYY-WW.pdf                │
└─────────────────────────────────────────────────────────────┘
```

## 術語自動提取設計

`extract_terms` 工具會：
1. 使用 `Glossary.find_terms(text)` 掃描文本
2. 識別術語庫中已收錄的術語
3. 去重並保留出現順序
4. 回傳 JSON 格式的術語列表

```json
[
  {
    "term": "進階持續性威脅",
    "term_en": "APT",
    "term_zh": "進階持續性威脅",
    "definition": "國家級駭客組織發動的長期網路攻擊",
    "id": "apt",
    "url": "https://astroicers.github.io/security-glossary-tw/glossary/apt"
  }
]
```

## 關鍵風格規則

遵循 `packages/glossary/meta/style_guide.yaml`：

| 禁止用詞 | 正確用詞 |
|----------|----------|
| 黑客 | 駭客 |
| 病毒 | 惡意程式 |
| 軟體 | 軟體 |
| 資訊 | 資訊 |
| 認證 | 驗證 (身份驗證) |
| 木馬 | 特洛伊木馬程式 |
| 暴力破解 | 暴力攻擊 |

## 開發指令

```bash
# 安裝依賴
uv sync

# 測試 MCP Server
uv run --package security-weekly-mcp-server python -c \
  "from security_weekly_mcp.server import app; print(app.name)"

# 啟動 MCP Server (stdio 模式)
uv run --package security-weekly-mcp-server python -m security_weekly_mcp.server

# 開發模式 (MCP Inspector)
uv run --package security-weekly-mcp-server mcp dev \
  packages/mcp-server/src/security_weekly_mcp/server.py

# 執行測試
uv run pytest

# 直接執行工具 (範例)
uv run python -c "
import asyncio
from security_weekly_mcp.tools import glossary
asyncio.run(glossary.call_tool('search_term', {'query': 'APT'}))
"
```

## Claude Code MCP 設定

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

## 相關專案

| 專案 | 位置 | 狀態 | 用途 |
|------|------|------|------|
| security-glossary-tw | `../security-glossary-tw/` | 活躍 | 術語庫獨立倉庫 |
| security-weekly-report | `../security-weekly-report/` | 封存 | 歷史週報 (功能遷至 Skill) |
| Claude Code Skill | `~/.claude/skills/security-weekly-tw/` | 活躍 | 自然語言介面 |

## 術語庫同步機制

`packages/glossary/` 是 Git Submodule，指向 `astroicers/security-glossary-tw`。

**更新術語庫：**
```bash
git submodule update --remote packages/glossary
```

**初始化 (clone 後)：**
```bash
git submodule update --init --recursive
```

**CI/CD 自動處理：** `.github/workflows/ci.yml` 已設定 `submodules: recursive`

## 已知問題

1. **BleepingComputer RSS** - 使用 Cloudflare 防護，已在 `sources.yaml` 標記為 `status: disabled`

## 新聞來源 (sources.yaml)

| 類別 | 來源 | 優先級 | 狀態 |
|------|------|--------|------|
| 國際新聞 | The Hacker News, Krebs on Security, SecurityWeek, Dark Reading | high | ✅ |
| 台灣新聞 | iThome 資安 | high | ✅ |
| 台灣官方 | TWCERT/CC, 資安人 | critical/medium | 手動 |
| 官方公告 | CISA Alerts, CISA KEV | critical | ✅ |
| 漏洞資料 | NVD, GitHub Advisories | high | ✅ |
| 威脅情報 | Mandiant, Microsoft Security | high | ✅ |
| 廠商公告 | Microsoft MSRC | high | ✅ |

**註：** 部分台灣來源 (TWCERT/CC, 資安人) 無可用 RSS，需手動收集或 web scraping。
