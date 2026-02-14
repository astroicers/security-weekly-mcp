# Security Weekly TW Skill

Claude Code 的資安週報自然語言介面。

## 安裝

使用 symlink 將 skill 連結到 Claude Code：

```bash
ln -s /path/to/security-weekly-mcp/skill ~/.claude/skills/security-weekly-tw
```

## 觸發詞

以下詞彙會自動載入此 Skill：

| 中文 | 英文 |
|------|------|
| 週報 | security report |
| 產生週報 | generate report |
| 術語 | glossary, term |
| 審核 | review |
| 資安新聞 | security news |
| 新增術語 | add term |
| 更新術語 | update term |
| 術語比對 | term matching |

## 功能

### 週報產生

```
產生本週資安週報
產生 2026-W05 的週報
列出已收集的週報資料
```

### 術語管理

```
審核待審術語
搜尋「APT」術語
新增術語：Salt Typhoon
```

### 新聞收集

```
收集最近 7 天的資安新聞
列出新聞來源
```

## 可用工具

此 Skill 可調用 17 個 MCP 工具：

### 術語庫 (8)
- `search_term` - 搜尋術語
- `get_term_definition` - 取得術語定義
- `validate_terminology` - 驗證用詞
- `add_term_links` - 加入術語連結
- `list_pending_terms` - 列出待審術語
- `extract_terms` - 提取術語
- `approve_pending_term` - 批准術語
- `reject_pending_term` - 拒絕術語

### 新聞 (6)
- `fetch_security_news` - 收集新聞
- `fetch_vulnerabilities` - 收集漏洞
- `list_news_sources` - 列出來源
- `suggest_searches` - 建議搜尋
- `list_weekly_data` - 列出週報資料
- `load_weekly_data` - 載入週報資料

### 週報 (3)
- `generate_report_draft` - 產生草稿
- `compile_report_pdf` - 編譯 PDF
- `list_reports` - 列出報告

## 兩階段週報架構

```
階段 1: GitHub Actions 自動收集
    weekly-collect.yml (每週一)
           │
           ▼
    output/raw/YYYY-WNN.json

階段 2: 使用者觸發產生
    「產生週報」
           │
           ▼
    load_weekly_data → Claude 分析 → PDF
```

## 相關檔案

- [SKILL.md](SKILL.md) - 完整 Skill 定義
- [references/](references/) - 參考資料

## 相依

- MCP Server: `security-weekly-mcp-server`
- Glossary: `security-glossary-tw` (submodule)
