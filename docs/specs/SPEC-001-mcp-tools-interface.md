# SPEC-001: MCP 工具介面規格

| 欄位 | 內容 |
|------|------|
| **狀態** | `Accepted` |
| **日期** | 2026-05-11 |
| **關聯 ADR** | ADR-001 |
| **負責模組** | `packages/mcp-server/src/security_weekly_mcp/tools/` |

---

## Goal（目標）

定義 security-weekly-mcp 所有 MCP 工具的介面規格，包含：命名慣例、輸入參數格式、回傳結構、錯誤行為。確保工具介面穩定，為術語庫管理、新聞收集、週報生成提供一致的協議。

---

## Done When（完成條件）

- [ ] 所有 15 個工具均符合本 SPEC 定義的命名慣例與回傳格式
- [ ] 每個工具呼叫失敗時回傳錯誤訊息而非拋出未捕捉例外
- [ ] `list_tools()` 回傳的工具數量 ≥ 14

---

## 介面慣例

### 命名規則

- 工具名稱使用 `snake_case`
- 動詞前置：`get_`、`search_`、`list_`、`create_`、`approve_`、`reject_`、`fetch_`、`generate_`、`validate_`、`add_`、`extract_`、`suggest_`

### 回傳格式

所有工具回傳 `list[TextContent]`，其中 `TextContent.text` 為 JSON 字串：

```json
{
  "status": "ok" | "error",
  "data": { ... }
}
```

錯誤時：
```json
{
  "status": "error",
  "message": "說明原因"
}
```

---

## 工具清單與規格

### 術語庫工具（glossary.py）

#### `search_term`
- **輸入**：`{ "query": string }` — 英文或中文術語關鍵字
- **回傳**：匹配術語清單，每項含 `id`、`term_en`、`term_zh`、`brief_definition`

#### `get_term_definition`
- **輸入**：`{ "term_id": string }` — 術語 ID（如 `apt`）
- **回傳**：完整術語物件，含 `definition`、`url`、`aliases`

#### `validate_terminology`
- **輸入**：`{ "text": string }` — 待驗證的文本
- **回傳**：違規用詞清單，每項含 `found`（錯誤用詞）、`correct`（正確用詞）、`context`

#### `add_term_links`
- **輸入**：`{ "text": string, "format": "markdown" | "html" }` — 文本與輸出格式
- **回傳**：術語已加連結的文本

#### `list_pending_terms`
- **輸入**：無必填參數
- **回傳**：待審術語清單，每項含 `id`、`term_en`、`term_zh`、`status`

#### `extract_terms`
- **輸入**：`{ "text": string }` — 週報文本
- **回傳**：已識別術語清單，每項含 `term`、`term_en`、`term_zh`、`definition`、`id`、`url`

#### `create_pending_term`
- **輸入**：`{ "term_id": string, "term_en": string, "term_zh": string, "brief_definition": string, "category": string }`
- **限制**：`brief_definition` ≤ 30 字元；`term_id` 在正式庫與 pending 均不得重複
- **回傳**：建立結果，含 `file_path`

#### `approve_pending_term`
- **輸入**：`{ "term_id": string }` — 待審術語 ID
- **回傳**：核准結果，含寫入的 YAML 路徑；自動呼叫 `reset_glossary_cache()`

#### `reject_pending_term`
- **輸入**：`{ "term_id": string, "reason": string }` — 術語 ID 與拒絕原因
- **回傳**：拒絕結果，含刪除的文件路徑

### 新聞收集工具（news.py）

#### `fetch_security_news`
- **輸入**：`{ "days": int (預設 7), "min_score": float (預設 0.0) }`
- **回傳**：新聞清單，每項含 `title`、`url`、`source`、`published`、`summary`

#### `fetch_vulnerabilities`
- **輸入**：`{ "days": int (預設 7), "min_cvss": float (預設 7.0) }`
- **回傳**：漏洞清單，每項含 `cve_id`、`description`、`cvss`、`published`

#### `list_news_sources`
- **輸入**：無必填參數
- **回傳**：來源清單，每項含 `name`、`url`、`category`、`priority`、`status`

#### `suggest_searches`
- **輸入**：`{ "topic": string (可選) }`
- **回傳**：搜尋建議清單，每項含 `query`、`template`、`purpose`

### 週報工具（report.py）

#### `generate_report_draft`
- **輸入**：`{ "report_data": object }` — 包含 events、vulnerabilities、threat_trends 等欄位的結構化資料
- **回傳**：`{ "report_id": string, "file_path": string }` — 儲存至 `output/reports/SEC-WEEKLY-YYYY-WW.json`

#### `list_reports`
- **輸入**：無必填參數
- **回傳**：已產生週報清單，每項含 `report_id`、`file_path`、`period`、`created_at`

---

## 測試矩陣（Test Matrix）

| 工具 | 正常路徑 | 邊界條件 | 錯誤處理 | 測試檔案 |
|------|---------|---------|---------|---------|
| `search_term` | 英文查詢、中文查詢 | 無結果查詢 | 空字串 | test_glossary_tools.py |
| `get_term_definition` | 已知 term_id | 不存在 term_id | — | test_glossary_tools.py |
| `validate_terminology` | 含禁用詞文本 | 全合規文本 | 空文本 | test_glossary_tools.py |
| `add_term_links` | markdown 格式 | html 格式 | 無術語文本 | test_glossary_tools.py |
| `list_pending_terms` | 有待審術語 | 無待審術語 | — | test_term_approval.py |
| `extract_terms` | 含多術語文本 | 無術語文本 | — | test_glossary_tools.py |
| `create_pending_term` | 新術語 | ID 重複攔截 | brief_definition 超長 | test_term_approval.py |
| `approve_pending_term` | 正常核准 | 術語不存在 | 欄位不完整 | test_term_approval.py |
| `reject_pending_term` | 正常拒絕 | 術語不存在 | — | test_term_approval.py |
| `fetch_security_news` | 正常抓取 | 無結果 | 來源逾時 | test_news_tools.py |
| `fetch_vulnerabilities` | CVSS 過濾 | 無高危漏洞 | API 不可用 | test_news_tools.py |
| `list_news_sources` | 完整列表 | — | — | test_sources_integration.py |
| `suggest_searches` | 一般主題 | 無 topic 參數 | — | test_news_tools.py |
| `generate_report_draft` | 完整資料 | 空 events | — | test_report_tools.py |
| `list_reports` | 有週報 | 無週報 | — | test_report_tools.py |

---

## 追溯性（Traceability）

| 規格項目 | 實作位置 | 測試覆蓋 |
|---------|---------|---------|
| 術語庫工具（9 個） | `packages/mcp-server/src/security_weekly_mcp/tools/glossary.py` | `tests/test_glossary_tools.py`, `tests/test_term_approval.py` |
| 新聞收集工具（4 個） | `packages/mcp-server/src/security_weekly_mcp/tools/news.py` | `tests/test_news_tools.py`, `tests/test_sources_integration.py` |
| 週報工具（2 個） | `packages/mcp-server/src/security_weekly_mcp/tools/report.py` | `tests/test_report_tools.py` |
| 工具回傳格式 | `packages/mcp-server/src/security_weekly_mcp/server.py` | 整合測試 |
| `brief_definition` ≤ 30 字元限制 | `tools/glossary.py`（create + approve 均驗證） | `tests/test_term_approval.py` |
| ID 重複三道防線 | `tools/glossary.py:create_pending_term` | `tests/test_term_approval.py` |

**最後驗證日期**：2026-05-11
