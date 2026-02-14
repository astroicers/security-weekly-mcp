# Config 設定檔說明

本目錄包含 Security Weekly MCP 的設定檔。

## 檔案清單

| 檔案 | 用途 | 使用者 |
|------|------|--------|
| `sources.yaml` | 新聞來源設定 | `fetch_security_news`, `list_news_sources` |
| `search_templates.yaml` | WebSearch 查詢模板 | `suggest_searches` |
| `writing_style.yaml` | 週報寫作風格 | Claude 提示詞 |

---

## sources.yaml

定義 32 個資安新聞來源。

### 結構

```yaml
sources:
  - name: "The Hacker News"       # 來源名稱
    type: "rss"                    # 類型: rss | api | manual
    url: "https://..."             # RSS URL
    category: "news"               # 分類: news | advisory | intelligence
    priority: "high"               # 優先級: critical | high | medium | low
    language: "en"                 # 語言: en | zh-TW
    status: "active"               # 狀態: active | disabled
    note: "說明文字"               # 備註（可選）
```

### 優先級說明

- `critical` - 必須包含，如 CISA、TWCERT
- `high` - 優先收集
- `medium` - 一般收集
- `low` - 僅在有相關內容時收集

### 新增來源

1. 在適當分類下新增條目
2. 確保 URL 可存取
3. 執行 `monthly-health.yml` 驗證

---

## search_templates.yaml

定義 WebSearch 查詢模板，用於 `suggest_searches` 工具。

### 結構

```yaml
taiwan_news:
  queries:
    - query: "site:twcert.org.tw 資安通報 {year}"
      priority: "critical"
      category: "taiwan"
      note: "TWCERT/CC 官方公告"

variables:
  year: 2026
  month: 2
  month_zh: "二月"
```

### 動態變數

- `{year}` - 當前年份
- `{month}` - 當前月份
- `{month_zh}` - 中文月份
- `{cve_id}` - CVE ID（來自 context）

---

## writing_style.yaml

定義週報寫作風格規範。

### 結構

```yaml
core_principles:
  - title: "客觀與精準"
    description: "使用確切數據，避免誇大"

avoid_patterns:
  - pattern: "令人震驚"
    reason: "避免誇大"
    alternative: "值得注意"

forbidden_words:
  - term: "黑客"
    use: "駭客"
```

### 風格規則

- 客觀精準，使用確切數據
- 避免 AI 痕跡（「值得注意的是」等）
- 使用台灣繁體中文慣用語
- 禁止使用中國用語（如「黑客」→「駭客」）

---

## 修改設定

1. 編輯對應 YAML 檔案
2. 執行測試確認格式正確：
   ```bash
   uv run pytest tests/test_sources_integration.py -v
   ```
3. 提交變更

## 驗證

```bash
# 驗證 sources.yaml
uv run python -c "
import yaml
with open('config/sources.yaml') as f:
    data = yaml.safe_load(f)
print(f'來源數量: {len(data[\"sources\"])}')"

# 驗證 search_templates.yaml
uv run python -c "
import yaml
with open('config/search_templates.yaml') as f:
    data = yaml.safe_load(f)
for cat in data:
    print(f'{cat}: {len(data[cat].get(\"queries\", []))} 個查詢')"
```
