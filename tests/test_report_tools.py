"""週報 MCP 工具單元測試"""

import json
import pytest

from security_weekly_mcp.tools import report


class TestGenerateReportDraft:
    """generate_report_draft 工具測試"""

    @pytest.mark.asyncio
    async def test_generate_minimal(self):
        """產生最小週報草稿"""
        result = await report.call_tool(
            "generate_report_draft",
            {
                "title": "測試週報",
                "period_start": "2026-01-01",
                "period_end": "2026-01-07"
            }
        )
        assert len(result) == 1

        data = json.loads(result[0].text)
        assert data["title"] == "測試週報"
        assert "report_id" in data
        assert "SEC-WEEKLY-2026-01" in data["report_id"]
        assert data["period"]["start"] == "2026-01-01"
        assert data["period"]["end"] == "2026-01-07"

    @pytest.mark.asyncio
    async def test_generate_with_events(self):
        """產生包含事件的週報草稿"""
        result = await report.call_tool(
            "generate_report_draft",
            {
                "title": "資安週報",
                "period_start": "2026-01-01",
                "period_end": "2026-01-07",
                "events": [
                    {
                        "title": "測試事件",
                        "severity": "high",
                        "event_type": "資料外洩",
                        "summary": "測試摘要"
                    }
                ]
            }
        )
        assert len(result) == 1

        data = json.loads(result[0].text)
        assert data["summary"]["total_events"] == 1
        assert len(data["events"]) == 1
        assert data["events"][0]["title"] == "測試事件"

    @pytest.mark.asyncio
    async def test_threat_level_elevated(self):
        """測試威脅等級計算 - 升高"""
        result = await report.call_tool(
            "generate_report_draft",
            {
                "title": "週報",
                "period_start": "2026-01-01",
                "period_end": "2026-01-07",
                "events": [
                    {"title": "事件1", "severity": "critical"}
                ]
            }
        )
        data = json.loads(result[0].text)
        assert data["summary"]["threat_level"] == "elevated"

    @pytest.mark.asyncio
    async def test_threat_level_normal(self):
        """測試威脅等級計算 - 正常"""
        result = await report.call_tool(
            "generate_report_draft",
            {
                "title": "週報",
                "period_start": "2026-01-01",
                "period_end": "2026-01-07",
                "events": [
                    {"title": "事件1", "severity": "low"}
                ]
            }
        )
        data = json.loads(result[0].text)
        assert data["summary"]["threat_level"] == "normal"


class TestListReports:
    """list_reports 工具測試"""

    @pytest.mark.asyncio
    async def test_list_reports(self):
        """列出已產生的週報"""
        result = await report.call_tool("list_reports", {"limit": 10})
        assert len(result) == 1
        # 可能有或沒有報告，但應該要有回傳
        text = result[0].text
        assert text is not None


class TestGenerateReportDraftAdvanced:
    """generate_report_draft 進階測試"""

    @pytest.mark.asyncio
    async def test_generate_with_vulnerabilities(self):
        """產生包含漏洞的週報草稿"""
        result = await report.call_tool(
            "generate_report_draft",
            {
                "title": "週報",
                "period_start": "2026-01-01",
                "period_end": "2026-01-07",
                "vulnerabilities": [
                    {"cve_id": "CVE-2026-0001", "cvss": 9.8, "severity": "critical"},
                    {"cve_id": "CVE-2026-0002", "cvss": 7.5, "severity": "high"}
                ]
            }
        )
        data = json.loads(result[0].text)
        assert data["summary"]["total_vulnerabilities"] == 2
        assert len(data["vulnerabilities"]) == 2

    @pytest.mark.asyncio
    async def test_generate_with_terms(self):
        """產生包含術語的週報草稿"""
        result = await report.call_tool(
            "generate_report_draft",
            {
                "title": "週報",
                "period_start": "2026-01-01",
                "period_end": "2026-01-07",
                "terms": [
                    {"term": "APT", "definition": "進階持續性威脅"},
                    {"term": "Zero-day", "definition": "零時差漏洞"}
                ]
            }
        )
        data = json.loads(result[0].text)
        assert len(data["terms"]) == 2

    @pytest.mark.asyncio
    async def test_generate_with_action_items(self):
        """產生包含行動項目的週報草稿"""
        result = await report.call_tool(
            "generate_report_draft",
            {
                "title": "週報",
                "period_start": "2026-01-01",
                "period_end": "2026-01-07",
                "action_items": [
                    {"priority": "P1", "action": "修補關鍵漏洞"},
                    {"priority": "P2", "action": "更新防火牆規則"}
                ]
            }
        )
        data = json.loads(result[0].text)
        assert len(data["action_items"]) == 2
