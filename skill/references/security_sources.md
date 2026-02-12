# 資安資源清單

本專案已設定 **32 個** 資安來源，包括 27 個 RSS、3 個 API 端點，以及 2 個需手動處理的來源。
搜尋資安新聞時，優先使用以下來源。

> **來源設定檔**: `config/sources.yaml`

## 來源統計

| 類型 | 數量 | 說明 |
|------|------|------|
| RSS Feed | 27 | 自動抓取 |
| API | 3 | NVD、CISA KEV、GitHub Advisory |
| 手動/WebFetch | 1 | 資安人 |
| 已停用 | 1 | BleepingComputer (Cloudflare 防護) |

---

## 台灣來源 (5 個)

| 來源 | 類型 | 優先級 | URL |
|------|------|--------|-----|
| iThome 資安 | RSS | high | https://www.ithome.com.tw/rss/security |
| TWCERT/CC 資安新聞 | RSS | **critical** | https://www.twcert.org.tw/tw/rss-104-1.xml |
| TWCERT/CC 漏洞公告 | RSS | **critical** | https://www.twcert.org.tw/tw/rss-132-1.xml |
| TechNews 資安 | RSS | high | https://infosecu.technews.tw/feed/ |
| 資安人 | WebFetch | medium | https://www.informationsecurity.com.tw/ |

## 國際資安新聞 (8 個)

| 來源 | 類型 | 優先級 | 說明 |
|------|------|--------|------|
| The Hacker News | RSS | high | 全球知名資安新聞 |
| Krebs on Security | RSS | high | 知名資安記者部落格 |
| SecurityWeek | RSS | medium | 資安產業新聞 |
| Dark Reading | RSS | medium | 企業資安新聞 |
| Schneier on Security | RSS | high | Bruce Schneier 部落格 |
| Infosecurity Magazine | RSS | high | 獲獎資安媒體 |
| CyberScoop | RSS | high | 政策與資安新聞 |
| ~~BleepingComputer~~ | ~~RSS~~ | ~~high~~ | 已停用 (Cloudflare) |

## 官方公告 (4 個)

| 來源 | 類型 | 優先級 | 說明 |
|------|------|--------|------|
| CISA Alerts | RSS | **critical** | 美國 CISA 資安公告 |
| CERT/CC Vulnerability Notes | RSS | high | 卡內基美隆大學 CERT |
| CIS MS-ISAC Advisories | RSS | high | 網際網路安全中心 |
| CISA KEV | API | **critical** | 已知遭利用漏洞目錄 |

## 漏洞資料庫 (2 個)

| 來源 | 類型 | 優先級 | 說明 |
|------|------|--------|------|
| NVD | API | high | 美國國家漏洞資料庫 |
| GitHub Security Advisories | API | medium | GitHub 安全公告 |

## 威脅情報 (12 個)

| 來源 | 類型 | 優先級 | 說明 |
|------|------|--------|------|
| Mandiant Blog | RSS | high | Google 旗下威脅情報 |
| Microsoft Security Blog | RSS | high | Microsoft 資安部落格 |
| Unit 42 | RSS | high | Palo Alto Networks |
| Recorded Future | RSS | high | 威脅情報領導者 |
| Check Point Research | RSS | high | Check Point 威脅研究 |
| CrowdStrike Blog | RSS | high | CrowdStrike 威脅情報 |
| SentinelOne Blog | RSS | high | SentinelLabs 研究 |
| Securelist (Kaspersky) | RSS | high | 卡巴斯基 GReAT 團隊 |
| Sophos Blog | RSS | medium | 威脅研究報告 |
| Google Security Blog | RSS | medium | Google 官方安全部落格 |
| WeLiveSecurity (ESET) | RSS | medium | ESET 威脅研究 |
| Elastic Security Labs | RSS | medium | Elastic 安全研究 |

## 廠商公告 (1 個)

| 來源 | 類型 | 優先級 | 說明 |
|------|------|--------|------|
| Microsoft MSRC | RSS | high | Microsoft 安全回應中心 |

---

## 來源優先級說明

| 優先級 | 分數 | 類型 | 說明 |
|--------|------|------|------|
| Critical | 100 | 重大漏洞 | CISA KEV、已遭實際利用的漏洞 |
| High | 75 | 主要來源 | 主要資安新聞、NVD 高嚴重性 CVE |
| Medium | 50 | 一般來源 | 一般資安新聞 |
| Low | 25 | 背景資訊 | 參考用途 |

## 提高優先級的關鍵詞

以下關鍵詞出現時會自動提高新聞優先級：

```yaml
boost_keywords:
  - taiwan, 台灣
  - 金融, 製造, 政府
  - critical, zero-day, actively exploited
  - CISA KEV, emergency directive
  - ransomware, data breach, supply chain
```

---

## 補充資源（手動查詢用）

以下資源未納入自動抓取，但可用於深入調查：

### APT 追蹤

| 來源 | URL | 說明 |
|------|-----|------|
| MITRE ATT&CK Groups | https://attack.mitre.org/groups/ | APT 組織資料庫 |
| Malpedia | https://malpedia.caad.fkie.fraunhofer.de/ | 惡意程式百科 |

### 勒索軟體追蹤

| 來源 | URL | 說明 |
|------|-----|------|
| Ransomware.live | https://www.ransomware.live/ | 勒索軟體即時追蹤 |
| Ransomlook | https://www.ransomlook.io/ | 受害者追蹤 |

### 惡意程式分析

| 來源 | URL | 說明 |
|------|-----|------|
| VirusTotal | https://www.virustotal.com/ | 多引擎掃描 |
| Any.Run | https://any.run/ | 互動式沙箱 |
| MalwareBazaar | https://bazaar.abuse.ch/ | 樣本庫 |

### 漏洞資料庫

| 來源 | URL | 說明 |
|------|-----|------|
| CVE | https://cve.mitre.org/ | CVE 官方網站 |
| Exploit-DB | https://www.exploit-db.com/ | 漏洞利用程式庫 |
| VulDB | https://vuldb.com/ | 漏洞情報資料庫 |
