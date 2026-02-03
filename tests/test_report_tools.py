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


class TestCompileReportPdf:
    """compile_report_pdf 工具測試

    注意：需要安裝 Typst
    """

    @pytest.mark.asyncio
    async def test_compile_requires_data(self):
        """編譯需要 report_data"""
        # 這個測試檢查工具會正確處理輸入
        result = await report.call_tool(
            "compile_report_pdf",
            {
                "report_data": {
                    "title": "測試",
                    "report_id": "TEST-001",
                    "period": {"start": "2026-01-01", "end": "2026-01-07"},
                    "publish_date": "2026-01-08",
                    "summary": {"total_events": 0, "total_vulnerabilities": 0, "threat_level": "normal"},
                    "events": [],
                    "vulnerabilities": [],
                    "threat_trends": {},
                    "action_items": [],
                    "terms": [],
                    "references": []
                }
            }
        )
        assert len(result) == 1
        # 即使 Typst 未安裝，也應該儲存 typ 和 json 檔案
        text = result[0].text
        assert "TEST-001" in text or "typst" in text.lower()
