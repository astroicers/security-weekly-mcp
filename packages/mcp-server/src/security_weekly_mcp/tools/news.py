"""新聞收集 MCP 工具"""

import json
from datetime import datetime, timedelta
from typing import Any
from pathlib import Path

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
    ]


def _load_sources_config() -> dict:
    """載入來源設定"""
    import yaml
    sources_file = CONFIG_DIR / "sources.yaml"
    if sources_file.exists():
        return yaml.safe_load(sources_file.read_text(encoding="utf-8"))
    return {"sources": []}


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
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, follow_redirects=True)
            response.raise_for_status()
            feed = feedparser.parse(response.text)
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
            result.append({
                "name": source.get("name"),
                "type": source.get("type"),
                "category": source.get("category"),
                "priority": source.get("priority"),
                "language": source.get("language")
            })

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

        # 過濾 RSS 類型的來源
        rss_sources = [s for s in all_sources if s.get("type") == "rss"]

        # 如果有指定來源，進行比對
        if requested_sources:
            matched_sources = []
            for query in requested_sources:
                matched_sources.extend(_match_source(query, rss_sources))
            rss_sources = matched_sources

        if not rss_sources:
            return [TextContent(type="text", text="找不到符合的 RSS 來源")]

        # 收集所有來源的新聞
        all_articles = {}
        for source in rss_sources:
            source_name = source.get("name", "Unknown")
            url = source.get("url", "")
            if not url:
                continue

            articles = await _fetch_rss(url, days, limit, keywords)
            all_articles[source_name] = articles

        return [TextContent(
            type="text",
            text=json.dumps(all_articles, ensure_ascii=False, indent=2)
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

    return [TextContent(type="text", text=f"未知工具：{name}")]
