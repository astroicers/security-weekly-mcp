#!/usr/bin/env python3
"""週報自動產生腳本

用於 GitHub Actions 或手動執行，產生資安週報 PDF。

用法：
    python scripts/generate_weekly_report.py --days 7 --output-dir output/reports
"""

import argparse
import asyncio
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path


async def main():
    parser = argparse.ArgumentParser(description="Generate security weekly report")
    parser.add_argument("--days", type=int, default=7, help="Days to collect news")
    parser.add_argument("--output-dir", type=str, default="output/reports", help="Output directory")
    parser.add_argument("--min-cvss", type=float, default=7.0, help="Minimum CVSS score")
    args = parser.parse_args()

    # Import MCP tools
    from security_weekly_mcp.tools import news, report

    print(f"=== 資安週報產生 ===")
    print(f"收集天數: {args.days}")
    print(f"輸出目錄: {args.output_dir}")
    print()

    # 計算日期範圍
    end_date = datetime.now()
    start_date = end_date - timedelta(days=args.days)

    # 1. 收集新聞
    print("📰 收集資安新聞...")
    news_result = await news.call_tool(
        "fetch_security_news",
        {"days": args.days, "limit": 50}
    )
    news_data = json.loads(news_result[0].text) if news_result else {}
    news_count = sum(len(items) for items in news_data.values() if isinstance(items, list))
    print(f"   收集到 {news_count} 則新聞")

    # 2. 收集漏洞
    print("🔒 收集漏洞資訊...")
    vuln_result = await news.call_tool(
        "fetch_vulnerabilities",
        {"min_cvss": args.min_cvss, "days": args.days, "include_kev": True, "limit": 20}
    )
    vuln_data = json.loads(vuln_result[0].text) if vuln_result else {}
    nvd_count = len(vuln_data.get("nvd", []))
    kev_count = len(vuln_data.get("kev", []))
    print(f"   NVD: {nvd_count} 個漏洞, KEV: {kev_count} 個漏洞")

    # 3. 整理事件
    events = []
    for source, items in news_data.items():
        if not isinstance(items, list):
            continue
        for item in items[:5]:  # 每個來源最多 5 則
            events.append({
                "title": item.get("title", "未知標題"),
                "severity": "medium",
                "event_type": "資安新聞",
                "summary": item.get("summary", "")[:200],
                "source": source,
                "date": item.get("published", ""),
                "url": item.get("link", "")
            })

    # 4. 整理漏洞
    vulnerabilities = []
    for vuln in vuln_data.get("nvd", [])[:10]:
        affected = vuln.get("affected_products", [])
        product = affected[0] if affected else "未知產品"
        vulnerabilities.append({
            "cve_id": vuln.get("cve_id", ""),
            "title": vuln.get("description", "")[:100],
            "cvss": vuln.get("cvss", 0),
            "severity": _cvss_to_severity(vuln.get("cvss", 0)),
            "product": product,
            "recommendation": "請參閱 NVD 更新資訊"
        })

    # 5. 產生週報草稿
    print("📝 產生週報草稿...")
    report_result = await report.call_tool(
        "generate_report_draft",
        {
            "title": f"資安週報 {start_date.strftime('%Y/%m/%d')} - {end_date.strftime('%Y/%m/%d')}",
            "period_start": start_date.strftime("%Y-%m-%d"),
            "period_end": end_date.strftime("%Y-%m-%d"),
            "events": events[:15],  # 最多 15 個事件
            "vulnerabilities": vulnerabilities,
            "action_items": [
                {"priority": "high", "action": "檢視本週高風險漏洞並評估影響"},
                {"priority": "medium", "action": "確認系統已套用最新安全更新"},
                {"priority": "low", "action": "持續監控資安威脅趨勢"}
            ]
        }
    )
    report_data = json.loads(report_result[0].text)
    print(f"   週報 ID: {report_data.get('report_id', 'N/A')}")

    # 6. 編譯 PDF
    print("📄 編譯 PDF...")
    pdf_result = await report.call_tool(
        "compile_report_pdf",
        {"report_data": report_data, "output_dir": args.output_dir}
    )
    print(f"   {pdf_result[0].text}")

    print()
    print("✅ 週報產生完成！")

    return 0


def _cvss_to_severity(cvss: float) -> str:
    if cvss >= 9.0:
        return "critical"
    elif cvss >= 7.0:
        return "high"
    elif cvss >= 4.0:
        return "medium"
    else:
        return "low"


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
