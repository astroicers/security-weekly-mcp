# 術語分類定義

## 7 大分類

| ID | 中文 | 英文 | 圖示 |
|----|------|------|------|
| `attack_types` | 攻擊類型 | Attack Types | ⚔️ |
| `vulnerabilities` | 漏洞類型 | Vulnerabilities | 🔓 |
| `threat_actors` | 威脅行為者 | Threat Actors | 👤 |
| `malware` | 惡意程式 | Malware | 🦠 |
| `technologies` | 技術名詞 | Technologies | 🛡️ |
| `frameworks` | 框架標準 | Frameworks & Standards | 📋 |
| `compliance` | 法規合規 | Compliance & Regulations | ⚖️ |

## 詳細分類說明

### attack_types（攻擊類型）

各種網路攻擊手法與技術。

| 子分類 | 說明 | 範例術語 |
|--------|------|----------|
| `social_engineering` | 社交工程 | phishing, spear_phishing, whaling, bec |
| `network_attack` | 網路攻擊 | ddos, mitm, dns_spoofing |
| `web_attack` | Web 應用攻擊 | sql_injection, xss, csrf |
| `advanced_attack` | 進階攻擊 | supply_chain_attack, zero_day |
| `post_exploitation` | 後滲透 | lateral_movement, privilege_escalation |

### vulnerabilities（漏洞類型）

軟體與系統中的安全弱點分類。

| 子分類 | 說明 | 範例術語 |
|--------|------|----------|
| `code_execution` | 程式碼執行 | rce, lce |
| `injection` | 注入攻擊 | sql_injection, command_injection |
| `memory_safety` | 記憶體安全 | buffer_overflow, use_after_free |
| `authentication` | 驗證問題 | authentication_bypass, weak_password |
| `configuration` | 配置問題 | misconfig, default_credentials |

### threat_actors（威脅行為者）

網路威脅的來源與攻擊者類型。

| 子分類 | 說明 | 範例術語 |
|--------|------|----------|
| `actor_type` | 行為者類型 | apt, nation_state_actor, cybercriminal |
| `apt_group` | APT 組織 | apt29, apt28, apt41, lazarus_group |
| `cybercrime_group` | 網路犯罪組織 | scattered_spider, fin7 |
| `ransomware_operator` | 勒索軟體運營商 | lockbit, alphv, cl0p |
| `methodology` | 方法論 | ttp, campaign |
| `infrastructure` | 基礎設施 | c2, botnet |

### malware（惡意程式）

各類惡意軟體的分類與特徵。

| 子分類 | 說明 | 範例術語 |
|--------|------|----------|
| `ransomware` | 勒索軟體 | ransomware, raas |
| `trojan` | 特洛伊木馬 | trojan, rat, banking_trojan |
| `worm` | 蠕蟲 | worm |
| `rootkit` | 根套件 | rootkit, bootkit |
| `other` | 其他 | spyware, adware, cryptominer |

### technologies（技術名詞）

資安技術、工具與解決方案。

| 子分類 | 說明 | 範例術語 |
|--------|------|----------|
| `security_operations` | 安全運營 | siem, soc, soar |
| `network_security` | 網路安全 | firewall, ids, ips, waf |
| `endpoint_security` | 端點安全 | edr, xdr, antivirus |
| `identity` | 身分管理 | iam, mfa, sso |
| `data_security` | 資料安全 | dlp, encryption |
| `cloud_security` | 雲端安全 | casb, cspm |

### frameworks（框架標準）

資安框架、標準與評估方法。

| 子分類 | 說明 | 範例術語 |
|--------|------|----------|
| `threat_framework` | 威脅框架 | mitre_attack, cyber_kill_chain |
| `compliance_framework` | 合規框架 | nist_csf, iso_27001 |
| `assessment` | 評估標準 | cvss, cwe, owasp_top10 |

### compliance（法規合規）

資安相關法規與合規要求。

| 子分類 | 說明 | 範例術語 |
|--------|------|----------|
| `data_protection` | 資料保護 | gdpr, ccpa |
| `industry_regulation` | 產業標準 | pci_dss, hipaa |
| `government` | 政府法規 | fisma, cmmc |

## 關係類型定義

### instance_of（是...的實例）

具體的組織、軟體、事件，屬於某個通用類別。

**範例**：
- APT29 是 APT 的一個具體組織
- LockBit 是勒索軟體集團的一個具體組織

**顯示格式**：`{child} 是 {parent} 的一個實例`

### subtype_of（是...的子類型）

概念上的分類，不是具體實例。

**範例**：
- 魚叉式釣魚是釣魚的一種特定類型
- 勒索軟體是惡意程式的一種類型

**顯示格式**：`{child} 是 {parent} 的一種類型`

### variant_of（是...的變體）

同一事物的不同版本。

**範例**：
- LockBit 3.0 是 LockBit 的新版本

**顯示格式**：`{child} 是 {parent} 的變體版本`

### alias_of（是...的別名）

完全相同的概念，只是不同名稱。

**注意**：別名應記錄在 `aliases` 欄位，不建立獨立術語。

**範例**：
- Cozy Bear 是 APT29 的別名（不需獨立術語）

### related_to（與...相關）

概念上相關但無從屬關係。

**範例**：
- 勒索軟體與資料外洩相關

**顯示格式**：`{term_a} 與 {term_b} 相關`

## 判斷流程決策樹

```
新發現的術語
    │
    ▼
Q1: 是現有術語的別名嗎？
    │
    ├── 是 → 加入 aliases 欄位，不建新術語
    │
    └── 否 ↓

Q2: 是具體組織/軟體/事件嗎？
    │
    ├── 是 → relationship: instance_of
    │
    └── 否 ↓

Q3: 是概念的子分類嗎？
    │
    ├── 是 → relationship: subtype_of
    │
    └── 否 ↓

Q4: 是術語的新版本嗎？
    │
    ├── 是 → relationship: variant_of
    │
    └── 否 → relationship: related_to 或獨立術語
```

## 常見判斷範例

| 術語 | 判斷 | 結果 |
|------|------|------|
| Cozy Bear | APT29 的別名 | 加入 apt29.aliases.en |
| APT29 | APT 的具體組織 | parent_term: apt, relationship: instance_of |
| 魚叉式釣魚 | 釣魚的子分類 | parent_term: phishing, relationship: subtype_of |
| LockBit 3.0 | LockBit 的新版本 | parent_term: lockbit, relationship: variant_of |
| Scattered Spider | 獨立的犯罪組織 | 獨立術語，category: threat_actors/cybercrime_group |
