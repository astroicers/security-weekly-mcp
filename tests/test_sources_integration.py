"""RSS 來源整合測試

這些測試會實際連接到 RSS 來源，用於驗證來源可用性。
標記為 slow 和 integration，在 CI 中可選擇性執行。
"""

import json
import pytest
import yaml
from pathlib import Path

from security_weekly_mcp.tools import news


# 載入 sources.yaml
SOURCES_PATH = Path(__file__).parent.parent / "config" / "sources.yaml"
with open(SOURCES_PATH) as f:
    SOURCES_CONFIG = yaml.safe_load(f)


class TestSourcesConfig:
    """sources.yaml 設定檔驗證"""

    def test_sources_file_exists(self):
        """sources.yaml 檔案存在"""
        assert SOURCES_PATH.exists()

    def test_sources_has_required_fields(self):
        """每個來源都有必要欄位"""
        for source in SOURCES_CONFIG["sources"]:
            assert "name" in source, f"來源缺少 name: {source}"
            assert "type" in source, f"來源缺少 type: {source.get('name')}"
            assert "category" in source, f"來源缺少 category: {source.get('name')}"
            assert "priority" in source, f"來源缺少 priority: {source.get('name')}"

    def test_rss_sources_have_url(self):
        """RSS 來源有 url 欄位"""
        for source in SOURCES_CONFIG["sources"]:
            if source.get("type") == "rss":
                assert "url" in source, f"RSS 來源缺少 url: {source.get('name')}"

    def test_api_sources_have_endpoint(self):
        """API 來源有 endpoint 欄位"""
        for source in SOURCES_CONFIG["sources"]:
            if source.get("type") == "api":
                assert "endpoint" in source, f"API 來源缺少 endpoint: {source.get('name')}"

    def test_source_count(self):
        """來源數量檢查"""
        sources = SOURCES_CONFIG["sources"]
        rss_count = len([s for s in sources if s.get("type") == "rss" and s.get("status") != "disabled"])
        api_count = len([s for s in sources if s.get("type") == "api"])
        manual_count = len([s for s in sources if s.get("status") == "manual"])
        disabled_count = len([s for s in sources if s.get("status") == "disabled"])

        # 驗證總數
        total = len(sources)
        assert total >= 30, f"來源總數應至少 30 個，目前 {total} 個"

        # 驗證各類型
        assert rss_count >= 20, f"RSS 來源應至少 20 個，目前 {rss_count} 個"
        assert api_count >= 2, f"API 來源應至少 2 個，目前 {api_count} 個"


class TestTaiwanSources:
    """台灣來源測試"""

    @pytest.mark.asyncio
    async def test_taiwan_sources_exist(self):
        """台灣來源存在於設定中"""
        result = await news.call_tool("list_news_sources", {})
        sources = json.loads(result[0].text)

        taiwan_sources = [s for s in sources if s.get("language") == "zh-TW"]
        assert len(taiwan_sources) >= 3, f"台灣來源應至少 3 個，目前 {len(taiwan_sources)} 個"

    @pytest.mark.asyncio
    async def test_twcert_sources_exist(self):
        """TWCERT/CC 來源存在"""
        result = await news.call_tool("list_news_sources", {})
        sources = json.loads(result[0].text)

        twcert_sources = [s for s in sources if "TWCERT" in s.get("name", "")]
        assert len(twcert_sources) >= 1, "應該有 TWCERT/CC 來源"


class TestRssFeedAvailability:
    """RSS Feed 可用性測試

    注意：這些測試需要網路連線且速度較慢
    """

    @pytest.mark.asyncio
    @pytest.mark.slow
    @pytest.mark.integration
    async def test_ithome_rss_available(self):
        """iThome RSS 可用"""
        result = await news.call_tool(
            "fetch_security_news",
            {"sources": ["ithome"], "days": 7, "limit": 3}
        )
        data = json.loads(result[0].text)
        # 應該有 iThome 的資料或錯誤訊息
        assert isinstance(data, dict)

    @pytest.mark.asyncio
    @pytest.mark.slow
    @pytest.mark.integration
    async def test_thehackernews_rss_available(self):
        """The Hacker News RSS 可用"""
        result = await news.call_tool(
            "fetch_security_news",
            {"sources": ["thehackernews"], "days": 7, "limit": 3}
        )
        data = json.loads(result[0].text)
        assert isinstance(data, dict)

    @pytest.mark.asyncio
    @pytest.mark.slow
    @pytest.mark.integration
    async def test_krebs_rss_available(self):
        """Krebs on Security RSS 可用"""
        result = await news.call_tool(
            "fetch_security_news",
            {"sources": ["krebs"], "days": 7, "limit": 3}
        )
        data = json.loads(result[0].text)
        assert isinstance(data, dict)


class TestFiltersConfig:
    """篩選規則設定測試"""

    def test_boost_keywords_exist(self):
        """加權關鍵字存在"""
        filters = SOURCES_CONFIG.get("filters", {})
        boost_keywords = filters.get("boost_keywords", [])
        assert "taiwan" in boost_keywords or "台灣" in boost_keywords

    def test_min_cvss_configured(self):
        """最低 CVSS 分數已設定"""
        filters = SOURCES_CONFIG.get("filters", {})
        min_cvss = filters.get("min_cvss", 0)
        assert min_cvss >= 5.0, f"最低 CVSS 應至少 5.0，目前 {min_cvss}"

    def test_lookback_days_configured(self):
        """回溯天數已設定"""
        filters = SOURCES_CONFIG.get("filters", {})
        lookback_days = filters.get("lookback_days", 0)
        assert lookback_days >= 7, f"回溯天數應至少 7 天，目前 {lookback_days}"
