# Security Weekly MCP

MCP Server 架構的資安週報與術語庫管理系統，專為台灣資安社群設計。

## 功能特色

- **32 個資安來源** - 自動收集國際與台灣資安新聞（並行抓取優化）
- **兩階段週報架構** - GitHub Actions 保存原始資料，Claude 分析產生高品質報告
- **WebSearch/WebFetch 整合** - 透過 Claude Code 補充 RSS 無法取得的資訊
- **歷史週報支援** - 可產生任意時間範圍的歷史報告
- **術語庫整合** - 自動提取並標註資安術語 (437+ 個術語)
- **術語審核工具** - 批准/拒絕待審術語的完整工作流程
- **HTML 週報** - 透過 GitHub Pages 發布的線上週報
- **安全審計** - CI 整合 pip-audit 自動檢測依賴漏洞
- **健康檢查** - 每月自動驗證 RSS 來源可用性

## 快速開始

### 1. 安裝依賴

```bash
git clone --recursive https://github.com/your-repo/security-weekly-mcp.git
cd security-weekly-mcp
uv sync
```

### 2. 設定 Claude Code MCP

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

### 3. 產生週報

在 Claude Code 中輸入：

```
產生本週資安週報
```

---

## 週報產生架構

本系統採用**兩階段架構**，解決 RSS 資料揮發性問題：

```
┌──────────────────────────────────────────────────────────────────────┐
│                    階段 1：自動資料收集                               │
│                    (GitHub Actions 每週一自動執行)                    │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  weekly-collect.yml (週一 09:00 UTC+8)                              │
│       │                                                              │
│       ▼                                                              │
│  collect_weekly_data.py                                             │
│       │                                                              │
│       ├─ fetch_security_news    → 32 個 RSS 來源 (並行抓取)         │
│       ├─ fetch_vulnerabilities  → NVD + CISA KEV                    │
│       └─ suggest_searches       → 搜尋查詢建議                       │
│       │                                                              │
│       ▼                                                              │
│  output/raw/YYYY-WNN.json  ← Git 自動提交保存                       │
│                                                              │
└──────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌──────────────────────────────────────────────────────────────────────┐
│                    階段 2：智慧報告產生                               │
│                    (使用者說「產生週報」時執行)                        │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  load_weekly_data           → 載入已保存的原始資料                   │
│       │                                                              │
│       ▼                                                              │
│  Claude 分析 + WebSearch 補充                                        │
│       │                                                              │
│       ├─ 分析新聞趨勢                                                │
│       ├─ 執行建議搜尋查詢                                            │
│       ├─ extract_terms        → 提取術語                             │
│       └─ validate_terminology → 驗證用詞                             │
│       │                                                              │
│       ▼                                                              │
│  generate_report_draft      → JSON 結構化資料                        │
│       │                                                              │
│       ▼                                                              │
│  output/reports/SEC-WEEKLY-YYYY-WW.json                             │
│  deploy-rss.yml → HTML 頁面發布至 GitHub Pages                       │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

### 方式一：透過 Claude Code (推薦)

```
# 使用已保存的資料產生週報
產生本週資安週報

# 查看可用的週報資料
列出已收集的週報資料

# 產生歷史週報
產生 2026-W05 的週報
```

### 方式二：手動資料收集 + 報告產生

```bash
# 1. 手動收集資料 (如果 GitHub Actions 未執行)
uv run python scripts/collect_weekly_data.py --days 7

# 2. 之後在 Claude Code 中說「產生週報」
```

### 歷史週報

對於已過期的 RSS 資料，系統會：
1. 使用 `suggest_searches` 產生帶時間過濾的搜尋查詢
2. 透過 WebSearch 搜尋歷史資料
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
│               ├── glossary.py      # 術語庫工具 (8 個)
│               ├── news.py          # 新聞收集工具 (6 個)
│               └── report.py        # 週報工具 (3 個)
│
├── skill/                           # Claude Code Skill
│   └── SKILL.md                     # 自然語言介面定義
│
├── config/
│   ├── sources.yaml                 # 32 個資料來源設定
│   ├── search_templates.yaml        # WebSearch 查詢模板
│   └── writing_style.yaml           # 寫作風格指南
│
├── scripts/
│   ├── collect_weekly_data.py       # 資料收集腳本 (階段 1)
│   └── generate_weekly_report.py    # 直接產生週報 (傳統模式)
│
├── output/
│   ├── raw/                         # 原始資料 (GitHub Actions 自動提交)
│   │   └── YYYY-WNN.json            # 週報原始資料
│   └── reports/                     # 產生的週報
│       └── SEC-WEEKLY-YYYY-WW.json  # 結構化資料
│
└── .github/workflows/
    ├── ci.yml                       # CI 測試 + 安全審計
    ├── weekly-collect.yml           # 每週一自動收集資料
    ├── weekly-reminder.yml          # 每週五提醒 Issue
    └── monthly-health.yml           # 每月 RSS 健康檢查
```

---

## MCP 工具清單 (16 個)

### 術語庫工具 (8 個)

| 工具 | 功能 | 用途 |
|------|------|------|
| `search_term` | 模糊搜尋術語庫 | 查詢英/中文術語 |
| `get_term_definition` | 取得完整術語定義 | 深入了解術語 |
| `validate_terminology` | 驗證用詞規範 | 檢查禁止用詞 |
| `add_term_links` | 為文本加術語連結 | Markdown/HTML 輸出 |
| `list_pending_terms` | 列出待審術語 | 術語審核流程 |
| `extract_terms` | 從文本自動提取術語 | 週報產生自動填充 |
| `approve_pending_term` | 批准待審術語 | 移至正式術語庫 |
| `reject_pending_term` | 拒絕待審術語 | 刪除待審檔案 |

### 新聞收集工具 (6 個)

| 工具 | 功能 | 資料來源 |
|------|------|----------|
| `fetch_security_news` | 收集資安新聞 (並行) | RSS (32 個來源) |
| `fetch_vulnerabilities` | 收集漏洞資訊 | NVD + CISA KEV |
| `list_news_sources` | 列出新聞來源 | sources.yaml |
| `suggest_searches` | 產生搜尋建議 | search_templates.yaml |
| `list_weekly_data` | 列出已保存週報資料 | output/raw/ |
| `load_weekly_data` | 載入指定週的資料 | output/raw/YYYY-WNN.json |

### 週報工具 (2 個)

| 工具                     | 功能               | 輸出格式 |
|--------------------------|--------------------| -------- |
| `generate_report_draft`  | 產生週報結構化資料 | JSON     |
| `list_reports`           | 列出已產生的週報   | 清單     |

---

## 資料來源 (32 個)

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
- **pip-audit 安全審計** - 檢測依賴套件漏洞

### 週報資料收集 (weekly-collect.yml)

- **每週一 09:00 (台灣時間)** 執行
- 收集 RSS 新聞、NVD/KEV 漏洞
- 保存原始 JSON 至 `output/raw/`
- Git 自動提交並推送
- 支援手動觸發 (workflow_dispatch)

### 週報提醒 (weekly-reminder.yml)

- **每週五 09:00 (台灣時間)** 執行
- 建立 GitHub Issue 提醒產生週報
- 列出本週收集的資料統計

### RSS 健康檢查 (monthly-health.yml)

- **每月 1 日** 執行
- 驗證所有 RSS 來源可用性
- 產生健康報告至 GitHub Summary

---

## LINE Notify 整合

當週報部署到 GitHub Pages 時，自動發送 LINE 通知給訂閱者。

### 設定步驟

1. **建立 LINE Notify 服務**
   - 前往 [LINE Notify](https://notify-bot.line.me/my/)
   - 點擊「產生權杖」
   - 選擇要接收通知的聊天室（個人或群組）
   - 複製產生的 Access Token

2. **設定 GitHub Secret**
   - 前往專案的 Settings > Secrets and variables > Actions
   - 點擊「New repository secret」
   - Name: `LINE_NOTIFY_TOKEN`
   - Value: 貼上步驟 1 取得的 Access Token

3. **完成！** 之後每次週報發布時，LINE 會自動收到通知：

```text
📰 台灣資安週報 2026-W08 已發布

本週摘要：
• 3 起資安事件
• 5 個高風險漏洞
• 威脅等級：中

閱讀完整報告：
https://astroicers.github.io/security-glossary-tw/weekly/reports/SEC-WEEKLY-2026-W08.html
```

### 手動發送測試

```bash
# 設定環境變數
export LINE_NOTIFY_TOKEN="your-token-here"

# 預覽訊息（不實際發送）
uv run python scripts/notify_line.py --latest --dry-run

# 發送通知
uv run python scripts/notify_line.py --latest
```

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
