# SPEC-001：MCP Server 核心功能

| 欄位 | 內容 |
|------|------|
| **SPEC ID** | SPEC-001 |
| **狀態** | Accepted |
| **ADR 關聯** | 無（技術棧選型隨術語庫 ADR-001 一致） |
| **建立日期** | 2026-05-10 |
| **最後更新** | 2026-05-10 |
| **追溯性（Traceability）** | `packages/mcp-server/src/security_weekly_mcp/tools/glossary.py`, `tools/news.py`, `tools/report.py` |

---

## 目標（Goal）

以 Model Context Protocol (MCP) Server 形式，提供 Claude Code 自然語言介面，整合資安週報產生、術語庫管理、資安新聞收集三大功能。

---

## 使用情境（User Stories）

| ID | 角色 | 需求 | 接受條件 |
|----|------|------|---------|
| US-01 | 資安分析師 | 搜尋術語庫 | `search_term(query)` 回傳相符術語清單 |
| US-02 | 資安分析師 | 驗證文稿用詞 | `validate_terminology(text)` 回傳禁止用詞與建議 |
| US-03 | 資安分析師 | 自動收集本週資安新聞 | `fetch_security_news(days=7)` 回傳新聞列表（≥1 筆） |
| US-04 | 資安分析師 | 收集高危漏洞 | `fetch_vulnerabilities(min_cvss=7.0)` 回傳 NVD + KEV 資料 |
| US-05 | 資安分析師 | 產生週報草稿 | `generate_report_draft(...)` 回傳 JSON 結構化週報 |
| US-06 | 術語管理員 | 審核待審術語 | `list_pending_terms()` 列出 pending/；`approve_pending_term(id)` 移至正式術語庫 |
| US-07 | 資安分析師 | 查看歷史收集資料 | `list_weekly_data()` 列出 output/raw/；`load_weekly_data(week)` 載入指定週 |

---

## 介面定義（MCP Tools）

### 術語庫工具（glossary.py）

```
search_term(query: str) -> list[TermResult]
get_term_definition(term_id: str) -> TermDetail
validate_terminology(text: str) -> ValidationReport
add_term_links(text: str, format: "markdown"|"html") -> str
list_pending_terms() -> list[PendingTerm]
extract_terms(text: str) -> list[TermMatch]
approve_pending_term(term_id: str) -> ApproveResult
reject_pending_term(term_id: str) -> RejectResult
```

### 新聞收集工具（news.py）

```
fetch_security_news(days: int, limit: int) -> list[NewsItem]
fetch_vulnerabilities(min_cvss: float, days: int, include_kev: bool) -> VulnReport
list_news_sources() -> list[SourceConfig]
suggest_searches(category: str, period_start?: str, period_end?: str) -> list[SearchQuery]
list_weekly_data() -> list[WeeklyDataMeta]
load_weekly_data(week: str) -> WeeklyRawData
```

### 週報工具（report.py）

```
generate_report_draft(period_start: str, period_end: str, ...) -> ReportDraft
compile_report_pdf(report_id: str) -> PDFResult
list_reports() -> list[ReportMeta]
```

---

## 完成條件（Done When）

- [ ] MCP Server 可以 stdio 模式啟動（`python -m security_weekly_mcp.server`）
- [ ] `search_term` 對存在術語回傳正確結果
- [ ] `fetch_security_news` 可抓取至少 1 個 RSS 來源
- [ ] `generate_report_draft` 回傳含 `period_start`、`period_end`、`events` 的 JSON
- [ ] `approve_pending_term` 將 pending YAML 移至對應 `terms/*.yaml`
- [ ] 所有工具測試通過（`pytest -m "not slow"`）

---

## 測試矩陣

| 測試場景 | 工具 | 輸入 | 預期輸出 | 對應 US |
|---------|------|------|---------|---------|
| 搜尋存在術語 | `search_term` | `"APT"` | 含 `apt` 的結果 | US-01 |
| 搜尋不存在術語 | `search_term` | `"xxxxxxxx"` | 空列表 | US-01 |
| 禁止用詞驗證 | `validate_terminology` | `"黑客入侵"` | `[{word:"黑客", suggestion:"駭客"}]` | US-02 |
| RSS 新聞收集 | `fetch_security_news` | `days=7, limit=5` | 列表長度 ≥ 1 | US-03 |
| 漏洞收集（mock） | `fetch_vulnerabilities` | `min_cvss=9.0` | CVSS ≥ 9.0 的漏洞列表 | US-04 |
| 週報草稿 | `generate_report_draft` | 任意期間 | 含 `period_start` 的 JSON | US-05 |
| 列出待審術語 | `list_pending_terms` | — | 列表（可為空） | US-06 |
| 列出歷史資料 | `list_weekly_data` | — | output/raw/ 中的 JSON 檔列表 | US-07 |

---

## 排除範圍（Out of Scope）

- HTTP/SSE 傳輸模式（目前僅支援 stdio）
- 多用戶認證（單人 Claude Code 工具）
- 歷史週報 PDF 自動重新產生（手動觸發）
