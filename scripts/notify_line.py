#!/usr/bin/env python3
"""LINE Notify 通知腳本

發送週報 LINE 通知。供 GitHub Actions 或手動執行。

用法：
    python scripts/notify_line.py --report output/reports/SEC-WEEKLY-2026-W08.json
    python scripts/notify_line.py --latest
"""

import argparse
import asyncio
import json
import sys
from pathlib import Path

# 專案根目錄
PROJECT_ROOT = Path(__file__).parent.parent

# 加入 mcp-server 套件路徑
sys.path.insert(0, str(PROJECT_ROOT / "packages" / "mcp-server" / "src"))

from security_weekly_mcp.notifications import send_line_notification  # noqa: E402


def find_latest_report(reports_dir: Path) -> Path | None:
    """找出最新的週報檔案"""
    report_files = sorted(reports_dir.glob("SEC-WEEKLY-*.json"), reverse=True)
    return report_files[0] if report_files else None


async def main() -> int:
    parser = argparse.ArgumentParser(description="發送週報 LINE Notify 通知")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--report", type=str, help="週報 JSON 檔案路徑")
    group.add_argument("--latest", action="store_true", help="使用最新的週報")
    parser.add_argument("--dry-run", action="store_true", help="只顯示訊息內容，不實際發送")
    args = parser.parse_args()

    # 決定報告檔案路徑
    if args.latest:
        reports_dir = PROJECT_ROOT / "output" / "reports"
        report_path = find_latest_report(reports_dir)
        if not report_path:
            print("錯誤：找不到任何週報檔案", file=sys.stderr)
            return 1
        print(f"使用最新週報：{report_path.name}")
    else:
        report_path = Path(args.report)

    # 讀取週報
    if not report_path.exists():
        print(f"錯誤：找不到週報檔案 {report_path}", file=sys.stderr)
        return 1

    try:
        report = json.loads(report_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"錯誤：週報 JSON 格式錯誤 - {e}", file=sys.stderr)
        return 1

    # 格式化訊息（用於 dry-run 或實際發送）
    from security_weekly_mcp.notifications.line_notify import format_weekly_summary

    message = format_weekly_summary(report)

    if args.dry_run:
        print("=== LINE Notify 訊息預覽 ===")
        print(message)
        print("=== 結束預覽 (dry-run 模式，未實際發送) ===")
        return 0

    # 發送通知
    print("正在發送 LINE Notify 通知...")
    try:
        result = await send_line_notification(report)
        print(f"發送成功！回應：{result}")
        return 0
    except Exception as e:
        print(f"錯誤：發送失敗 - {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    exit(asyncio.run(main()))
