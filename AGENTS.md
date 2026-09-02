# AGENTS.md — security-weekly-mcp 開發慣例(人機一體適用)

本檔為開發慣例的單一入口:任何 harness(Claude Code 或其他讀 AGENTS.md 的工具)與人類開發者讀到相同內容。專案總覽、MCP 工具清單、資料來源明細見 `README.md`;貢獻流程細節見 `CONTRIBUTING.md`。

## 目錄導覽

Monorepo(uv workspace),完整目錄樹見 `README.md`「專案結構」:

- `packages/glossary/` — 資安術語庫,Git Submodule → `astroicers/security-glossary-tw`;`terms/` 分類 YAML、`meta/` 元資料(categories、style_guide)、`pending/` 待審術語。
- `packages/mcp-server/` — MCP Server 主程式(`security_weekly_mcp`);工具模組在 `tools/`,分 `glossary.py`(術語庫)、`news.py`(新聞收集)、`report.py`(週報)。
- `config/` — `sources.yaml`(資料來源設定,含各來源啟停狀態)、`search_templates.yaml`(搜尋查詢模板)、`writing_style.yaml`(寫作風格)。
- `output/reports/` — 產出的週報(`SEC-WEEKLY-YYYY-WW.json`),經 `deploy-rss.yml` 發布為 HTML 至 GitHub Pages。
- `scripts/` — 自動化腳本(如 `generate_rss.py` 產 HTML/RSS)。
- `skill/` — Claude Code Skill 定義(自然語言介面的原始碼)。
- `tests/` — pytest 測試。
- `.asp/` — gate 渲染物(`gate.sh`、`gitleaks.toml`);單一事實源為根目錄 `asp-gate.yaml`,渲染物勿手改。另含 `pr.md`——asp-ng worker 出勤的 PR 描述快照(每票覆寫,main 恆為最近一票;asp-ng 決策 24/#183 已知邊界,人勿編輯)。

## 語言與風格

- 文件與 commit 訊息使用繁體中文;技術名詞保留英文。
- Python 遵循 PEP 8,以 ruff 檢查與格式化(`make lint` / `make format`)。
- 週報與術語內容遵循 `packages/glossary/meta/style_guide.yaml` 用詞規範(單一事實源),常見對照:駭客(非「黑客」)、惡意程式(非「病毒」)、特洛伊木馬程式(非「木馬」)、暴力破解(非「爆破」)、身份驗證用「驗證」(非「認證」)。

## 分支與提交

- 流:工作分支 → PR → `main`(單線,無 develop;merge 前 CI 須綠)。
- 分支名以型別前綴,如 `feature/*`、`fix/*`、`chore/*`、`ci/*`。
- Commit 遵循 Conventional Commits:`feat|fix|docs|refactor|test|chore|report|ci(scope): 摘要`(與 `asp-gate.yaml` 的 commit-format 檢查一致)。
- `report` 型別專用於每週週報產出 commit,如 `report: weekly security report 2026-W32`。
- 提交前跑本地 gate:`bash .asp/gate.sh`(lint、gitleaks staged 秘密掃描、commit 格式);本地 gate 與 CI 跑同一份渲染物,判定一致由構造保證。

### 分支流(2026-08-21 起)

- **develop = 整合層**:asp-ng worker 的 PR 一律以 develop 為 base;CI 全套照跑。
- **main = 部署面**:push main 會觸發 deploy-rss(RSS 發布)——develop→main 的促升
  PR **必由人審併**,這是本 repo 的部署閘,不在任何自動化放權路徑上。

## 票與 PR

- PR 清楚描述變更內容、關聯對應 issue(`Closes #n`)、確保 CI 綠後才請 review。
- 一 PR 一主題;超出範圍的想法開新 issue 而非擴大 diff。
- 術語庫內容變更(`terms/`、`meta/`)請至 `security-glossary-tw` 提 PR;本 repo 的 PR 只更新 submodule 指標。

## 測試

- 框架 pytest;非同步測試標 `pytest.mark.asyncio`;共享資源用 fixture。
- 分層 markers:預設為快速測試;網路相關測試標 `@pytest.mark.slow`;整合測試標 `integration`。
- 常用目標:`make test`(快速,排除 slow/integration,含 coverage)、`make test-all`(全部)、`make test-quick`(無 coverage,開發用)。
- 新增 MCP 工具至少附基本測試;缺陷修復附重現測試。
- CI(`ci.yml`)於 Python 3.11/3.12/3.13 矩陣執行,並含 ruff 檢查與 pip-audit 依賴安全審計。

## 開發指令

以 Makefile 為準(`make help` 列出全部),常用:

```bash
make sync         # 初始化 submodule + 安裝依賴
make test         # 快速測試
make lint         # ruff check
make format       # ruff format
make server       # 以 stdio 模式啟動 MCP Server
make dev          # MCP Inspector 開發模式
```

## 領域不變量(實作時必守)

- `create_pending_term` 三道防線:ID 檢查(`glossary.get`)、名稱檢查(`glossary.get_by_name`,含 term_en/term_zh/aliases,攔截 ID 不同但名稱相同的重複)、pending 掃描(`pending/*.yaml` 無同 ID 待審)。
- `approve_pending_term` 成功寫入 YAML 後必呼叫 `reset_glossary_cache()`,確保同 session 後續的重複檢查看得到剛入庫的術語。
- `brief_definition` 長度 ≤ 30 字元(create 與 approve 均驗證)。
- `extract_terms` 去重並保留術語出現順序。
- 術語連結:每個術語只在首次出現時加連結(避免干擾閱讀);連結指向 `https://glossary.astroicers.link/glossary/{term_id}`;HTML 週報底部「本期術語區塊」最多 10 個。
- 週報新聞過濾條件(CVSS 門檻、時間窗、關鍵字加權)之單一事實源為 `config/sources.yaml` 與 `packages/mcp-server/.../news.py`、`generate_weekly_report.py`,勿在文件另抄數值。

## Submodule 慣例

- `packages/glossary/` 是 Git Submodule,指向 `astroicers/security-glossary-tw`。
- Clone 後初始化:`git submodule update --init --recursive`(或 `make sync`)。
- 更新術語庫指標:`git submodule update --remote packages/glossary`。
- CI 已設定 `submodules: recursive`,毋須另行處理。

## 相關專案

| 專案 | 位置 | 狀態 | 用途 |
|------|------|------|------|
| security-glossary-tw | `../security-glossary-tw/` | 活躍 | 術語庫獨立倉庫(submodule 上游) |
| security-weekly-report | `../security-weekly-report/` | 封存 | 歷史週報(功能已遷至 Skill) |
| Claude Code Skill | `~/.claude/skills/security-weekly-tw/` | 活躍 | 自然語言介面(原始碼在本 repo `skill/`) |
