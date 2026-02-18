"""LINE Notify 整合模組

用於發送週報通知到 LINE Notify 服務。
"""

import os
from typing import Any

import httpx

LINE_NOTIFY_API = "https://notify-api.line.me/api/notify"


class LineNotifyError(Exception):
    """LINE Notify 錯誤"""

    pass


class LineNotify:
    """LINE Notify 客戶端"""

    def __init__(self, token: str | None = None):
        """初始化 LINE Notify 客戶端

        Args:
            token: LINE Notify Access Token。若未提供，從環境變數 LINE_NOTIFY_TOKEN 讀取。
        """
        self.token = token or os.environ.get("LINE_NOTIFY_TOKEN")
        if not self.token:
            raise LineNotifyError(
                "LINE Notify token 未設定。請設定 LINE_NOTIFY_TOKEN 環境變數或傳入 token 參數。"
            )

    async def send(self, message: str) -> dict[str, Any]:
        """發送通知訊息

        Args:
            message: 要發送的訊息內容（最多 1000 字元）

        Returns:
            LINE Notify API 回應

        Raises:
            LineNotifyError: 發送失敗時拋出
        """
        if len(message) > 1000:
            message = message[:997] + "..."

        headers = {"Authorization": f"Bearer {self.token}"}
        data = {"message": message}

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(LINE_NOTIFY_API, headers=headers, data=data)

                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 401:
                    raise LineNotifyError("LINE Notify token 無效或已過期")
                elif response.status_code == 400:
                    raise LineNotifyError(f"請求格式錯誤: {response.text}")
                else:
                    raise LineNotifyError(
                        f"LINE Notify API 錯誤 ({response.status_code}): {response.text}"
                    )

        except httpx.TimeoutException:
            raise LineNotifyError("LINE Notify API 連線逾時 (30s)")
        except httpx.RequestError as e:
            raise LineNotifyError(f"網路請求失敗: {type(e).__name__}")


def format_weekly_summary(report: dict) -> str:
    """將週報資料格式化為 LINE 通知訊息

    Args:
        report: 週報 JSON 資料

    Returns:
        格式化後的訊息字串
    """
    title = report.get("title", "資安週報")
    report_id = report.get("report_id", "")
    summary = report.get("summary", {})
    _ = report.get("period", {})  # Reserved for future use

    # 威脅等級對照
    threat_level_map = {
        "normal": "一般",
        "elevated": "升高",
        "high": "高",
        "critical": "嚴重",
    }
    threat_level = threat_level_map.get(summary.get("threat_level", "normal"), "一般")

    total_events = summary.get("total_events", 0)
    total_vulns = summary.get("total_vulnerabilities", 0)

    # 組合訊息
    lines = [
        f"\n{title}",
        "",
        "本週摘要：",
        f"• {total_events} 起資安事件",
        f"• {total_vulns} 個高風險漏洞",
        f"• 威脅等級：{threat_level}",
        "",
    ]

    # 加入報告連結
    if report_id:
        report_url = (
            f"https://astroicers.github.io/security-glossary-tw/weekly/reports/{report_id}.html"
        )
        lines.append(f"閱讀完整報告：\n{report_url}")

    return "\n".join(lines)


async def send_line_notification(report: dict, token: str | None = None) -> dict:
    """發送週報 LINE 通知的便捷函數

    Args:
        report: 週報 JSON 資料
        token: LINE Notify Access Token（可選）

    Returns:
        LINE Notify API 回應
    """
    client = LineNotify(token=token)
    message = format_weekly_summary(report)
    return await client.send(message)
