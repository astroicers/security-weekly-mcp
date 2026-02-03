# 術語 YAML 格式規範

## 完整術語格式

```yaml
- id: "term_id"                        # 必填，小寫底線分隔
  term_en: "English Term"              # 必填，英文術語
  term_zh: "中文術語"                   # 必填，中文術語
  full_name_en: "Full English Name"    # 選填，英文全稱
  full_name_zh: "中文全稱"              # 選填，中文全稱

  definitions:
    brief: "30字內簡短定義"              # 必填，用於 Tooltip
    standard: |                         # 選填，100字內標準定義
      標準定義內容...
    detailed: |                         # 選填，完整技術說明
      詳細定義內容...

  category: "threat_actors"             # 必填，分類 ID
  subcategory: "apt_group"              # 選填，子分類
  tags: ["標籤1", "標籤2"]              # 選填

  parent_term: "apt"                    # 選填，父術語 ID
  relationship: "instance_of"           # 選填，關係類型
  related_terms: ["term1", "term2"]     # 選填
  child_terms: ["child1", "child2"]     # 選填，子術語列表

  aliases:
    en: ["Alias 1", "Alias 2"]          # 選填，英文別名
    zh: ["別名1", "別名2"]               # 選填，中文別名

  usage:
    preferred: true                     # 是否為偏好用語
    context: "使用情境說明"
    examples:
      - "例句1"
      - "例句2"
    avoid: ["避免用法"]

  references:
    mitre_attack: "https://attack.mitre.org/..."
    nist: "https://..."
    cwe: "https://cwe.mitre.org/..."
    owasp: "https://owasp.org/..."
    wikipedia: "https://..."

  metadata:
    status: "approved"                  # approved/pending/deprecated
    created: "2024-12-15"
    updated: "2024-12-15"
    attribution_country: "Russia"       # APT 組織歸屬國（若適用）
    attribution_agency: "SVR"           # APT 組織歸屬機構（若適用）
    first_seen: "2015-01"               # 首次發現時間（若適用）
    active: true                        # 是否仍活躍（若適用）
```

## 最小必需格式

```yaml
- id: "sql_injection"
  term_en: "SQL Injection"
  term_zh: "SQL 注入"
  definitions:
    brief: "透過惡意 SQL 語句操縱資料庫的攻擊"
  category: "vulnerabilities"
```

## 驗證規則

### 必填欄位
- `id` - 唯一識別碼
- `term_en` - 英文術語
- `term_zh` - 中文術語
- `definitions.brief` - 簡短定義
- `category` - 分類 ID

### 格式規則

| 欄位 | 規則 | 範例 |
|------|------|------|
| `id` | 小寫 + 底線，無空格 | `sql_injection`, `apt29` |
| `definitions.brief` | 不超過 30 個中文字 | 「透過惡意 SQL 語句操縱資料庫的攻擊」 |
| `category` | 有效分類 ID | `attack_types`, `threat_actors` |
| `relationship` | 有效關係類型 | `instance_of`, `subtype_of`, `variant_of` |
| `metadata.status` | 狀態值 | `approved`, `pending`, `deprecated` |

### 重複檢查

1. 檢查 `id` 是否已存在於 `terms/*.yaml`
2. 檢查術語名稱是否為現有術語的別名
3. 若重複，建議合併或使用不同 ID

## 關係類型定義

### instance_of（是...的實例）

具體的組織、軟體、事件，屬於某個通用類別。

```yaml
- id: "apt29"
  parent_term: "apt"
  relationship: "instance_of"
```

說明：APT29 是 APT 的一個具體組織。

### subtype_of（是...的子類型）

概念上的分類，不是具體實例。

```yaml
- id: "spear_phishing"
  parent_term: "phishing"
  relationship: "subtype_of"
```

說明：魚叉式釣魚是釣魚的一種特定類型。

### variant_of（是...的變體）

同一事物的不同版本。

```yaml
- id: "lockbit_30"
  parent_term: "lockbit"
  relationship: "variant_of"
```

說明：LockBit 3.0 是 LockBit 的新版本。

### alias_of（是...的別名）

完全相同的概念，只是不同名稱。**不需獨立術語**，應記錄在 `aliases` 欄位。

```yaml
# 不要這樣做：
- id: "cozy_bear"
  parent_term: "apt29"
  relationship: "alias_of"

# 應該這樣做：
- id: "apt29"
  aliases:
    en: ["Cozy Bear", "The Dukes", "NOBELIUM"]
```

## 判斷流程

```
新發現的術語
    │
    ▼
是現有術語的別名嗎？
    │
    ├── 是 → 加入 aliases 欄位，不建新術語
    │
    └── 否 → 是具體組織/軟體/事件嗎？
                │
                ├── 是 → relationship: instance_of
                │
                └── 否 → 是概念的子分類嗎？
                            │
                            ├── 是 → relationship: subtype_of
                            │
                            └── 否 → 是術語的新版本嗎？
                                        │
                                        ├── 是 → relationship: variant_of
                                        │
                                        └── 否 → 獨立術語或 related_to
```

## Pending 術語格式

自動產生的待審核術語格式：

```yaml
# 待審核術語
discovery:
  discovered_at: "2024-12-15"
  discovered_in: "weekly-report-2024-50"
  source_url: "https://..."
  source_title: "文章標題"
  confidence: 0.88

term:
  id: "scattered_spider"
  term_en: "Scattered Spider"
  term_zh: "Scattered Spider"
  definitions:
    brief: "以社交工程和 SIM 卡劫持聞名的駭客組織"
  category: "threat_actors"
  subcategory: "cybercrime_group"
  parent_term: null
  relationship: null
  metadata:
    status: "pending"
    auto_generated: true
    needs_review: true

ai_analysis:
  reasoning: |
    分析說明...
  similar_existing_terms:
    - term_id: "ransomware_group"
      similarity: 0.65
  recommendation: "建議新增為獨立術語"
```

## 有效分類 ID

| ID | 中文 | 子分類 |
|----|------|--------|
| `attack_types` | 攻擊類型 | social_engineering, network_attack, web_attack, advanced_attack, post_exploitation |
| `vulnerabilities` | 漏洞類型 | code_execution, injection, memory_safety, authentication, configuration |
| `threat_actors` | 威脅行為者 | actor_type, apt_group, cybercrime_group, methodology, infrastructure |
| `malware` | 惡意程式 | ransomware, trojan, worm, rootkit, other |
| `technologies` | 技術名詞 | security_operations, network_security, endpoint_security, identity, data_security, cloud_security |
| `frameworks` | 框架標準 | threat_framework, compliance_framework, assessment |
| `compliance` | 法規合規 | data_protection, industry_regulation, government |