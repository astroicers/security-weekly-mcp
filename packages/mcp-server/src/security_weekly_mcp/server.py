"""MCP Server 主程式

Security Weekly TW - 資安週報與術語庫 MCP Server
提供術語庫查詢、新聞收集、PDF 週報產生等功能
"""

from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

from .tools import glossary, news, report

app = Server("security-weekly-tw")

# 工具模組列表
TOOL_MODULES = [glossary, news, report]


@app.list_tools()
async def list_tools() -> list[Tool]:
    """列出所有可用工具"""
    tools = []
    for module in TOOL_MODULES:
        module_tools = await module.list_tools()
        tools.extend(module_tools)
    return tools


@app.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """呼叫指定工具"""
    # 根據工具名稱找到對應模組
    for module in TOOL_MODULES:
        module_tools = await module.list_tools()
        tool_names = [t.name for t in module_tools]
        if name in tool_names:
            return await module.call_tool(name, arguments)

    return [TextContent(type="text", text=f"未知工具：{name}")]


async def main():
    """啟動 MCP Server"""
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
