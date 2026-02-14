#!/usr/bin/env python3
"""週報資料收集腳本

每週自動執行，收集 RSS 和 API 資料並保存為 JSON。
這些資料是「揮發性」的，RSS feed 只保留最近幾天，所以需要定期保存。

用法：
    python scripts/collect_weekly_data.py --days 7 --output-dir output/raw
"""

import argparse
import asyncio
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path


async def main():
    parser = argparse.ArgumentParser(description="Collect weekly security data")
    parser.add_argument("--days", type=int, default=7, help="Days to collect news")
    parser.add_argument("--output-dir", type=str, default="output/raw", help="Output directory")
    parser.add_argument("--min-cvss", type=float, default=7.0, help="Minimum CVSS score")
    args = parser.parse_args()

    # Import MCP tools
    from security_weekly_mcp.tools import news

    # 計算日期範圍
    end_date = datetime.now()
    start_date = end_date - timedelta(days=args.days)

    # 計算週數 (ISO week)
    year, week_num, _ = end_date.isocalendar()

    print(f"=== 資安週報資料收集 ===")
    print(f"週數: {year}-W{week_num:02d}")
    print(f"期間: {start_date.strftime('%Y-%m-%d')} ~ {end_date.strftime('%Y-%m-%d')}")
    print(f"輸出目錄: {args.output_dir}")
    print()

    # 1. 收集新聞
    print("📰 收集資安新聞...")
    news_result = await news.call_tool(
        "fetch_security_news",
        {"days": args.days, "limit": 50}
    )
    news_data = json.loads(news_result[0].text) if news_result else {}

    # 統計
    news_stats = {}
    total_articles = 0
    for source, items in news_data.items():
        if isinstance(items, list):
            count = len(items)
            news_stats[source] = count
            total_articles += count

    print(f"   收集到 {total_articles} 則新聞（來自 {len(news_stats)} 個來源）")

    # 2. 收集漏洞
    print("🔒 收集漏洞資訊...")
    vuln_result = await news.call_tool(
        "fetch_vulnerabilities",
        {"min_cvss": args.min_cvss, "days": args.days, "include_kev": True, "limit": 30}
    )
    vuln_data = json.loads(vuln_result[0].text) if vuln_result else {}
    nvd_count = len(vuln_data.get("nvd", []))
    kev_count = len(vuln_data.get("kev", []))
    print(f"   NVD: {nvd_count} 個漏洞, KEV: {kev_count} 個漏洞")

    # 3. 取得建議搜尋（用於後續 WebSearch）
    print("🔍 產生建議搜尋查詢...")
    search_result = await news.call_tool(
        "suggest_searches",
        {"category": "all", "include_fetch_targets": True}
    )
    search_data = json.loads(search_result[0].text) if search_result else {}
    search_count = len(search_data.get("web_searches", []))
    print(f"   產生 {search_count} 個搜尋查詢")

    # 4. 組合完整資料
    collected_data = {
        "metadata": {
            "collected_at": datetime.now().isoformat(),
            "week": f"{year}-W{week_num:02d}",
            "period": {
                "start": start_date.strftime("%Y-%m-%d"),
                "end": end_date.strftime("%Y-%m-%d"),
                "days": args.days
            },
            "stats": {
                "total_articles": total_articles,
                "news_sources": len(news_stats),
                "nvd_vulnerabilities": nvd_count,
                "kev_vulnerabilities": kev_count,
                "suggested_searches": search_count
            }
        },
        "news": news_data,
        "vulnerabilities": vuln_data,
        "suggested_searches": search_data.get("web_searches", []),
        "fetch_targets": search_data.get("fetch_targets", [])
    }

    # 5. 保存 JSON
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    filename = f"{year}-W{week_num:02d}.json"
    output_path = output_dir / filename

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(collected_data, f, ensure_ascii=False, indent=2)

    print()
    print(f"✅ 資料已保存: {output_path}")
    print(f"   檔案大小: {output_path.stat().st_size / 1024:.1f} KB")
    print()
    print("📋 後續步驟:")
    print("   1. 使用 Claude Code 說「產生週報」")
    print("   2. Claude 會讀取此 JSON 並結合 WebSearch 產生報告")

    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
