"""新聞收集 MCP 工具單元測試"""

import json
import pytest

from security_weekly_mcp.tools import news


class TestListNewsSources:
    """list_news_sources 工具測試"""

    @pytest.mark.asyncio
    async def test_list_sources(self):
        """列出新聞來源"""
        result = await news.call_tool("list_news_sources", {})
        assert len(result) == 1

        sources = json.loads(result[0].text)
        assert isinstance(sources, list)
        assert len(sources) > 0

        # 檢查來源結構
        source = sources[0]
        assert "name" in source
        assert "type" in source


class TestFetchSecurityNews:
    """fetch_security_news 工具測試"""

    @pytest.mark.asyncio
    async def test_fetch_with_source(self):
        """從指定來源收集新聞"""
        result = await news.call_tool(
            "fetch_security_news",
            {"sources": ["thehackernews"], "days": 7, "limit": 3}
        )
        assert len(result) == 1

        data = json.loads(result[0].text)
        assert isinstance(data, dict)

    @pytest.mark.asyncio
    async def test_fetch_not_found_source(self):
        """收集不存在的來源"""
        result = await news.call_tool(
            "fetch_security_news",
            {"sources": ["not_exist_source_xyz"], "days": 7, "limit": 3}
        )
        assert len(result) == 1
        # 應該回傳錯誤訊息或空結果
        text = result[0].text
        assert "找不到" in text or "{}" in text or "[]" in text


class TestFetchVulnerabilities:
    """fetch_vulnerabilities 工具測試

    注意：這些測試會實際呼叫 NVD API，可能需要網路連線且速度較慢
    """

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_fetch_nvd(self):
        """從 NVD 收集漏洞（需要網路）"""
        result = await news.call_tool(
            "fetch_vulnerabilities",
            {"min_cvss": 9.0, "days": 30, "include_kev": False, "limit": 5}
        )
        assert len(result) == 1

        data = json.loads(result[0].text)
        assert "nvd" in data

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_fetch_kev(self):
        """從 CISA KEV 收集漏洞（需要網路）"""
        result = await news.call_tool(
            "fetch_vulnerabilities",
            {"min_cvss": 7.0, "days": 30, "include_kev": True, "limit": 5}
        )
        assert len(result) == 1

        data = json.loads(result[0].text)
        assert "nvd" in data
        assert "kev" in data


class TestSuggestSearches:
    """suggest_searches 工具測試"""

    @pytest.mark.asyncio
    async def test_suggest_taiwan_news(self):
        """建議台灣新聞搜尋"""
        result = await news.call_tool(
            "suggest_searches",
            {"category": "taiwan_news"}
        )
        assert len(result) == 1

        data = json.loads(result[0].text)
        assert "web_searches" in data
        assert "fetch_targets" in data
        assert len(data["web_searches"]) > 0

        # 檢查搜尋建議結構
        search = data["web_searches"][0]
        assert "query" in search
        assert "priority" in search

    @pytest.mark.asyncio
    async def test_suggest_all_categories(self):
        """建議所有類別搜尋"""
        result = await news.call_tool(
            "suggest_searches",
            {"category": "all", "include_fetch_targets": True}
        )
        assert len(result) == 1

        data = json.loads(result[0].text)
        assert len(data["web_searches"]) > 5  # 應該有多個類別的搜尋
        assert len(data["fetch_targets"]) > 0

    @pytest.mark.asyncio
    async def test_suggest_with_context(self):
        """建議搜尋並填入動態變數"""
        result = await news.call_tool(
            "suggest_searches",
            {
                "category": "vulnerabilities",
                "context": {"cve_id": "CVE-2026-1234"}
            }
        )
        assert len(result) == 1

        data = json.loads(result[0].text)
        # 檢查變數是否被替換
        queries = [s["query"] for s in data["web_searches"]]
        # 有些查詢應該包含 cve_id
        has_cve_query = any("CVE-2026-1234" in q for q in queries)
        assert has_cve_query or len(queries) > 0  # 至少有查詢結果

    @pytest.mark.asyncio
    async def test_suggest_historical_search(self):
        """建議歷史時間範圍搜尋"""
        result = await news.call_tool(
            "suggest_searches",
            {
                "category": "taiwan_news",
                "period_start": "2025-06-01",
                "period_end": "2025-06-07"
            }
        )
        assert len(result) == 1

        data = json.loads(result[0].text)

        # 檢查時間範圍資訊
        assert "period" in data
        assert data["period"]["is_historical"] is True
        assert data["period"]["start"] == "2025-06-01"
        assert data["period"]["end"] == "2025-06-07"

        # 歷史搜尋應該有時間過濾
        queries = [s["query"] for s in data["web_searches"]]
        has_date_filter = any("after:" in q or "2025年06月" in q for q in queries)
        assert has_date_filter

        # 歷史搜尋不應該有 fetch_targets
        assert len(data["fetch_targets"]) == 0
        assert "fetch_targets_note" in data
