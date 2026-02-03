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
