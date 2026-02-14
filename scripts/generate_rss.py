#!/usr/bin/env python3
"""RSS Feed 生成腳本

讀取週報 JSON 檔案，產生 RSS 2.0 feed。

用法：
    python scripts/generate_rss.py [--output-dir docs] [--max-items 20]
"""

import argparse
import html
import json
from datetime import datetime
from email.utils import format_datetime
from pathlib import Path
from zoneinfo import ZoneInfo

SITE_URL = "https://astroicers.github.io/security-glossary-tw/weekly"
FEED_TITLE = "資安週報 | Security Weekly TW"
FEED_DESCRIPTION = "台灣資安週報，每週更新最新資安威脅、漏洞與新聞"
TIMEZONE = ZoneInfo("Asia/Taipei")


def parse_publish_date(date_str: str) -> datetime:
    """解析發布日期字串為 datetime 物件"""
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    return dt.replace(tzinfo=TIMEZONE)


def format_description(report: dict) -> str:
    """格式化 RSS item 的 description"""
    summary = report.get("summary", {})
    events = report.get("events", [])

    threat_level_map = {
        "normal": "一般",
        "elevated": "升高",
        "high": "高",
        "critical": "嚴重",
    }
    threat_level = threat_level_map.get(summary.get("threat_level", "normal"), "一般")

    total_events = summary.get("total_events", 0)
    total_vulns = summary.get("total_vulnerabilities", 0)

    lines = [
        f"威脅等級：{threat_level}",
        f"本週收錄 {total_events} 則事件、{total_vulns} 個漏洞",
        "",
    ]

    # 取前 3 則重要新聞
    top_events = events[:3]
    if top_events:
        lines.append("重點新聞：")
        for event in top_events:
            title = event.get("title", "")
            # 移除 emoji 並截斷過長標題
            title = title.lstrip(" \u26a1\u2728\u2757\u274c\u2705")
            if len(title) > 60:
                title = title[:57] + "..."
            lines.append(f"• {title}")

    return "\n".join(lines)


def generate_rss_xml(items: list[dict], build_date: datetime) -> str:
    """生成 RSS 2.0 XML"""
    feed_url = f"{SITE_URL}/feed.xml"

    xml_lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">',
        "  <channel>",
        f"    <title>{html.escape(FEED_TITLE)}</title>",
        f"    <link>{SITE_URL}/</link>",
        f"    <description>{html.escape(FEED_DESCRIPTION)}</description>",
        "    <language>zh-TW</language>",
        f'    <atom:link href="{feed_url}" rel="self" type="application/rss+xml"/>',
        f"    <lastBuildDate>{format_datetime(build_date)}</lastBuildDate>",
        "    <generator>security-weekly-mcp RSS Generator</generator>",
    ]

    for item in items:
        pub_date = parse_publish_date(item["publish_date"])
        description = format_description(item)
        report_id = item["report_id"]

        # 使用 report_id 作為 permalink
        item_link = f"{SITE_URL}/reports/{report_id}.html"

        xml_lines.extend([
            "    <item>",
            f"      <title>{html.escape(item['title'])}</title>",
            f"      <link>{item_link}</link>",
            f'      <guid isPermaLink="false">{report_id}</guid>',
            f"      <pubDate>{format_datetime(pub_date)}</pubDate>",
            f"      <description>{html.escape(description)}</description>",
            "    </item>",
        ])

    xml_lines.extend([
        "  </channel>",
        "</rss>",
    ])

    return "\n".join(xml_lines)


def main():
    parser = argparse.ArgumentParser(description="Generate RSS feed from weekly reports")
    parser.add_argument("--output-dir", type=str, default="docs", help="Output directory")
    parser.add_argument("--max-items", type=int, default=20, help="Maximum items in feed")
    parser.add_argument(
        "--reports-dir", type=str, default="output/reports", help="Reports directory"
    )
    args = parser.parse_args()

    reports_dir = Path(args.reports_dir)
    output_dir = Path(args.output_dir)

    # 掃描週報 JSON 檔案
    report_files = sorted(reports_dir.glob("SEC-WEEKLY-*.json"), reverse=True)

    if not report_files:
        print(f"找不到週報檔案: {reports_dir}/SEC-WEEKLY-*.json")
        return 1

    print("=== RSS Feed 生成 ===")
    print(f"找到 {len(report_files)} 份週報")

    # 讀取並解析報告
    items = []
    for report_file in report_files:
        with open(report_file, encoding="utf-8") as f:
            data = json.load(f)
            items.append(data)

    # 按發布日期排序（最新在前）
    items.sort(key=lambda x: x.get("publish_date", ""), reverse=True)

    # 取最新 N 篇
    items = items[: args.max_items]
    print(f"納入 RSS: {len(items)} 篇")

    # 生成 RSS XML
    build_date = datetime.now(TIMEZONE)
    rss_xml = generate_rss_xml(items, build_date)

    # 確保輸出目錄存在
    output_dir.mkdir(parents=True, exist_ok=True)

    # 寫入 feed.xml
    feed_path = output_dir / "feed.xml"
    feed_path.write_text(rss_xml, encoding="utf-8")

    print(f"已生成: {feed_path}")
    print(f"檔案大小: {feed_path.stat().st_size / 1024:.1f} KB")

    return 0


if __name__ == "__main__":
    exit(main())
