# ADR-001: 初始技術棧選型

| 欄位 | 內容 |
|------|------|
| **狀態** | `Accepted` |
| **日期** | 2026-02-15 |
| **決策者** | 技術負責人 |

---

## 背景（Context）

security-weekly-mcp 需要作為 MCP Server，整合現有的 Python 術語庫（security-glossary-tw submodule），提供資安週報生成、術語查詢、RSS 新聞收集等功能。

關鍵約束條件：
1. **Submodule 相依**：`packages/glossary/` 是 Python package，技術棧需能直接 import 調用
2. **MCP 協議相容**：需與 Claude Code 的 MCP 客戶端完全相容
3. **非同步 I/O**：RSS 抓取、HTTP 請求需高效並行處理（32 個來源）
4. **Monorepo 結構**：術語庫與 MCP Server 分開發布，但共享一個 repo

---

## 評估選項（Options Considered）

### 選項 A：Python + uv + 官方 MCP SDK（最終選擇）

- **優點**：
  - 與 security-glossary-tw（Python）零摩擦整合，直接 import
  - uv workspace 原生支援 monorepo，`packages/` 結構自然
  - 官方 MCP SDK 保證協議合規，不依賴第三方抽象
  - asyncio 原生支援，httpx[http2] 高效 RSS 並行抓取
  - Python 3.11-3.13 matrix CI，覆蓋未來版本
- **缺點**：
  - uv workspace 為相對新概念，CI 需額外學習成本
  - MCP Python SDK 版本上界（`<2.0.0`）需定期評估升級
- **風險**：MCP SDK major version 升級可能有 breaking change

### 選項 B：Node.js + TypeScript + MCP SDK

- **優點**：TypeScript MCP SDK 較成熟；前端生態工具豐富
- **缺點**：
  - 無法直接調用 Python glossary package，需 subprocess 或 REST API 橋接
  - 團隊主要熟悉 Python，切換成本高
- **風險**：跨語言橋接增加運維複雜度，調試困難

### 選項 C：Python + Poetry + FastMCP

- **優點**：FastMCP 高階抽象，裝飾器語法開發速度快
- **缺點**：
  - FastMCP 為第三方框架，官方 MCP spec 更新可能出現落差
  - Poetry 不支援 workspace，monorepo 管理困難
- **風險**：FastMCP 版本與 Claude Code 客戶端不相容風險較高

---

## 決策（Decision）

選擇**選項 A：Python + uv + 官方 MCP SDK**，因為：

1. 術語庫相依性是硬性約束，Python 是唯一零摩擦選項
2. uv workspace 完整解決 monorepo 的依賴隔離需求
3. 官方 SDK 保證與 Claude Code MCP 客戶端的協議相容性
4. asyncio + httpx 組合在 RSS 並行抓取場景下效能充足

完整技術棧：
- **語言**：Python 3.11+（型別標注，asyncio）
- **套件管理**：uv workspace 模式
- **MCP 框架**：`mcp[cli]>=1.2.0,<2.0.0`（官方 SDK）
- **HTTP 客戶端**：`httpx[http2]>=0.25.0`
- **資料模型**：`pydantic>=2.5`（驗證術語格式）
- **RSS 解析**：`feedparser>=6.0`
- **Build backend**：hatchling（packages/mcp-server）
- **測試**：pytest + pytest-asyncio（asyncio_mode=auto）
- **Linting**：ruff（check + format，line-length=100）
- **CI**：GitHub Actions，Python 3.11/3.12/3.13 matrix

---

## 後果（Consequences）

**正面影響：**
- 術語庫整合為零成本，直接 import Python package
- uv workspace 讓 `packages/glossary`（submodule）與 `packages/mcp-server` 依賴完全隔離
- 官方 MCP SDK 的 `stdio_server` 模式與 Claude Code 整合即開即用

**負面影響 / 技術債：**
- `mcp[cli]<2.0.0` 的版本上界需在 MCP SDK 2.0 發布時評估升級
- asyncio_mode=auto 在測試中需注意 fixture scope 管理

**後續追蹤：**
- [x] MCP Server 實作（server.py + tools/）
- [x] 15 個 MCP 工具完成實作（glossary 9 + news 3 + report 2 + 額外 1）
- [x] CI 三矩陣（3.11/3.12/3.13）通過
- [ ] MCP SDK 2.0 發布時評估升級計劃

---

## 成功指標（Success Metrics）

| 指標 | 目標值 | 驗證方式 | 狀態 |
|------|--------|----------|------|
| MCP 工具數量 | ≥ 14 個 | `list_tools()` 回傳 | ✅ 達成（15 個）|
| 測試通過率 | 100% | `make test` | ✅ 達成 |
| Python 版本支援 | 3.11, 3.12, 3.13 | CI matrix | ✅ 達成 |
| RSS 來源數 | ≥ 30 個 | sources.yaml | ✅ 達成（32 個）|
| 術語庫整合 | 零橋接層 | 直接 import | ✅ 達成 |
| MCP 協議合規 | Claude Code 可連線 | 手動測試 | ✅ 達成 |

---

## 關聯（Relations）

- 取代：（無）
- 被取代：（無）
- 參考：
  - `pyproject.toml`（依賴宣告）
  - `packages/mcp-server/pyproject.toml`（MCP Server 套件設定）
  - `.github/workflows/ci.yml`（CI 設定）
