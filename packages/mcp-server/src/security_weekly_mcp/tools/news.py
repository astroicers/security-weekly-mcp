"""新聞收集 MCP 工具"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import feedparser
import httpx
from mcp.types import TextContent, Tool

# 配置檔案路徑
CONFIG_DIR = Path(__file__).parent.parent.parent.parent.parent.parent / "config"


async def list_tools() -> list[Tool]:
    """列出新聞收集相關工具"""
    return [
        Tool(
            name="fetch_security_news",
            description="從 RSS 來源收集資安新聞",
            inputSchema={
                "type": "object",
                "properties": {
                    "sources": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "來源名稱列表（如 thehackernews, bleepingcomputer, ithome）。留空則使用所有來源。"
                    },
                    "days": {
                        "type": "integer",
                        "description": "回顧天數",
                        "default": 7
                    },
                    "keywords": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "關鍵字過濾（符合任一即可）"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "每個來源的最大文章數",
                        "default": 10
                    }
                }
            }
        ),
        Tool(
            name="fetch_vulnerabilities",
            description="收集近期高風險漏洞（NVD + CISA KEV）",
            inputSchema={
                "type": "object",
                "properties": {
                    "min_cvss": {
                        "type": "number",
                        "description": "最低 CVSS 分數",
                        "default": 7.0
                    },
                    "days": {
                        "type": "integer",
                        "description": "回顧天數",
                        "default": 7
                    },
                    "include_kev": {
                        "type": "boolean",
                        "description": "是否包含 CISA KEV（已知被利用漏洞）",
                        "default": True
                    },
                    "limit": {
                        "type": "integer",
                        "description": "最大回傳數量",
                        "default": 20
                    }
                }
            }
        ),
        Tool(
            name="list_news_sources",
            description="列出可用的新聞來源",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="suggest_searches",
            description="產生 WebSearch/WebFetch 搜尋建議，用於補充 RSS 無法取得的資安新聞。支援歷史時間範圍搜尋。",
            inputSchema={
                "type": "object",
                "properties": {
                    "category": {
                        "type": "string",
                        "enum": ["taiwan_news", "vulnerabilities", "threat_intel", "industry_specific", "all"],
                        "description": "搜尋類別",
                        "default": "all"
                    },
                    "period_start": {
                        "type": "string",
                        "description": "搜尋起始日期 (YYYY-MM-DD)，用於產生歷史週報",
                    },
                    "period_end": {
                        "type": "string",
                        "description": "搜尋結束日期 (YYYY-MM-DD)，用於產生歷史週報",
                    },
                    "context": {
                        "type": "object",
                        "description": "動態內容（如 cve_id, ransomware_name, apt_group）",
                        "additionalProperties": {"type": "string"}
                    },
                    "include_fetch_targets": {
                        "type": "boolean",
                        "description": "是否包含 WebFetch 目標網址",
                        "default": True
                    }
                }
            }
        ),
        Tool(
            name="load_weekly_data",
            description="載入已保存的週報原始資料（由 GitHub Actions 每週自動收集）",
            inputSchema={
                "type": "object",
                "properties": {
                    "week": {
                        "type": "string",
                        "description": "週數（格式：YYYY-WNN，如 2026-W07）。留空則載入最新一週。"
                    }
                }
            }
        ),
        Tool(
            name="list_weekly_data",
            description="列出所有已保存的週報原始資料",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
    ]


# 設定檔快取
_sources_cache = None
_templates_cache = None


def _load_sources_config() -> dict:
    """載入來源設定（快取）"""
    global _sources_cache
    if _sources_cache is None:
        import yaml
        sources_file = CONFIG_DIR / "sources.yaml"
        if sources_file.exists():
            _sources_cache = yaml.safe_load(sources_file.read_text(encoding="utf-8"))
        else:
            _sources_cache = {"sources": []}
    return _sources_cache


def _load_search_templates() -> dict:
    """載入搜尋模板設定（快取）"""
    global _templates_cache
    if _templates_cache is None:
        import yaml
        templates_file = CONFIG_DIR / "search_templates.yaml"
        if templates_file.exists():
            _templates_cache = yaml.safe_load(templates_file.read_text(encoding="utf-8"))
        else:
            _templates_cache = {}
    return _templates_cache


def reset_config_cache():
    """重設設定檔快取（用於測試）"""
    global _sources_cache, _templates_cache
    _sources_cache = None
    _templates_cache = None


def _normalize_source_name(name: str) -> str:
    """標準化來源名稱以便比對"""
    return name.lower().replace(" ", "").replace("_", "").replace("-", "")


def _match_source(query: str, sources: list[dict]) -> list[dict]:
    """根據查詢字串比對來源"""
    query_normalized = _normalize_source_name(query)
    matched = []
    for source in sources:
        source_normalized = _normalize_source_name(source["name"])
        if query_normalized in source_normalized or source_normalized in query_normalized:
            matched.append(source)
    return matched


async def _fetch_rss(url: str, days: int, limit: int, keywords: list[str] | None = None) -> list[dict]:
    """從 RSS 來源抓取文章"""
    # 設定 User-Agent 以避免被某些網站封鎖 (如 BleepingComputer)
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/rss+xml, application/xml, text/xml, */*",
    }
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, headers=headers, follow_redirects=True)
            response.raise_for_status()
            feed = feedparser.parse(response.text)
    except httpx.TimeoutException:
        return [{"error": "RSS 抓取超時 (30s)"}]
    except httpx.HTTPStatusError as e:
        return [{"error": f"HTTP {e.response.status_code}: {e.response.reason_phrase}"}]
    except httpx.RequestError as e:
        return [{"error": f"網路請求失敗: {type(e).__name__}"}]
    except Exception as e:
        return [{"error": f"無法抓取 RSS: {e}"}]

    cutoff_date = datetime.now() - timedelta(days=days)
    articles = []

    for entry in feed.entries[:limit * 2]:  # 抓多一點再過濾
        # 解析發布時間
        published = None
        if hasattr(entry, "published_parsed") and entry.published_parsed:
            published = datetime(*entry.published_parsed[:6])
        elif hasattr(entry, "updated_parsed") and entry.updated_parsed:
            published = datetime(*entry.updated_parsed[:6])

        # 時間過濾
        if published and published < cutoff_date:
            continue

        # 關鍵字過濾
        if keywords:
            title = entry.get("title", "").lower()
            summary = entry.get("summary", "").lower()
            content = title + " " + summary
            if not any(kw.lower() in content for kw in keywords):
                continue

        articles.append({
            "title": entry.get("title", ""),
            "link": entry.get("link", ""),
            "published": published.isoformat() if published else None,
            "summary": entry.get("summary", "")[:500]  # 摘要截斷
        })

        if len(articles) >= limit:
            break

    return articles


async def _fetch_nvd(min_cvss: float, days: int, limit: int) -> list[dict]:
    """從 NVD 抓取漏洞資料"""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)

    params = {
        "pubStartDate": start_date.strftime("%Y-%m-%dT00:00:00.000"),
        "pubEndDate": end_date.strftime("%Y-%m-%dT23:59:59.999"),
        "cvssV3Severity": "HIGH" if min_cvss >= 7.0 else "MEDIUM",
        "resultsPerPage": min(limit, 50)
    }

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.get(
                "https://services.nvd.nist.gov/rest/json/cves/2.0",
                params=params,
                headers={"Accept": "application/json"}
            )
            response.raise_for_status()
            data = response.json()
    except httpx.TimeoutException:
        return [{"error": "NVD API 超時 (60s)"}]
    except httpx.HTTPStatusError as e:
        return [{"error": f"NVD API HTTP {e.response.status_code}"}]
    except httpx.RequestError as e:
        return [{"error": f"NVD API 網路錯誤: {type(e).__name__}"}]
    except json.JSONDecodeError:
        return [{"error": "NVD API 回傳非 JSON 格式"}]
    except Exception as e:
        return [{"error": f"NVD API 錯誤: {e}"}]

    vulnerabilities = []
    for item in data.get("vulnerabilities", []):
        cve = item.get("cve", {})
        cve_id = cve.get("id", "")

        # 取得 CVSS 分數
        cvss_score = 0.0
        cvss_vector = ""
        metrics = cve.get("metrics", {})
        if "cvssMetricV31" in metrics:
            cvss_data = metrics["cvssMetricV31"][0].get("cvssData", {})
            cvss_score = cvss_data.get("baseScore", 0.0)
            cvss_vector = cvss_data.get("vectorString", "")
        elif "cvssMetricV30" in metrics:
            cvss_data = metrics["cvssMetricV30"][0].get("cvssData", {})
            cvss_score = cvss_data.get("baseScore", 0.0)
            cvss_vector = cvss_data.get("vectorString", "")

        if cvss_score < min_cvss:
            continue

        # 取得描述
        descriptions = cve.get("descriptions", [])
        description = ""
        for desc in descriptions:
            if desc.get("lang") == "en":
                description = desc.get("value", "")
                break

        vulnerabilities.append({
            "cve_id": cve_id,
            "cvss": cvss_score,
            "cvss_vector": cvss_vector,
            "description": description[:500],
            "published": cve.get("published", ""),
            "url": f"https://nvd.nist.gov/vuln/detail/{cve_id}"
        })

    return vulnerabilities[:limit]


async def _fetch_cisa_kev(days: int, limit: int) -> list[dict]:
    """從 CISA KEV 抓取已知被利用漏洞"""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                "https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json"
            )
            response.raise_for_status()
            data = response.json()
    except httpx.TimeoutException:
        return [{"error": "CISA KEV 超時 (30s)"}]
    except httpx.HTTPStatusError as e:
        return [{"error": f"CISA KEV HTTP {e.response.status_code}"}]
    except httpx.RequestError as e:
        return [{"error": f"CISA KEV 網路錯誤: {type(e).__name__}"}]
    except json.JSONDecodeError:
        return [{"error": "CISA KEV 回傳非 JSON 格式"}]
    except Exception as e:
        return [{"error": f"CISA KEV API 錯誤: {e}"}]

    cutoff_date = datetime.now() - timedelta(days=days)
    vulnerabilities = []

    for vuln in data.get("vulnerabilities", []):
        # 解析加入日期
        date_added = vuln.get("dateAdded", "")
        try:
            added_date = datetime.strptime(date_added, "%Y-%m-%d")
            if added_date < cutoff_date:
                continue
        except ValueError:
            continue

        vulnerabilities.append({
            "cve_id": vuln.get("cveID", ""),
            "vendor": vuln.get("vendorProject", ""),
            "product": vuln.get("product", ""),
            "name": vuln.get("vulnerabilityName", ""),
            "description": vuln.get("shortDescription", ""),
            "date_added": date_added,
            "due_date": vuln.get("dueDate", ""),
            "in_kev": True,
            "url": f"https://nvd.nist.gov/vuln/detail/{vuln.get('cveID', '')}"
        })

        if len(vulnerabilities) >= limit:
            break

    return vulnerabilities


async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """執行新聞收集工具"""

    if name == "list_news_sources":
        config = _load_sources_config()
        sources = config.get("sources", [])

        result = []
        for source in sources:
            item = {
                "name": source.get("name"),
                "type": source.get("type"),
                "category": source.get("category"),
                "priority": source.get("priority"),
                "language": source.get("language"),
            }
            # 如果有 status 或 note，加入顯示
            if source.get("status"):
                item["status"] = source.get("status")
            if source.get("note"):
                item["note"] = source.get("note")
            result.append(item)

        return [TextContent(
            type="text",
            text=json.dumps(result, ensure_ascii=False, indent=2)
        )]

    elif name == "fetch_security_news":
        config = _load_sources_config()
        all_sources = config.get("sources", [])
        days = arguments.get("days", 7)
        limit = arguments.get("limit", 10)
        keywords = arguments.get("keywords")
        requested_sources = arguments.get("sources", [])

        # 過濾 RSS 類型的來源（排除 disabled 的來源）
        rss_sources = [
            s for s in all_sources
            if s.get("type") == "rss" and s.get("status") != "disabled"
        ]

        # 如果有指定來源，進行比對
        if requested_sources:
            matched_sources = []
            for query in requested_sources:
                matched_sources.extend(_match_source(query, rss_sources))
            rss_sources = matched_sources

        if not rss_sources:
            return [TextContent(type="text", text="找不到符合的 RSS 來源")]

        # 並行抓取所有來源的新聞（大幅提升效能）
        import asyncio

        async def fetch_source(source: dict) -> tuple[str, list[dict]]:
            source_name = source.get("name", "Unknown")
            url = source.get("url", "")
            if not url:
                return source_name, []
            articles = await _fetch_rss(url, days, limit, keywords)
            return source_name, articles

        # 使用 asyncio.gather 並行抓取
        tasks = [fetch_source(s) for s in rss_sources]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        all_articles = {}
        failed_sources = []
        for i, result in enumerate(results):
            source_name = rss_sources[i].get("name", f"來源 {i+1}")
            if isinstance(result, Exception):
                failed_sources.append({
                    "source": source_name,
                    "error": f"{type(result).__name__}: {result}"
                })
                continue
            name, articles = result
            all_articles[name] = articles

        # 在結果中加入統計和失敗資訊
        response = {
            "_meta": {
                "total_sources": len(rss_sources),
                "success": len(all_articles),
                "failed": len(failed_sources)
            }
        }
        response.update(all_articles)
        if failed_sources:
            response["_failed"] = failed_sources

        return [TextContent(
            type="text",
            text=json.dumps(response, ensure_ascii=False, indent=2)
        )]

    elif name == "fetch_vulnerabilities":
        min_cvss = arguments.get("min_cvss", 7.0)
        days = arguments.get("days", 7)
        include_kev = arguments.get("include_kev", True)
        limit = arguments.get("limit", 20)

        result = {
            "nvd": [],
            "kev": []
        }

        # 從 NVD 抓取
        result["nvd"] = await _fetch_nvd(min_cvss, days, limit)

        # 從 CISA KEV 抓取
        if include_kev:
            result["kev"] = await _fetch_cisa_kev(days, limit)

        # 合併並標記 KEV 狀態
        kev_cves = {v["cve_id"] for v in result["kev"] if "cve_id" in v}
        for vuln in result["nvd"]:
            vuln["in_kev"] = vuln["cve_id"] in kev_cves

        return [TextContent(
            type="text",
            text=json.dumps(result, ensure_ascii=False, indent=2)
        )]

    elif name == "suggest_searches":
        category = arguments.get("category", "all")
        context = arguments.get("context", {})
        include_fetch_targets = arguments.get("include_fetch_targets", True)
        period_start = arguments.get("period_start")
        period_end = arguments.get("period_end")

        # 載入搜尋模板
        search_templates = _load_search_templates()
        if not search_templates:
            return [TextContent(type="text", text="找不到搜尋模板配置檔")]

        # 解析時間範圍
        now = datetime.now()
        if period_start:
            try:
                start_date = datetime.strptime(period_start, "%Y-%m-%d")
            except ValueError:
                start_date = now - timedelta(days=7)
        else:
            start_date = now - timedelta(days=7)

        if period_end:
            try:
                end_date = datetime.strptime(period_end, "%Y-%m-%d")
            except ValueError:
                end_date = now
        else:
            end_date = now

        # 準備動態變數
        variables = {
            "year": str(start_date.year),
            "month": start_date.strftime("%B"),
            "month_zh": _month_to_chinese(start_date.month),
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d"),
            "date_range": f"{start_date.strftime('%Y/%m/%d')}~{end_date.strftime('%Y/%m/%d')}",
            **context
        }

        # 判斷是否為歷史搜尋
        is_historical = (now - end_date).days > 7

        result = {
            "web_searches": [],
            "fetch_targets": [],
            "period": {
                "start": start_date.strftime("%Y-%m-%d"),
                "end": end_date.strftime("%Y-%m-%d"),
                "is_historical": is_historical
            }
        }

        # 收集搜尋建議
        categories_to_process = (
            [category] if category != "all"
            else ["taiwan_news", "vulnerabilities", "threat_intel", "industry_specific"]
        )

        for cat in categories_to_process:
            cat_data = search_templates.get(cat, {})
            queries = cat_data.get("queries", [])
            for q in queries:
                query_template = q.get("query", "")
                # 替換變數
                try:
                    query = query_template.format(**variables)
                except KeyError:
                    # 如果有未提供的變數，跳過此查詢
                    continue

                # 對於歷史搜尋，加入時間範圍限定
                if is_historical:
                    # 加入 Google 時間過濾語法
                    date_filter = f" after:{start_date.strftime('%Y-%m-%d')} before:{end_date.strftime('%Y-%m-%d')}"
                    query = query + date_filter

                result["web_searches"].append({
                    "query": query,
                    "priority": q.get("priority", "medium"),
                    "category": q.get("category", cat),
                    "note": q.get("note")
                })

        # 對於歷史搜尋，加入額外的時間限定搜尋
        if is_historical:
            historical_queries = [
                {
                    "query": f"台灣 資安事件 {start_date.strftime('%Y年%m月')}",
                    "priority": "high",
                    "category": "news",
                    "note": "歷史時間範圍搜尋"
                },
                {
                    "query": f"cybersecurity incident {start_date.strftime('%B %Y')}",
                    "priority": "high",
                    "category": "news",
                    "note": "歷史時間範圍搜尋 (英文)"
                },
                {
                    "query": f"CVE {start_date.strftime('%Y-%m')} critical",
                    "priority": "high",
                    "category": "vulnerability",
                    "note": "該月份重大漏洞"
                },
            ]
            result["web_searches"].extend(historical_queries)

        # 收集 WebFetch 目標（歷史搜尋時不包含，因為網頁內容會是最新的）
        if include_fetch_targets and not is_historical:
            fetch_data = search_templates.get("fetch_targets", {})
            urls = fetch_data.get("urls", [])
            for target in urls:
                result["fetch_targets"].append({
                    "name": target.get("name"),
                    "url": target.get("url"),
                    "type": target.get("type"),
                    "priority": target.get("priority", "medium"),
                    "prompt": target.get("prompt")
                })
        elif is_historical:
            result["fetch_targets_note"] = "歷史週報不使用 WebFetch，因為網頁內容是最新的。請依賴 WebSearch 結果。"

        # 按優先級排序
        priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        result["web_searches"].sort(key=lambda x: priority_order.get(x["priority"], 99))
        if result["fetch_targets"]:
            result["fetch_targets"].sort(key=lambda x: priority_order.get(x["priority"], 99))

        return [TextContent(
            type="text",
            text=json.dumps(result, ensure_ascii=False, indent=2)
        )]

    elif name == "list_weekly_data":
        raw_dir = Path(__file__).parent.parent.parent.parent.parent.parent / "output" / "raw"

        if not raw_dir.exists():
            return [TextContent(type="text", text="尚無已保存的週報資料。GitHub Actions 會每週一自動收集。")]

        files = sorted(raw_dir.glob("*.json"), reverse=True)
        if not files:
            return [TextContent(type="text", text="尚無已保存的週報資料。")]

        result = {
            "available_weeks": [],
            "total_files": len(files),
            "storage_path": str(raw_dir)
        }

        for f in files:
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
                meta = data.get("metadata", {})
                result["available_weeks"].append({
                    "week": meta.get("week", f.stem),
                    "filename": f.name,
                    "collected_at": meta.get("collected_at", "unknown"),
                    "stats": meta.get("stats", {})
                })
            except Exception:
                result["available_weeks"].append({
                    "week": f.stem,
                    "filename": f.name,
                    "error": "無法解析檔案"
                })

        return [TextContent(
            type="text",
            text=json.dumps(result, ensure_ascii=False, indent=2)
        )]

    elif name == "load_weekly_data":
        raw_dir = Path(__file__).parent.parent.parent.parent.parent.parent / "output" / "raw"
        week = arguments.get("week")

        if not raw_dir.exists():
            return [TextContent(type="text", text="❌ 尚無已保存的週報資料。")]

        if week:
            # 載入指定週數
            target_file = raw_dir / f"{week}.json"
        else:
            # 載入最新一週
            files = sorted(raw_dir.glob("*.json"), reverse=True)
            if not files:
                return [TextContent(type="text", text="❌ 尚無已保存的週報資料。")]
            target_file = files[0]

        if not target_file.exists():
            return [TextContent(type="text", text=f"❌ 找不到週報資料：{target_file.name}")]

        try:
            data = json.loads(target_file.read_text(encoding="utf-8"))
            meta = data.get("metadata", {})

            # 回傳摘要 + 資料
            summary = f"""## 📊 週報原始資料：{meta.get('week', target_file.stem)}

**收集時間**: {meta.get('collected_at', 'unknown')}
**資料期間**: {meta.get('period', {}).get('start')} ~ {meta.get('period', {}).get('end')}

### 統計
- 新聞文章: {meta.get('stats', {}).get('total_articles', 0)} 則
- 新聞來源: {meta.get('stats', {}).get('news_sources', 0)} 個
- NVD 漏洞: {meta.get('stats', {}).get('nvd_vulnerabilities', 0)} 個
- KEV 漏洞: {meta.get('stats', {}).get('kev_vulnerabilities', 0)} 個
- 建議搜尋: {meta.get('stats', {}).get('suggested_searches', 0)} 個

### 使用方式
此資料已載入，你可以：
1. 分析新聞趨勢並撰寫摘要
2. 執行建議的 WebSearch 查詢補充最新資訊
3. 使用 `generate_report_draft` 產生週報

---
### 完整資料
"""
            return [TextContent(
                type="text",
                text=summary + json.dumps(data, ensure_ascii=False, indent=2)
            )]

        except Exception as e:
            return [TextContent(type="text", text=f"❌ 載入資料失敗：{e}")]


def _month_to_chinese(month: int) -> str:
    """將月份數字轉換為中文"""
    months = ["一月", "二月", "三月", "四月", "五月", "六月",
              "七月", "八月", "九月", "十月", "十一月", "十二月"]
    return months[month - 1] if 1 <= month <= 12 else str(month)
