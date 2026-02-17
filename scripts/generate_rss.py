#!/usr/bin/env python3
"""RSS Feed 與週報 HTML 生成腳本

讀取週報 JSON 檔案，產生：
1. RSS 2.0 feed (feed.xml)
2. 每篇週報的 HTML 頁面 (reports/*.html)

用法：
    python scripts/generate_rss.py [--output-dir docs] [--max-items 20]
"""

import argparse
import html
import json
import sys
from datetime import datetime
from email.utils import format_datetime
from pathlib import Path
from zoneinfo import ZoneInfo

# 專案根目錄
PROJECT_ROOT = Path(__file__).parent.parent

# 引入術語庫（需動態加入 path，因此無法放在檔案頂端）
sys.path.insert(0, str(PROJECT_ROOT / "packages" / "glossary" / "src"))
from security_glossary_tw import Glossary  # noqa: E402

# 初始化術語庫
GLOSSARY = Glossary(terms_dir=PROJECT_ROOT / "packages" / "glossary" / "terms")
GLOSSARY_BASE_URL = "https://astroicers.github.io/security-glossary-tw/glossary"

SITE_URL = "https://astroicers.github.io/security-glossary-tw/weekly"
FEED_TITLE = "資安週報 | Security Weekly TW"


def add_term_links_html(text: str, linked_terms: set) -> tuple[str, set, list]:
    """為文本中的術語加上 HTML 連結（只為首次出現的術語加連結）

    Args:
        text: 要處理的文本
        linked_terms: 已經連結過的術語 ID 集合

    Returns:
        tuple: (處理後的文本, 更新後的已連結術語集合, 本次新連結的術語資訊列表)
    """
    if not text:
        return text, linked_terms, []

    # 找出文本中的所有術語
    matches = GLOSSARY.find_terms(text)
    if not matches:
        return text, linked_terms, []

    # 按位置從後往前處理，避免位置偏移
    matches_sorted = sorted(matches, key=lambda m: m.start, reverse=True)

    new_terms = []
    result = text

    for match in matches_sorted:
        # 只為首次出現的術語加連結
        if match.term_id in linked_terms:
            continue

        term = GLOSSARY.get(match.term_id)
        if not term:
            continue

        # 記錄新連結的術語
        linked_terms.add(match.term_id)
        new_terms.append({
            "id": term.id,
            "term_en": term.term_en,
            "term_zh": term.term_zh,
            "definition": term.definitions.brief if term.definitions else "",
        })

        # 生成連結 HTML
        term_url = f"{GLOSSARY_BASE_URL}/{term.id}"
        tooltip = html.escape(term.term_zh or term.term_en)
        matched_text = result[match.start:match.end]
        link_html = f'<a href="{term_url}" class="term-link" title="{tooltip}">{html.escape(matched_text)}</a>'

        # 替換文本
        result = result[:match.start] + link_html + result[match.end:]

    return result, linked_terms, new_terms
FEED_DESCRIPTION = "台灣資安週報，每週更新最新資安威脅、漏洞與新聞"
TIMEZONE = ZoneInfo("Asia/Taipei")


def parse_publish_date(date_str: str) -> datetime:
    """解析發布日期字串為 datetime 物件"""
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    return dt.replace(tzinfo=TIMEZONE)


def extract_terms_from_report(report: dict) -> list[dict]:
    """從週報內容中提取術語（用於 RSS 摘要）"""
    linked_terms: set = set()
    all_terms: list = []

    # 掃描事件摘要
    for event in report.get("events", []):
        _, linked_terms, new_terms = add_term_links_html(
            event.get("summary", ""), linked_terms
        )
        all_terms.extend(new_terms)

    # 掃描漏洞標題
    for vuln in report.get("vulnerabilities", []):
        _, linked_terms, new_terms = add_term_links_html(
            vuln.get("title", ""), linked_terms
        )
        all_terms.extend(new_terms)

    # 去重
    seen = set()
    unique_terms = []
    for term in all_terms:
        if term["id"] not in seen:
            seen.add(term["id"])
            unique_terms.append(term)

    return unique_terms


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

    # 加入本期術語摘要
    terms = extract_terms_from_report(report)
    if terms:
        lines.append("")
        term_names = [t.get("term_en") or t.get("term_zh", "") for t in terms[:5]]
        lines.append(f"相關術語：{', '.join(term_names)}")

    return "\n".join(lines)


def generate_report_html(report: dict) -> str:
    """生成單篇週報的 HTML 頁面"""
    title = report.get("title", "資安週報")
    report_id = report.get("report_id", "")
    period = report.get("period", {})
    summary = report.get("summary", {})
    events = report.get("events", [])
    vulnerabilities = report.get("vulnerabilities", [])
    action_items = report.get("action_items", [])

    threat_level_map = {
        "normal": ("一般", "#22c55e"),
        "elevated": ("升高", "#eab308"),
        "high": ("高", "#f97316"),
        "critical": ("嚴重", "#ef4444"),
    }
    threat_level, threat_color = threat_level_map.get(
        summary.get("threat_level", "normal"), ("一般", "#22c55e")
    )

    # 追蹤已連結的術語（首次出現才連結）
    linked_terms: set = set()
    all_linked_terms: list = []

    # 生成事件列表 HTML（加入術語連結）
    events_html = ""
    for event in events:
        event_title = event.get("title", "")
        event_summary = event.get("summary", "")[:200]
        event_source = html.escape(event.get("source", ""))
        event_url = event.get("url", "#")
        event_date = event.get("date", "")[:10]

        # 為事件摘要加術語連結
        linked_summary, linked_terms, new_terms = add_term_links_html(event_summary, linked_terms)
        all_linked_terms.extend(new_terms)

        events_html += f"""
        <div class="event-card">
            <h3><a href="{event_url}" target="_blank" rel="noopener">{html.escape(event_title)}</a></h3>
            <p class="event-meta">{event_source} · {event_date}</p>
            <p>{linked_summary}...</p>
        </div>
        """

    # 生成漏洞列表 HTML（加入術語連結）
    vulns_html = ""
    for vuln in vulnerabilities[:10]:  # 限制顯示 10 個
        cve_id = html.escape(vuln.get("cve_id", ""))
        vuln_title = vuln.get("title", "")[:100]
        severity = vuln.get("severity", "low")
        cvss = vuln.get("cvss", 0)

        # 為漏洞標題加術語連結
        linked_vuln_title, linked_terms, new_terms = add_term_links_html(vuln_title, linked_terms)
        all_linked_terms.extend(new_terms)

        severity_colors = {
            "critical": "#ef4444",
            "high": "#f97316",
            "medium": "#eab308",
            "low": "#22c55e",
        }
        sev_color = severity_colors.get(severity, "#64748b")

        vulns_html += f"""
        <tr>
            <td><a href="https://nvd.nist.gov/vuln/detail/{cve_id}" target="_blank">{cve_id}</a></td>
            <td>{linked_vuln_title}...</td>
            <td style="color: {sev_color}; font-weight: 600;">{severity.upper()}</td>
            <td>{cvss if cvss > 0 else "N/A"}</td>
        </tr>
        """

    # 生成行動建議 HTML（加入術語連結）
    actions_html = ""
    for item in action_items:
        priority = item.get("priority", "low")
        action = item.get("action", "")
        priority_icons = {"high": "🔴", "medium": "🟡", "low": "🟢"}
        icon = priority_icons.get(priority, "⚪")

        # 為行動建議加術語連結
        linked_action, linked_terms, new_terms = add_term_links_html(action, linked_terms)
        all_linked_terms.extend(new_terms)

        actions_html += f"<li>{icon} {linked_action}</li>\n"

    # 生成「本期術語」區塊 HTML
    terms_html = ""
    if all_linked_terms:
        # 去重並保持順序
        seen = set()
        unique_terms = []
        for term in all_linked_terms:
            if term["id"] not in seen:
                seen.add(term["id"])
                unique_terms.append(term)

        terms_cards = ""
        for term in unique_terms[:10]:  # 最多顯示 10 個術語
            term_url = f"{GLOSSARY_BASE_URL}/{term['id']}"
            term_en = html.escape(term.get("term_en", ""))
            term_zh = html.escape(term.get("term_zh", ""))
            term_def = html.escape(term.get("definition", ""))

            terms_cards += f"""
            <div class="term-card">
                <h3><a href="{term_url}" target="_blank">{term_en}</a></h3>
                <p class="term-zh">{term_zh}</p>
                <p class="term-def">{term_def}</p>
            </div>
            """

        terms_html = f"""
        <section class="terms-section">
            <h2>📚 本期術語 ({len(unique_terms)})</h2>
            <div class="terms-grid">
                {terms_cards}
            </div>
        </section>
        """

    return f"""<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{html.escape(title)}</title>
    <meta name="description" content="資安週報 {period.get('start', '')} - {period.get('end', '')}">
    <link rel="alternate" type="application/rss+xml" title="資安週報 RSS" href="../feed.xml">
    <style>
        :root {{
            --primary: #2563eb;
            --bg: #f8fafc;
            --text: #1e293b;
            --text-muted: #64748b;
            --border: #e2e8f0;
            --card-bg: #ffffff;
        }}
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background: var(--bg);
            color: var(--text);
            line-height: 1.6;
            padding: 2rem 1rem;
        }}
        .container {{ max-width: 900px; margin: 0 auto; }}
        header {{ margin-bottom: 2rem; }}
        h1 {{ font-size: 1.75rem; margin-bottom: 0.5rem; }}
        .meta {{ color: var(--text-muted); margin-bottom: 1rem; }}
        .back-link {{ color: var(--primary); text-decoration: none; display: inline-block; margin-bottom: 1.5rem; }}
        .back-link:hover {{ text-decoration: underline; }}
        .summary-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 1rem;
            margin-bottom: 2rem;
        }}
        .summary-card {{
            background: var(--card-bg);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 1rem;
            text-align: center;
        }}
        .summary-card .value {{ font-size: 1.5rem; font-weight: 700; }}
        .summary-card .label {{ color: var(--text-muted); font-size: 0.875rem; }}
        section {{ margin-bottom: 2rem; }}
        h2 {{ font-size: 1.25rem; margin-bottom: 1rem; padding-bottom: 0.5rem; border-bottom: 2px solid var(--border); }}
        .event-card {{
            background: var(--card-bg);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 1rem;
            margin-bottom: 1rem;
        }}
        .event-card h3 {{ font-size: 1rem; margin-bottom: 0.25rem; }}
        .event-card h3 a {{ color: var(--text); text-decoration: none; }}
        .event-card h3 a:hover {{ color: var(--primary); }}
        .event-meta {{ color: var(--text-muted); font-size: 0.875rem; margin-bottom: 0.5rem; }}
        table {{ width: 100%; border-collapse: collapse; background: var(--card-bg); border-radius: 8px; overflow: hidden; }}
        th, td {{ padding: 0.75rem; text-align: left; border-bottom: 1px solid var(--border); }}
        th {{ background: var(--bg); font-weight: 600; }}
        td a {{ color: var(--primary); text-decoration: none; }}
        td a:hover {{ text-decoration: underline; }}
        .actions {{ background: var(--card-bg); border: 1px solid var(--border); border-radius: 8px; padding: 1rem; }}
        .actions ul {{ list-style: none; }}
        .actions li {{ padding: 0.5rem 0; }}
        /* 術語連結樣式 */
        .term-link {{
            color: var(--primary);
            text-decoration: underline dotted;
            text-underline-offset: 2px;
            cursor: help;
        }}
        .term-link:hover {{
            text-decoration: underline solid;
        }}
        /* 本期術語區塊樣式 */
        .terms-section {{
            margin-top: 2rem;
            padding: 1.5rem;
            background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
            border-radius: 12px;
            border: 1px solid #bae6fd;
        }}
        .terms-section h2 {{
            border-bottom-color: #7dd3fc;
        }}
        .terms-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
            gap: 1rem;
        }}
        .term-card {{
            background: var(--card-bg);
            padding: 1rem;
            border-radius: 8px;
            border-left: 3px solid var(--primary);
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }}
        .term-card h3 {{
            font-size: 1rem;
            margin-bottom: 0.25rem;
        }}
        .term-card h3 a {{
            color: var(--primary);
            text-decoration: none;
        }}
        .term-card h3 a:hover {{
            text-decoration: underline;
        }}
        .term-zh {{
            color: var(--text-muted);
            font-size: 0.9rem;
            margin-bottom: 0.5rem;
        }}
        .term-def {{
            font-size: 0.85rem;
            color: var(--text);
            line-height: 1.5;
        }}
        footer {{ margin-top: 3rem; text-align: center; color: var(--text-muted); font-size: 0.875rem; }}
        footer a {{ color: var(--primary); text-decoration: none; }}
    </style>
</head>
<body>
    <div class="container">
        <a href="../" class="back-link">&larr; 返回週報列表</a>

        <header>
            <h1>{html.escape(title)}</h1>
            <p class="meta">報告編號：{report_id} · 發布日期：{report.get('publish_date', '')}</p>
        </header>

        <div class="summary-grid">
            <div class="summary-card">
                <div class="value" style="color: {threat_color};">{threat_level}</div>
                <div class="label">威脅等級</div>
            </div>
            <div class="summary-card">
                <div class="value">{summary.get('total_events', 0)}</div>
                <div class="label">資安事件</div>
            </div>
            <div class="summary-card">
                <div class="value">{summary.get('total_vulnerabilities', 0)}</div>
                <div class="label">漏洞數量</div>
            </div>
        </div>

        <section>
            <h2>行動建議</h2>
            <div class="actions">
                <ul>
                    {actions_html if actions_html else '<li>本週無特別行動建議</li>'}
                </ul>
            </div>
        </section>

        <section>
            <h2>資安新聞 ({len(events)})</h2>
            {events_html if events_html else '<p>本週無重要資安新聞</p>'}
        </section>

        <section>
            <h2>漏洞追蹤 ({len(vulnerabilities)})</h2>
            {f'''<table>
                <thead>
                    <tr><th>CVE ID</th><th>描述</th><th>嚴重性</th><th>CVSS</th></tr>
                </thead>
                <tbody>{vulns_html}</tbody>
            </table>''' if vulns_html else '<p>本週無重要漏洞</p>'}
        </section>

        {terms_html}

        <footer>
            <p>
                <a href="../feed.xml">訂閱 RSS</a> ·
                由 <a href="https://github.com/AstroicerS/security-weekly-mcp">security-weekly-mcp</a> 生成
            </p>
        </footer>
    </div>
</body>
</html>
"""


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

    print("=== RSS Feed 與週報頁面生成 ===")
    print(f"找到 {len(report_files)} 份週報")

    # 讀取並解析報告
    items = []
    for report_file in report_files:
        with open(report_file, encoding="utf-8") as f:
            data = json.load(f)
            items.append(data)

    # 按發布日期排序（最新在前）
    items.sort(key=lambda x: x.get("publish_date", ""), reverse=True)

    # 確保輸出目錄存在
    output_dir.mkdir(parents=True, exist_ok=True)
    reports_output_dir = output_dir / "reports"
    reports_output_dir.mkdir(parents=True, exist_ok=True)

    # 生成每篇週報的 HTML 頁面
    print("\n生成週報 HTML 頁面...")
    for item in items:
        report_id = item.get("report_id", "unknown")
        report_html = generate_report_html(item)
        report_path = reports_output_dir / f"{report_id}.html"
        report_path.write_text(report_html, encoding="utf-8")
        print(f"  - {report_path.name}")

    # 取最新 N 篇納入 RSS
    rss_items = items[: args.max_items]
    print(f"\n納入 RSS: {len(rss_items)} 篇")

    # 生成 RSS XML
    build_date = datetime.now(TIMEZONE)
    rss_xml = generate_rss_xml(rss_items, build_date)

    # 寫入 feed.xml
    feed_path = output_dir / "feed.xml"
    feed_path.write_text(rss_xml, encoding="utf-8")

    print("\n已生成:")
    print(f"  - {feed_path} ({feed_path.stat().st_size / 1024:.1f} KB)")
    print(f"  - {len(items)} 個週報 HTML 頁面")

    return 0


if __name__ == "__main__":
    exit(main())
