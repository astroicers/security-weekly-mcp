# Security Weekly MCP

MCP Server 架構的資安週報與術語庫管理系統，專為台灣資安社群設計。

## 功能特色

- **30 個資安來源** - 自動收集國際與台灣資安新聞
- **WebSearch/WebFetch 整合** - 透過 Claude Code 補充 RSS 無法取得的資訊
- **歷史週報支援** - 可產生任意時間範圍的歷史報告
- **術語庫整合** - 自動提取並標註資安術語 (437+ 個術語)
- **PDF 輸出** - 使用 Typst 產生專業排版的 PDF 報告

## 快速開始

### 1. 安裝依賴

```bash
git clone --recursive https://github.com/your-repo/security-weekly-mcp.git
cd security-weekly-mcp
uv sync
```

### 2. 安裝 Typst (產生 PDF 需要)

```bash
curl -fsSL https://typst.community/typst-install/install.sh | sh
```

### 3. 設定 Claude Code MCP

在 `~/.claude/settings.json` 加入：

```json
{
  "mcpServers": {
    "security-weekly-tw": {
      "command": "/home/ubuntu/.local/bin/uv",
      "args": [
        "run",
        "--directory",
        "/path/to/security-weekly-mcp",
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

### 4. 產生週報

在 Claude Code 中輸入：

```
產生本週資安週報
```

---

## 週報產生完整流程

### 方式一：透過 Claude Code (推薦)

```
┌─────────────────────────────────────────────────────────────┐
│                   階段 1：MCP 工具收集                        │
├─────────────────────────────────────────────────────────────┤
│  fetch_security_news    → 收集 32 個 RSS 來源新聞            │
│  fetch_vulnerabilities  → 收集 NVD + CISA KEV 漏洞          │
│  extract_terms          → 自動提取術語庫術語                 │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                   階段 2：WebSearch 補充                      │
├─────────────────────────────────────────────────────────────┤
│  suggest_searches       → 產生搜尋建議                       │
│                                                             │
│  Claude Code 執行 WebSearch：                                │
│  - site:twcert.org.tw 資安通報                              │
│  - 台灣 資安事件 2026                                       │
│  - CVE critical vulnerability 2026                         │
│                                                             │
│  Claude Code 執行 WebFetch：                                 │
│  - TWCERT/CC 最新消息                                       │
│  - 數位發展部資安公告                                        │
│  - 資安人首頁                                               │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                   階段 3：產生報告                            │
├─────────────────────────────────────────────────────────────┤
│  generate_report_draft  → 產生 JSON 結構化資料               │
│  compile_report_pdf     → 使用 Typst 編譯 PDF               │
│                                                             │
│  輸出：output/reports/SEC-WEEKLY-YYYY-WW.pdf               │
└─────────────────────────────────────────────────────────────┘
```

### 方式二：透過腳本 (CI/CD)

```bash
# 產生最近 7 天的週報
uv run python scripts/generate_weekly_report.py --days 7

# 指定輸出目錄
uv run python scripts/generate_weekly_report.py --output-dir ./reports

# 調整 CVSS 門檻
uv run python scripts/generate_weekly_report.py --min-cvss 8.0
```

### 方式三：歷史週報

在 Claude Code 中輸入：

```
產生 2025 年 6 月第一週的資安週報
```

系統會自動：
1. 使用 `suggest_searches` 產生帶時間過濾的搜尋查詢
2. 透過 WebSearch 搜尋歷史資料 (RSS 資料已過期)
3. 整合結果並產生報告

---

## 專案結構

```
security-weekly-mcp/
├── packages/
│   ├── glossary/                    # 術語庫 (Git Submodule)
│   │   ├── src/security_glossary_tw/
│   │   ├── terms/                   # 術語 YAML 檔案 (7 個分類)
│   │   ├── meta/                    # 元資料 (categories, style_guide)
│   │   └── pending/                 # 待審術語
│   │
│   └── mcp-server/                  # MCP Server 套件
│       └── src/security_weekly_mcp/
│           ├── server.py            # MCP Server 主程式
│           └── tools/               # MCP 工具模組
│               ├── glossary.py      # 術語庫工具 (6 個)
│               ├── news.py          # 新聞收集工具 (4 個)
│               └── report.py        # 週報工具 (3 個)
│
├── config/
│   ├── sources.yaml                 # 32 個資料來源設定
│   ├── search_templates.yaml        # WebSearch 查詢模板
│   └── writing_style.yaml           # 寫作風格指南
│
├── templates/typst/                 # Typst 週報模板
│   ├── weekly_report.typ
│   └── components/
│
├── scripts/
│   └── generate_weekly_report.py    # 自動化腳本
│
├── output/reports/                  # 產生的週報
│   ├── SEC-WEEKLY-YYYY-WW.json     # 結構化資料
│   ├── SEC-WEEKLY-YYYY-WW.typ      # Typst 原始檔
│   └── SEC-WEEKLY-YYYY-WW.pdf      # PDF 輸出
│
└── .github/workflows/
    ├── ci.yml                       # CI 測試
    └── weekly-report.yml            # 每週自動產生
```

---

## MCP 工具清單 (13 個)

### 術語庫工具

| 工具 | 功能 | 用途 |
|------|------|------|
| `search_term` | 模糊搜尋術語庫 | 查詢英/中文術語 |
| `get_term_definition` | 取得完整術語定義 | 深入了解術語 |
| `validate_terminology` | 驗證用詞規範 | 檢查禁止用詞 |
| `add_term_links` | 為文本加術語連結 | Markdown/HTML 輸出 |
| `list_pending_terms` | 列出待審術語 | 術語審核流程 |
| `extract_terms` | 從文本自動提取術語 | 週報產生自動填充 |

### 新聞收集工具

| 工具 | 功能 | 資料來源 |
|------|------|----------|
| `fetch_security_news` | 收集資安新聞 | RSS (32 個來源) |
| `fetch_vulnerabilities` | 收集漏洞資訊 | NVD + CISA KEV |
| `list_news_sources` | 列出新聞來源 | sources.yaml |
| `suggest_searches` | 產生搜尋建議 | search_templates.yaml |

### 週報工具

| 工具 | 功能 | 輸出格式 |
|------|------|----------|
| `generate_report_draft` | 產生週報結構化資料 | JSON |
| `compile_report_pdf` | 編譯 Typst → PDF | PDF |
| `list_reports` | 列出已產生的週報 | 清單 |

---

## 資料來源 (30 個)

### 國際資安新聞 (8 個)

| 來源 | 優先級 | 說明 |
|------|--------|------|
| The Hacker News | high | 最受歡迎的資安新聞 |
| Krebs on Security | high | Brian Krebs 調查報導 |
| SecurityWeek | medium | 企業資安新聞 |
| Dark Reading | medium | 深度資安分析 |
| Schneier on Security | high | Bruce Schneier 部落格 |
| Infosecurity Magazine | high | 獲獎資安媒體 |
| CyberScoop | high | 政策與資安新聞 |
| BleepingComputer | disabled | Cloudflare 防護 |

### 台灣來源 (3 個)

| 來源 | 優先級 | 說明 |
|------|--------|------|
| iThome 資安 | high | 台灣 IT 媒體 |
| TWCERT/CC | critical | 台灣 CERT (手動) |
| 資安人 | medium | 台灣資安媒體 (手動) |

### 官方公告 (4 個)

| 來源 | 優先級 | 說明 |
|------|--------|------|
| CISA Alerts | critical | 美國 CISA 公告 |
| CISA KEV | critical | 已知被利用漏洞 |
| CERT/CC Vulnerability Notes | high | 卡內基美隆大學 CERT |
| CIS MS-ISAC Advisories | high | 網際網路安全中心 |

### 漏洞資料庫 (2 個)

| 來源 | 優先級 | 說明 |
|------|--------|------|
| NVD | high | NIST 漏洞資料庫 |
| GitHub Security Advisories | medium | 開源漏洞 |

### 威脅情報 (12 個)

| 來源 | 優先級 | 說明 |
|------|--------|------|
| Mandiant Blog | high | Google 威脅情報 |
| Microsoft Security Blog | high | 微軟安全部落格 |
| Unit 42 | high | Palo Alto 威脅研究 |
| Recorded Future | high | 威脅情報領導者 |
| Check Point Research | high | Check Point 研究 |
| CrowdStrike Blog | high | CrowdStrike 威脅情報 |
| SentinelOne Blog | high | SentinelLabs 研究 |
| Securelist (Kaspersky) | high | 卡巴斯基 GReAT |
| Sophos Blog | medium | Sophos 威脅研究 |
| Google Security Blog | medium | Google 安全部落格 |
| WeLiveSecurity (ESET) | medium | ESET 威脅研究 |
| Elastic Security Labs | medium | Elastic 安全研究 |

### 廠商公告 (1 個)

| 來源 | 優先級 | 說明 |
|------|--------|------|
| Microsoft MSRC | high | 微軟安全回應中心 |

---

## 開發指令

```bash
# 安裝依賴
uv sync

# 執行測試
uv run pytest

# 執行測試 (跳過慢速網路測試)
uv run pytest -m "not slow"

# 測試 MCP Server
uv run --package security-weekly-mcp-server python -c \
  "from security_weekly_mcp.server import app; print(f'MCP Server: {app.name}')"

# 啟動 MCP Server (stdio 模式)
uv run --package security-weekly-mcp-server python -m security_weekly_mcp.server

# 開發模式 (MCP Inspector)
uv run --package security-weekly-mcp-server mcp dev \
  packages/mcp-server/src/security_weekly_mcp/server.py

# 更新術語庫 (Git Submodule)
git submodule update --remote packages/glossary

# 列出新聞來源
uv run python -c "
import asyncio
from security_weekly_mcp.tools import news
result = asyncio.run(news.call_tool('list_news_sources', {}))
print(result[0].text)
"
```

---

## 術語庫同步

`packages/glossary/` 是 Git Submodule，指向 [astroicers/security-glossary-tw](https://github.com/astroicers/security-glossary-tw)。

```bash
# 初始化 (clone 後)
git submodule update --init --recursive

# 更新術語庫
git submodule update --remote packages/glossary
```

CI/CD 已設定 `submodules: recursive`，自動處理。

---

## GitHub Actions

### CI 測試 (ci.yml)

- Python 3.11 / 3.12 矩陣測試
- Ruff 程式碼檢查
- MCP Server 載入測試

### 週報自動產生 (weekly-report.yml)

- 每週一 09:00 (台灣時間) 執行
- 支援手動觸發 (workflow_dispatch)
- 產生 PDF 並上傳為 artifact

---

## 相關專案

| 專案 | 說明 |
|------|------|
| [security-glossary-tw](https://github.com/astroicers/security-glossary-tw) | 術語庫獨立倉庫 |
| [Claude Code Skill](skill/) | 自然語言介面（位於 `skill/` 目錄） |

### Claude Code Skill 設定

Skill 已包含在本專案的 `skill/` 目錄中，使用 symlink 連結：

```bash
# 建立 symlink（如果尚未存在）
ln -s /path/to/security-weekly-mcp/skill ~/.claude/skills/security-weekly-tw
```

---

## 授權

MIT License
