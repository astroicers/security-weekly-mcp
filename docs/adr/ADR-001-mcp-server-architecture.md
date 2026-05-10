# [ADR-001]: MCP Server 技術棧與架構選型

| 欄位 | 內容 |
|------|------|
| **狀態** | `Accepted` |
| **日期** | 2026-02-01 |
| **決策者** | astroicers |

---

## 背景（Context）

需要建立一套整合台灣資安週報產生、術語庫管理、資安新聞收集的工具，並讓 Claude Code 透過自然語言介面操作。核心需求：

1. Claude Code 可直接呼叫工具（查術語、抓新聞、產週報）
2. 術語庫作為 Git Submodule 維護，可獨立更新
3. 兩階段週報架構：GitHub Actions 保存揮發性 RSS 資料 + 事後 Claude 分析產生報告
4. 支援 32 個資安 RSS 來源的並行收集

---

## 評估選項（Options Considered）

### 選項 A：MCP Server（Python, stdio 模式）

- **優點**：與 Claude Code 原生整合；工具以函數形式定義，直覺清晰；`uv` workspace 管理 monorepo
- **缺點**：MCP 協定較新，生態仍在成熟中
- **風險**：MCP spec 版本變動需跟進

### 選項 B：Claude Code Slash Commands（bash 腳本）

- **優點**：實作簡單
- **缺點**：缺乏型別安全；複雜參數傳遞困難；無法回傳結構化資料
- **風險**：長期維護成本高

### 選項 C：REST API + Webhook

- **優點**：語言無關
- **缺點**：需要伺服器運維；Claude Code 整合需額外橋接
- **風險**：運維複雜度高，不適合個人專案

---

## 決策（Decision）

選擇 **選項 A**：Python MCP Server + `mcp` 套件 + `uv` monorepo workspace。

架構決策：
- **傳輸模式**：stdio（最簡單，Claude Code 直接支援）
- **工具分層**：`tools/glossary.py`（8 工具）、`tools/news.py`（6 工具）、`tools/report.py`（3 工具）
- **術語庫**：Git Submodule（`packages/glossary/` → `astroicers/security-glossary-tw`）
- **套件管理**：`uv` + `pyproject.toml` workspace
- **資料收集**：`aiohttp` 並行 RSS 抓取 + NVD API + CISA KEV API
- **週報輸出**：Markdown（`output/reports/`）；PDF 由 Typst 編譯

---

## 後果（Consequences）

**正面影響：**
- Claude Code 可直接用自然語言操作所有工具，無需記憶指令
- 術語庫獨立版控，`git submodule update` 即可同步最新術語
- 並行 RSS 抓取提升資料收集效率（32 個來源）

**負面影響 / 技術債：**
- MCP Server 目前僅支援 stdio，未來若需多客戶端需新增 HTTP transport
- Git Submodule 操作對新手略有學習曲線

**後續追蹤：**
- [x] 建立 MCP Server 初始版本（16 工具）
- [x] 設定 GitHub Actions 每週自動收集 RSS 資料
- [x] 建立 Claude Code Skill 自然語言介面
- [ ] 評估 HTTP/SSE transport 需求（待有多客戶端需求時）

---

## 成功指標（Success Metrics）

| 指標 | 目標值 | 驗證方式 | 檢查時間 |
|------|--------|----------|----------|
| MCP Server 啟動 | 成功 | `python -m security_weekly_mcp.server` | 每次部署 |
| RSS 收集成功率 | ≥ 80% 來源可用 | `monthly-health.yml` workflow | 每月 |
| 術語搜尋回應 | < 1s | 手動測試 | 術語 > 1000 筆時 |

---

## 關聯（Relations）

- 取代：（無）
- 被取代：（無）
- 參考：SPEC-001-mcp-server.md、security-glossary-tw ADR-001
