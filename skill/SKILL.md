---
name: security-weekly-tw
description: |
  Use when working with Taiwan security weekly reports or security glossary.
  Handles: reviewing pending terms, adding new terms, updating term definitions,
  generating professional weekly reports, term matching and validation,
  discovering new security terms from the web.
  Triggers: 週報, 術語, glossary, 審核, 資安新聞, security report, term review,
  add term, validate terminology, 產生週報, 新增術語, 更新術語, 術語比對,
  收集術語, discover terms, 搜尋新術語, 找術語.
---

# Security Weekly TW - 資安週報與術語庫管理

## 專案路徑

| 專案 | 路徑 |
|------|------|
| Monorepo | `~/projects/security-weekly-mcp/` |
| 術語庫 | `~/projects/security-weekly-mcp/packages/glossary/` |
| MCP Server | `~/projects/security-weekly-mcp/packages/mcp-server/` |
| 週報輸出 | `~/projects/security-weekly-mcp/output/reports/` |
| 舊專案（已封存） | `~/projects/security-glossary-tw/`, `~/projects/security-weekly-report/` |

## 功能概覽

| 功能 | 觸發詞 | 說明 |
|------|--------|------|
| 審核待審術語 | 「審核術語」「review terms」 | 檢視 pending/ 中的新術語 |
| 新增術語 | 「新增術語」「add term」 | 手動新增術語到術語庫 |
| 更新術語庫 | 「更新術語」「修改定義」 | 修改現有術語定義 |
| 產生週報 | 「產生週報」「寫週報」 | 根據來源產生專業週報 |
| 術語比對 | 「檢查用詞」「加術語連結」 | 驗證用詞並加上連結 |
| 收集術語 | 「收集術語」「discover terms」 | 從網路搜尋新興資安術語 |

## MCP 工具清單

MCP Server `security-weekly-tw` 提供以下工具：

### 術語庫工具
| 工具 | 說明 |
|------|------|
| `search_term` | 模糊搜尋術語庫 |
| `get_term_definition` | 取得完整術語定義 |
| `validate_terminology` | 驗證用詞規範 |
| `add_term_links` | 為文本加術語連結 |
| `list_pending_terms` | 列出待審術語 |
| `extract_terms` | 從文本自動提取術語 |
| `approve_pending_term` | 批准待審術語 |
| `reject_pending_term` | 拒絕待審術語 |

### 新聞收集工具
| 工具 | 說明 |
|------|------|
| `fetch_security_news` | 從 RSS 來源收集資安新聞 |
| `fetch_vulnerabilities` | 收集 NVD + CISA KEV 漏洞 |
| `list_news_sources` | 列出新聞來源 |
| `suggest_searches` | 產生 WebSearch/WebFetch 搜尋建議 |
| `list_weekly_data` | 列出已保存的週報原始資料 |
| `load_weekly_data` | 載入指定週數的原始資料 |

### 週報工具
| 工具 | 說明 |
|------|------|
| `generate_report_draft` | 產生週報結構化資料 |
| `compile_report_pdf` | 使用 Typst 編譯 PDF |
| `list_reports` | 列出已產生的週報 |

---

## 兩階段週報架構

```
GitHub Actions (每週一自動)          你 + Claude (隨時)
════════════════════════           ═══════════════════

collect_weekly_data.py              「產生週報」
       ↓                                  ↓
  抓 RSS + API                      load_weekly_data
       ↓                                  ↓
  output/raw/YYYY-WNN.json          讀取已保存資料
       ↓                            + WebSearch 補充
  永久保存到 repo                    + AI 分析撰寫
                                          ↓
                                    高品質 PDF 報告
```

### 為什麼需要兩階段？
- RSS feed 只保留最近幾天的資料（揮發性）
- GitHub Actions 每週自動保存，確保資料不流失
- 你可以事後隨時用 Claude 產生高品質報告

---

## 功能一：審核待審術語

### 工作流程

1. **列出待審術語**
   ```bash
   ls ~/projects/security-weekly-mcp/packages/glossary/pending/
   ```

2. **讀取並顯示摘要**（每個 pending 檔案）

   | 欄位 | 來源 |
   |------|------|
   | 術語名稱 | `term.term_en` / `term.term_zh` |
   | 定義 | `term.definitions.brief` |
   | 分類 | `term.category` / `term.subcategory` |
   | 關聯判斷 | `term.parent_term`, `term.relationship` |
   | 信心度 | `discovery.confidence` |
   | AI 建議 | `ai_analysis.recommendation` |

3. **互動決策**
   ```
   ### Scattered Spider
   - **英文**: Scattered Spider
   - **中文**: Scattered Spider
   - **定義**: 以社交工程和 SIM 卡劫持聞名的駭客組織
   - **分類**: threat_actors/cybercrime_group
   - **信心度**: 88%

   請選擇：[A] 批准  [E] 編輯  [R] 拒絕  [S] 跳過
   ```

4. **執行操作**
   - **批准 (A)**：驗證格式後追加到 `terms/{category}.yaml`
   - **編輯 (E)**：讓使用者修改欄位後追加
   - **拒絕 (R)**：刪除 pending 檔案
   - **跳過 (S)**：保留待下次審核

### 格式驗證

批准前須驗證：
- `id` 為小寫底線分隔（如 `scattered_spider`）
- `definitions.brief` 不超過 30 字
- `category` 為有效分類 ID
- 無重複 ID（與現有術語比對）

詳見 [references/term_format.md](references/term_format.md)

---

## 功能二：新增術語

### 工作流程

1. **收集資訊**
   - 英文術語 (term_en)
   - 中文術語 (term_zh)
   - 簡短定義 (definitions.brief，30 字內)
   - 分類 (category)

2. **判斷關聯**（使用決策樹）

   | 問題 | 是 → 結果 |
   |------|-----------|
   | 是現有術語的別名嗎？ | 加入 aliases，不建新術語 |
   | 是具體組織/軟體/事件？ | `relationship: instance_of` |
   | 是概念的子分類？ | `relationship: subtype_of` |
   | 是術語的新版本？ | `relationship: variant_of` |
   | 以上皆非 | 獨立術語或 `related_to` |

3. **產生 YAML**
   ```yaml
   - id: "term_id"
     term_en: "English Term"
     term_zh: "中文術語"
     definitions:
       brief: "30字內簡短定義"
     category: "category_id"
     parent_term: null
     relationship: null
     metadata:
       status: "approved"
   ```

4. **追加到檔案**
   - 寫入 `~/projects/security-weekly-mcp/packages/glossary/terms/{category}.yaml` 的 `terms:` 區塊末尾

### 分類選項

| ID | 中文 | 說明 |
|----|------|------|
| `attack_types` | 攻擊類型 | 社交工程、網路攻擊等 |
| `vulnerabilities` | 漏洞類型 | CVE 類型、安全弱點 |
| `threat_actors` | 威脅行為者 | APT 組織、犯罪集團 |
| `malware` | 惡意程式 | 勒索軟體、木馬等 |
| `technologies` | 技術名詞 | 資安技術與工具 |
| `frameworks` | 框架標準 | MITRE ATT&CK、NIST 等 |
| `compliance` | 法規合規 | 資安法規與合規 |

---

## 功能三：更新術語庫

### 工作流程

1. **搜尋術語**（支援 ID、英文、中文、別名）
   ```bash
   grep -r "搜尋詞" ~/projects/security-weekly-mcp/packages/glossary/terms/
   ```

2. **顯示現有定義**

3. **讓使用者指定修改欄位**

### 可修改欄位

| 欄位 | 說明 |
|------|------|
| `definitions.brief` | 簡短定義（30 字內） |
| `definitions.standard` | 標準定義（100 字內） |
| `definitions.detailed` | 詳細定義 |
| `aliases.en` / `aliases.zh` | 別名 |
| `related_terms` | 相關術語 |
| `tags` | 標籤 |
| `references` | 參考連結 |

---

## 功能四：產生週報

### 資料收集流程（三階段）

```
┌─────────────────────────────────────────────────────────────┐
│                   階段 1：MCP 工具基礎收集                    │
├─────────────────────────────────────────────────────────────┤
│  使用 security-weekly-mcp MCP Server 工具：                  │
│                                                             │
│  1. fetch_security_news - 收集 32 個 RSS 來源                │
│     - 國際: The Hacker News, Krebs, SecurityWeek, CyberScoop│
│     - 台灣: iThome, TWCERT/CC, TechNews 資安                 │
│     - 威脅情報: CrowdStrike, Unit 42, Securelist, 等        │
│                                                             │
│  2. fetch_vulnerabilities - 收集漏洞資訊                     │
│     - NVD API (CVSS ≥ 7.0)                                  │
│     - CISA KEV (已知被利用漏洞)                              │
│                                                             │
│  3. extract_terms - 自動提取術語庫術語                       │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                   階段 2：WebSearch/WebFetch 補充             │
├─────────────────────────────────────────────────────────────┤
│  使用 MCP 工具 suggest_searches 取得搜尋建議：               │
│                                                             │
│  1. 呼叫 suggest_searches(category="all")                   │
│                                                             │
│  2. 執行 WebSearch 查詢（按優先級）：                        │
│     - site:twcert.org.tw 資安通報                           │
│     - 台灣 資安事件 2026                                    │
│     - site:informationsecurity.com.tw                       │
│     - CVE critical vulnerability 2026                       │
│                                                             │
│  3. 執行 WebFetch 抓取目標網頁：                            │
│     - TWCERT/CC 最新消息頁面                                │
│     - 數位發展部資安公告                                    │
│     - 資安人首頁                                            │
│                                                             │
│  4. 整合搜尋結果到週報資料                                   │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                   階段 3：分析與產生                          │
├─────────────────────────────────────────────────────────────┤
│  1. 整理所有收集到的資料                                     │
│  2. 評估風險等級（依 CVSS）                                  │
│  3. 識別新術語 → 寫入 pending/                               │
│  4. 產生 generate_report_draft                               │
│  5. 編譯 compile_report_pdf（如需 PDF）                      │
└─────────────────────────────────────────────────────────────┘
```

### 完整週報產生指令範例

**本週週報**（使用 RSS + WebSearch）：
```
使用者：產生本週資安週報

Claude 執行：
1. 呼叫 fetch_security_news(days=7, limit=30)
2. 呼叫 fetch_vulnerabilities(min_cvss=7.0, days=7, include_kev=True)
3. 呼叫 suggest_searches(category="all")
4. 依序執行 WebSearch 查詢（前 5 個高優先級）
5. 依序執行 WebFetch 抓取（前 3 個）
6. 整合資料並產生報告草稿
7. 呼叫 generate_report_draft(...)
8. 呼叫 compile_report_pdf(...) 產生 PDF
```

**歷史週報**（完全依賴 WebSearch，因為 RSS 資料已過期）：
```
使用者：產生 2025 年 6 月第一週的資安週報

Claude 執行：
1. 呼叫 suggest_searches(category="all", period_start="2025-06-01", period_end="2025-06-07")
   → 工具自動加入時間過濾（after:2025-06-01 before:2025-06-07）
   → 不回傳 WebFetch 目標（網頁內容是最新的）
2. 執行所有 WebSearch 查詢（會包含時間範圍）
   - 台灣 資安事件 2025 after:2025-06-01 before:2025-06-07
   - CVE 2025-06 critical
   - 台灣 資安事件 2025年06月
3. 整合搜尋結果
4. 呼叫 generate_report_draft(period_start="2025-06-01", period_end="2025-06-07", ...)
5. 呼叫 compile_report_pdf(...) 產生 PDF
```

### 輸入來源

使用者可提供：
1. **自動收集** → 執行完整三階段流程
2. **指定時間範圍** → 產生歷史週報（使用 WebSearch）
3. **新聞網址** → 使用 WebFetch 取得內容
4. **貼上文章** → 直接使用
5. **上傳文件** → 讀取檔案內容
6. **指定主題** → 使用 WebSearch 搜尋

### 週報結構

```markdown
# 資安週報

**報告期間**：YYYY/MM/DD ~ YYYY/MM/DD
**發布日期**：YYYY/MM/DD
**報告編號**：SEC-WEEKLY-YYYY-WW

---

## 📊 本週摘要

[2-3 句話總結]

| 指標 | 數值 |
|------|------|
| 重大事件 | X 件 |
| 高風險漏洞 | X 個 |
| 威脅等級 | 🔴/🟡/🟢 升高/正常/降低 |

---

## 🔴 重大資安事件

### 1. [事件標題]

**影響等級**：🔴 危急
**事件類型**：[威脅情報/漏洞通報/資料外洩]

[2-4 段落事件摘要]

**受影響產業**：[產業列表]

**建議行動**：
1. [具體行動項目]
2. [具體行動項目]

---

## 🛡️ 關鍵漏洞通報

| CVE ID | 產品 | CVSS | 狀態 | 優先級 |
|--------|------|------|------|--------|
| CVE-XXXX-XXXXX | 產品名 | 9.8 | 🔴 已遭利用 | ⚡ P1 |

---

## 📈 威脅趨勢

[整體威脅態勢分析]

### 本週活躍威脅行為者
- **[組織名稱]**：[活動描述]

### 熱門攻擊手法
- [攻擊手法1]
- [攻擊手法2]

---

## ✅ 本週行動項目

| 優先級 | 行動項目 | 負責單位 | 期限 |
|--------|----------|----------|------|
| ⚡ P1 | [行動項目] | 資安團隊 | 立即 |
| 🔥 P2 | [行動項目] | 資安團隊 | 本週 |

---

## 📚 本期術語

| 術語 | 說明 |
|------|------|
| [APT](https://glossary.astroicers.link/glossary/apt/) | 進階持續性威脅。國家級駭客組織發動的長期網路攻擊 |

---

## 📖 參考資料

1. [來源標題](URL)
```

### 檔案命名與儲存

- **路徑**：`~/projects/security-weekly-mcp/output/reports/`
- **格式**：`SEC-WEEKLY-YYYY-WW.md`（年份-週數）

---

## 功能五：術語比對與驗證

### 工作流程

1. **接收使用者文本**
2. **載入術語庫**（讀取 `terms/*.yaml`）
3. **比對術語並加連結**
4. **檢查禁止用詞**
5. **輸出結果**

### 術語連結格式

```markdown
[術語名稱](https://glossary.astroicers.link/glossary/{id}/)
```

### 驗證報告格式

```
## 術語比對結果

**比對到的術語**：5 個
**用詞問題**：2 個

### 處理後文本

> 駭客利用 [APT](URL) 攻擊手法入侵系統

### ⚠️ 用詞問題

1. 第 1 行：「黑客」建議改為「駭客」
2. 第 3 行：「病毒」建議改為「惡意程式」
```

---

## 禁止用詞對照表

| 禁止 | 正確 | 原因 |
|------|------|------|
| 黑客 | 駭客 | 台灣慣用語 |
| 病毒 | 惡意程式 | 病毒只是一種類型 |
| 軟件 | 軟體 | 台灣用語 |
| 信息 | 資訊 | 台灣用語 |
| 代碼 | 程式碼 | 台灣用語 |
| 服務器 | 伺服器 | 台灣用語 |
| 數據 | 資料 | 台灣用語 |
| 網絡 | 網路 | 台灣用語 |
| 木馬 | 特洛伊木馬程式 | 完整術語 |
| 肉雞 | 受感染主機 | 專業用語 |
| 脫褲 | 資料外洩 | 專業用語 |
| 社工 | 社交工程 | 完整術語 |
| 爆破 | 暴力破解 | 完整術語 |
| 提權 | 權限提升 | 完整術語 |
| 認證 | 驗證 | authentication 應譯為驗證 |

---

## 嚴重程度標準

| 等級 | 圖示 | CVSS 範圍 |
|------|------|----------|
| 危急 | 🔴 | 9.0-10.0 |
| 高 | 🟠 | 7.0-8.9 |
| 中 | 🟡 | 4.0-6.9 |
| 低 | 🟢 | 0.1-3.9 |
| 資訊 | 🔵 | 0 |

## 行動優先級

| 優先級 | 圖示 | 期限 |
|--------|------|------|
| 立即 | ⚡ | 24 小時內 |
| 緊急 | 🔥 | 48-72 小時內 |
| 優先 | ❗ | 一週內 |
| 一般 | 📋 | 兩週內 |

---

## 寫作風格重點

### 核心原則

1. **精準簡潔** - 用最少的字傳達重點
2. **風險導向** - 聚焦業務影響，不只技術細節
3. **可行動** - 每個發現有具體建議
4. **客觀中立** - 基於事實

### 避免的 AI 模式

- ❌ 首先、其次、最後
- ❌ 總的來說、綜上所述
- ❌ 值得注意的是
- ❌ 在當今這個...的時代
- ❌ 希望本報告對您有所幫助

### 句型模板

**事件描述**：
```
[時間] [組織/對象] 遭受 [攻擊類型]，[一句話影響]
```
例：「本週某金融機構遭受 LockBit 勒索軟體攻擊，約 50 萬筆客戶資料恐外洩」

**漏洞描述**：
```
[產品] 存在 [漏洞類型]（CVE-XXXX），CVSS [分數]
```
例：「Microsoft Exchange 存在 RCE 漏洞（CVE-2024-1234），CVSS 9.8」

**建議行動**：
```
[動作] [對象]，[期限/方式]
```
例：「立即更新所有 Exchange Server 至 2024 年 3 月累積更新」

詳見 [references/writing_style.md](references/writing_style.md)

---

## 資安資源清單

詳見 [references/security_sources.md](references/security_sources.md)

### 優先使用來源

**台灣**：iThome 資安、TWCERT/CC、DEVCORE、TeamT5

**國際新聞**：The Hacker News、BleepingComputer、Krebs on Security

**官方公告**：CISA Alerts、CISA KEV、NVD

**威脅情報**：Mandiant、Microsoft Security Blog、Kaspersky SecureList

---

## 檔案操作參考

### 讀取術語
```bash
cat ~/projects/security-weekly-mcp/packages/glossary/terms/threat_actors.yaml
```

### 讀取 pending 術語
```bash
cat ~/projects/security-weekly-mcp/packages/glossary/pending/*.yaml
```

### 儲存週報
```
~/projects/security-weekly-mcp/output/reports/SEC-WEEKLY-{YYYY}-{WW}.md
```

### 新增 pending 術語
```
~/projects/security-weekly-mcp/packages/glossary/pending/{YYYY-MM-DD}-{term_id}.yaml
```

---

## 功能六：收集術語

### 觸發詞

「收集術語」「discover terms」「搜尋新術語」「找術語」

### 工作流程

1. **搜尋新興資安術語**
   - 使用 WebSearch 搜尋最新資安新聞和威脅報告
   - 重點來源：MITRE ATT&CK、Mandiant、Microsoft Security Blog
   - 搜尋關鍵字範例：
     - `new APT group 2026`
     - `new ransomware family 2026`
     - `emerging cyber threat`
     - `new malware strain`
     - `新興 APT 組織`

2. **識別候選術語**
   - 從搜尋結果中識別尚未收錄的術語
   - 與現有術語庫比對，排除已存在的術語
   - 優先收集：
     - 新出現的 APT 組織
     - 新型勒索軟體家族
     - 新攻擊手法名稱
     - 新漏洞類型

3. **產生 pending 檔案**

   對每個候選術語產生 pending YAML 檔案：

   ```yaml
   # 待審核術語 - {term_en}
   # 此檔案由術語收集功能自動產生，待人工審核

   discovery:
     discovered_at: "YYYY-MM-DD"
     discovered_in: "term-discovery"
     source_url: "來源網址"
     source_title: "來源標題"
     confidence: 0.85

   term:
     id: "term_id"
     term_en: "English Term"
     term_zh: "中文術語"

     definitions:
       brief: "30字內簡短定義"
       standard: |
         100字內標準定義

     category: "threat_actors"  # 或其他分類
     subcategory: "apt_group"   # 子分類
     tags: ["標籤1", "標籤2"]

     parent_term: null
     relationship: null
     related_terms: []

     aliases:
       en: ["別名1", "別名2"]

     references:
       mitre_attack: "https://..."

     metadata:
       status: "pending"
       auto_generated: true
       needs_review: true

   ai_analysis:
     reasoning: |
       為何建議收錄此術語的原因分析

     similar_existing_terms:
       - term_id: "existing_term"
         similarity: 0.80
         reason: "相似原因"

     recommendation: "建議新增為..."
   ```

4. **儲存位置**

   ```text
   ~/projects/security-weekly-mcp/packages/glossary/pending/{YYYY-MM-DD}-{term_id}.yaml
   ```

5. **後續處理**
   - 使用「審核術語」功能審核產生的 pending 檔案
   - 批准、編輯或拒絕候選術語

### 搜尋策略

**按分類搜尋**：

| 分類 | 搜尋關鍵字 |
|------|-----------|
| APT 組織 | `new APT group`, `nation-state actor`, `advanced persistent threat` |
| 勒索軟體 | `new ransomware`, `ransomware family`, `RaaS operator` |
| 惡意程式 | `new malware`, `malware strain`, `trojan`, `backdoor` |
| 攻擊手法 | `attack technique`, `MITRE ATT&CK new`, `exploit method` |
| 漏洞類型 | `new vulnerability class`, `CVE category` |

**優先來源**：

1. **MITRE ATT&CK**：新增的 Groups 和 Software
2. **Mandiant Blog**：新發現的威脅行為者
3. **Microsoft Security Blog**：Typhoon/Blizzard/Sleet 系列組織
4. **CISA Alerts**：新披露的威脅
5. **The Hacker News**：資安新聞中的新術語

### 範例執行

```
使用者：收集術語 APT

Claude：
1. 搜尋最新 APT 組織相關新聞...
2. 識別到 3 個候選術語：
   - Plaid Rain（新發現的北韓組織）
   - Velvet Ant（針對東南亞的中國組織）
   - Pensive Ursa（伊朗組織新別名）
3. 與現有術語庫比對...
4. 產生 pending 檔案：
   - pending/2026-01-30-plaid_rain.yaml
   - pending/2026-01-30-velvet_ant.yaml
5. 請使用「審核術語」功能審核這些候選術語
```

---

## 資料來源清單 (32 個)

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

### 台灣來源 (5 個)

| 來源 | 優先級 | 說明 |
|------|--------|------|
| iThome 資安 | high | 台灣 IT 媒體 (RSS) |
| TWCERT/CC 資安新聞 | critical | 台灣 CERT 資安新聞 (RSS) |
| TWCERT/CC 漏洞公告 | critical | 台灣 CERT TVN 漏洞公告 (RSS) |
| TechNews 資安 | high | 科技新報資安專區 (RSS) |
| 資安人 | medium | 台灣資安媒體 (WebFetch) |

### 官方公告 (4 個)

| 來源 | 優先級 | 說明 |
|------|--------|------|
| CISA Alerts | critical | 美國 CISA 公告 |
| CISA KEV | critical | 已知被利用漏洞 (API) |
| CERT/CC Vulnerability Notes | high | 卡內基美隆大學 CERT |
| CIS MS-ISAC Advisories | high | 網際網路安全中心 |

### 漏洞資料庫 (2 個)

| 來源 | 優先級 | 說明 |
|------|--------|------|
| NVD | high | NIST 漏洞資料庫 (API) |
| GitHub Security Advisories | medium | 開源漏洞 (API) |

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

### WebSearch 補充查詢

透過 `suggest_searches` 工具產生的搜尋查詢：

| 類別 | 查詢範例 |
|------|----------|
| 台灣新聞 | `site:twcert.org.tw 資安通報` |
| 台灣新聞 | `台灣 資安事件 {year}` |
| 漏洞 | `CVE critical vulnerability {year}` |
| 威脅情報 | `APT group campaign {year}` |

### WebFetch 目標網頁

| 網站 | URL | 用途 |
|------|-----|------|
| TWCERT/CC | https://www.twcert.org.tw/tw/np-131-1.html | 最新資安通報 |
| TWCERT/CC 電子報 | https://www.twcert.org.tw/newepaper/index.html | 電子報摘要 |
| 資安人 | https://www.informationsecurity.com.tw/ | 首頁新聞 |
| 數位發展部 | https://moda.gov.tw/ACS/security-notice | 資安公告 |
