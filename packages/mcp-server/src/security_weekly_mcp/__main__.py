"""MCP Server 入口點"""

import asyncio
from .server import main

if __name__ == "__main__":
    asyncio.run(main())
