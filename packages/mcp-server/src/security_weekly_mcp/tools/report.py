"""週報 MCP 工具"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from mcp.types import TextContent, Tool

# 專案根目錄
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent.parent.parent
OUTPUT_DIR = PROJECT_ROOT / "output" / "reports"


async def list_tools() -> list[Tool]:
    """列出週報相關工具"""
    return [
        Tool(
            name="generate_report_draft",
            description="產生週報結構化資料（JSON 格式）",
            inputSchema={
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "週報標題"
                    },
                    "period_start": {
                        "type": "string",
                        "description": "報告期間開始日期（YYYY-MM-DD）"
                    },
                    "period_end": {
                        "type": "string",
                        "description": "報告期間結束日期（YYYY-MM-DD）"
                    },
                    "events": {
                        "type": "array",
                        "description": "重大資安事件列表",
                        "items": {
                            "type": "object",
                            "properties": {
                                "title": {"type": "string"},
                                "severity": {"type": "string", "enum": ["critical", "high", "medium", "low"]},
                                "event_type": {"type": "string"},
                                "summary": {"type": "string"},
                                "affected_industries": {"type": "array", "items": {"type": "string"}},
                                "recommendations": {"type": "array", "items": {"type": "string"}}
                            }
                        }
                    },
                    "vulnerabilities": {
                        "type": "array",
                        "description": "漏洞列表",
                        "items": {
                            "type": "object",
                            "properties": {
                                "cve_id": {"type": "string"},
                                "product": {"type": "string"},
                                "cvss": {"type": "number"},
                                "status": {"type": "string"},
                                "priority": {"type": "string"}
                            }
                        }
                    },
                    "threat_trends": {
                        "type": "object",
                        "description": "威脅趨勢",
                        "properties": {
                            "summary": {"type": "string"},
                            "active_actors": {"type": "array", "items": {"type": "object"}},
                            "attack_techniques": {"type": "array", "items": {"type": "string"}}
                        }
                    },
                    "action_items": {
                        "type": "array",
                        "description": "行動項目",
                        "items": {
                            "type": "object",
                            "properties": {
                                "priority": {"type": "string", "enum": ["P1", "P2", "P3", "P4"]},
                                "action": {"type": "string"},
                                "owner": {"type": "string"},
                                "deadline": {"type": "string"}
                            }
                        }
                    },
                    "terms": {
                        "type": "array",
                        "description": "本期術語",
                        "items": {
                            "type": "object",
                            "properties": {
                                "term": {"type": "string"},
                                "definition": {"type": "string"},
                                "url": {"type": "string"}
                            }
                        }
                    },
                    "references": {
                        "type": "array",
                        "description": "參考資料",
                        "items": {
                            "type": "object",
                            "properties": {
                                "title": {"type": "string"},
                                "url": {"type": "string"}
                            }
                        }
                    }
                },
                "required": ["title", "period_start", "period_end"]
            }
        ),
        Tool(
            name="list_reports",
            description="列出已產生的週報",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "回傳數量限制",
                        "default": 10
                    }
                }
            }
        ),
    ]


def _get_week_number(date_str: str) -> str:
    """從日期字串取得週數"""
    date = datetime.strptime(date_str, "%Y-%m-%d")
    return f"{date.year}-{date.isocalendar()[1]:02d}"


async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """執行週報工具"""

    if name == "generate_report_draft":
        # 產生結構化週報資料
        report_data = {
            "title": arguments.get("title", "資安週報"),
            "report_id": f"SEC-WEEKLY-{_get_week_number(arguments['period_start'])}",
            "period": {
                "start": arguments["period_start"],
                "end": arguments["period_end"]
            },
            "publish_date": datetime.now().strftime("%Y-%m-%d"),
            "summary": {
                "total_events": len(arguments.get("events", [])),
                "total_vulnerabilities": len(arguments.get("vulnerabilities", [])),
                "threat_level": _calculate_threat_level(arguments)
            },
            "events": arguments.get("events", []),
            "vulnerabilities": arguments.get("vulnerabilities", []),
            "threat_trends": arguments.get("threat_trends", {}),
            "action_items": arguments.get("action_items", []),
            "terms": arguments.get("terms", []),
            "references": arguments.get("references", [])
        }

        return [TextContent(
            type="text",
            text=json.dumps(report_data, ensure_ascii=False, indent=2)
        )]

    elif name == "list_reports":
        limit = arguments.get("limit", 10)

        if not OUTPUT_DIR.exists():
            return [TextContent(type="text", text="尚無已產生的週報")]

        # 列出 JSON 檔案
        json_files = sorted(OUTPUT_DIR.glob("SEC-WEEKLY-*.json"), reverse=True)[:limit]

        if not json_files:
            return [TextContent(type="text", text="尚無已產生的週報")]

        reports = []
        for json_file in json_files:
            data = json.loads(json_file.read_text(encoding="utf-8"))
            reports.append({
                "filename": json_file.name,
                "report_id": data.get("report_id", json_file.stem),
                "period": data.get("period", {}),
                "publish_date": data.get("publish_date", "")
            })

        return [TextContent(
            type="text",
            text=json.dumps(reports, ensure_ascii=False, indent=2)
        )]

    return [TextContent(type="text", text=f"未知工具：{name}")]


def _calculate_threat_level(arguments: dict) -> str:
    """計算威脅等級"""
    events = arguments.get("events", [])
    vulns = arguments.get("vulnerabilities", [])

    # 檢查是否有危急事件
    critical_events = [e for e in events if e.get("severity") == "critical"]
    critical_vulns = [v for v in vulns if v.get("cvss", 0) >= 9.0]

    if critical_events or critical_vulns:
        return "elevated"  # 升高

    high_events = [e for e in events if e.get("severity") == "high"]
    high_vulns = [v for v in vulns if v.get("cvss", 0) >= 7.0]

    if len(high_events) >= 3 or len(high_vulns) >= 5:
        return "elevated"

    return "normal"  # 正常
