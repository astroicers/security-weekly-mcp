"""週報與 PDF 產生 MCP 工具"""

import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

from mcp.types import TextContent, Tool

# 專案根目錄
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent.parent.parent
TEMPLATES_DIR = PROJECT_ROOT / "templates" / "typst"
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
            name="compile_report_pdf",
            description="將週報資料編譯為 PDF（使用 Typst）",
            inputSchema={
                "type": "object",
                "properties": {
                    "report_data": {
                        "type": "object",
                        "description": "週報結構化資料（來自 generate_report_draft）"
                    },
                    "output_filename": {
                        "type": "string",
                        "description": "輸出檔名（不含副檔名，預設為 SEC-WEEKLY-YYYY-WW）"
                    },
                    "template": {
                        "type": "string",
                        "description": "模板名稱（預設為 weekly_report）",
                        "default": "weekly_report"
                    }
                },
                "required": ["report_data"]
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


def _generate_typst_content(report_data: dict) -> str:
    """將報告資料轉換為 Typst 格式"""
    # 匯入主模板（使用相對路徑從 output/reports/ 到 templates/typst/）
    content = '#import "../../templates/typst/weekly_report.typ": weekly-report, render-full-report\n\n'

    # 設定報告資料
    content += "#let report-data = (\n"
    content += _dict_to_typst(report_data)
    content += ")\n\n"

    # 呼叫完整報告渲染
    content += "#render-full-report(report-data)\n"

    return content


def _dict_to_typst(data, indent=2) -> str:
    """將 Python dict 轉換為 Typst dictionary 語法"""
    lines = []
    prefix = " " * indent

    if isinstance(data, dict):
        for key, value in data.items():
            # Typst 字典 key 需要用引號包裹
            if isinstance(value, dict):
                lines.append(f'{prefix}"{key}": (')
                lines.append(_dict_to_typst(value, indent + 2))
                lines.append(f'{prefix}),')
            elif isinstance(value, list):
                lines.append(f'{prefix}"{key}": (')
                for item in value:
                    if isinstance(item, dict):
                        lines.append(f'{prefix}  (')
                        lines.append(_dict_to_typst(item, indent + 4))
                        lines.append(f'{prefix}  ),')
                    elif isinstance(item, str):
                        lines.append(f'{prefix}  "{_escape_typst_string(item)}",')
                    else:
                        lines.append(f'{prefix}  {item},')
                lines.append(f'{prefix}),')
            elif isinstance(value, str):
                lines.append(f'{prefix}"{key}": "{_escape_typst_string(value)}",')
            elif isinstance(value, bool):
                lines.append(f'{prefix}"{key}": {"true" if value else "false"},')
            elif isinstance(value, (int, float)):
                lines.append(f'{prefix}"{key}": {value},')
            elif value is None:
                lines.append(f'{prefix}"{key}": none,')
            else:
                lines.append(f'{prefix}"{key}": "{_escape_typst_string(str(value))}",')

    return "\n".join(lines)


def _escape_typst_string(s: str) -> str:
    """轉義 Typst 字串中的特殊字元"""
    return s.replace("\\", "\\\\").replace('"', '\\"').replace("\n", " ")


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

    elif name == "compile_report_pdf":
        report_data = arguments["report_data"]

        # 確定輸出檔名
        if "output_filename" in arguments:
            filename = arguments["output_filename"]
        else:
            week = _get_week_number(report_data.get("period", {}).get("start", datetime.now().strftime("%Y-%m-%d")))
            filename = f"SEC-WEEKLY-{week}"

        # 確保輸出目錄存在
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

        # 產生 Typst 內容
        typst_content = _generate_typst_content(report_data)

        # 寫入暫存 Typst 檔案
        typst_file = OUTPUT_DIR / f"{filename}.typ"
        typst_file.write_text(typst_content, encoding="utf-8")

        # 寫入 JSON 資料檔
        json_file = OUTPUT_DIR / f"{filename}.json"
        json_file.write_text(json.dumps(report_data, ensure_ascii=False, indent=2), encoding="utf-8")

        # 編譯 PDF
        pdf_file = OUTPUT_DIR / f"{filename}.pdf"
        try:
            result = subprocess.run(
                ["typst", "compile", str(typst_file), str(pdf_file)],
                capture_output=True,
                text=True,
                cwd=str(TEMPLATES_DIR)  # 從模板目錄執行以便找到模板
            )

            if result.returncode != 0:
                return [TextContent(
                    type="text",
                    text=f"PDF 編譯失敗：\n{result.stderr}\n\n已儲存 Typst 檔案：{typst_file}"
                )]

            return [TextContent(
                type="text",
                text=f"PDF 產生成功：\n- PDF: {pdf_file}\n- Typst: {typst_file}\n- JSON: {json_file}"
            )]

        except FileNotFoundError:
            return [TextContent(
                type="text",
                text=f"找不到 typst 指令，請先安裝 Typst。\n\n已儲存：\n- Typst: {typst_file}\n- JSON: {json_file}"
            )]

    elif name == "list_reports":
        limit = arguments.get("limit", 10)

        if not OUTPUT_DIR.exists():
            return [TextContent(type="text", text="尚無已產生的週報")]

        # 列出 PDF 檔案
        pdf_files = sorted(OUTPUT_DIR.glob("SEC-WEEKLY-*.pdf"), reverse=True)[:limit]

        if not pdf_files:
            return [TextContent(type="text", text="尚無已產生的週報")]

        reports = []
        for pdf in pdf_files:
            json_file = pdf.with_suffix(".json")
            if json_file.exists():
                data = json.loads(json_file.read_text(encoding="utf-8"))
                reports.append({
                    "filename": pdf.name,
                    "report_id": data.get("report_id", pdf.stem),
                    "period": data.get("period", {}),
                    "publish_date": data.get("publish_date", "")
                })
            else:
                reports.append({
                    "filename": pdf.name,
                    "report_id": pdf.stem
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
