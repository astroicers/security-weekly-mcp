"""術語庫 MCP 工具"""

from pathlib import Path
from typing import Any

from mcp.types import TextContent, Tool

# 術語庫路徑
GLOSSARY_PATH = Path(__file__).parent.parent.parent.parent.parent / "glossary"

# 延遲載入 Glossary
_glossary = None


def get_glossary():
    """取得術語庫實例（延遲載入）"""
    global _glossary
    if _glossary is None:
        import sys
        # 加入 glossary 套件路徑
        glossary_src = GLOSSARY_PATH / "src"
        if str(glossary_src) not in sys.path:
            sys.path.insert(0, str(glossary_src))

        from security_glossary_tw import Glossary
        _glossary = Glossary(
            terms_dir=GLOSSARY_PATH / "terms",
            meta_dir=GLOSSARY_PATH / "meta",
        )
    return _glossary


async def list_tools() -> list[Tool]:
    """列出術語庫相關工具"""
    return [
        Tool(
            name="search_term",
            description="搜尋術語庫，支援英文或中文關鍵字模糊比對",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "搜尋關鍵字"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "最多回傳數量",
                        "default": 10
                    }
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="get_term_definition",
            description="取得術語的完整定義",
            inputSchema={
                "type": "object",
                "properties": {
                    "term_id": {
                        "type": "string",
                        "description": "術語 ID（如 apt, ransomware）"
                    }
                },
                "required": ["term_id"]
            }
        ),
        Tool(
            name="validate_terminology",
            description="驗證文本用詞是否符合台灣繁體中文規範",
            inputSchema={
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "要驗證的文本"
                    }
                },
                "required": ["text"]
            }
        ),
        Tool(
            name="add_term_links",
            description="為文本中的術語加上連結",
            inputSchema={
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "原始文本"
                    },
                    "format": {
                        "type": "string",
                        "enum": ["markdown", "html"],
                        "description": "輸出格式",
                        "default": "markdown"
                    }
                },
                "required": ["text"]
            }
        ),
        Tool(
            name="list_pending_terms",
            description="列出待審核的術語",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
    ]


async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """執行術語庫工具"""
    glossary = get_glossary()

    if name == "search_term":
        query = arguments["query"]
        limit = arguments.get("limit", 10)
        results = glossary.search(query)[:limit]

        if not results:
            return [TextContent(type="text", text=f"找不到符合「{query}」的術語")]

        lines = [f"## 搜尋結果：{query}\n"]
        for term in results:
            lines.append(f"- **{term.term_en}** ({term.term_zh})")
            lines.append(f"  - ID: `{term.id}`")
            lines.append(f"  - 定義: {term.definitions.brief}")
            lines.append(f"  - 分類: {term.category}")
            lines.append("")

        return [TextContent(type="text", text="\n".join(lines))]

    elif name == "get_term_definition":
        term_id = arguments["term_id"]
        term = glossary.get(term_id)

        if not term:
            return [TextContent(type="text", text=f"找不到術語：{term_id}")]

        lines = [
            f"# {term.term_en} ({term.term_zh})",
            "",
            f"**ID**: `{term.id}`",
            f"**分類**: {term.category}",
        ]

        if term.full_name_en:
            lines.append(f"**全稱**: {term.full_name_en}")

        lines.extend([
            "",
            "## 定義",
            "",
            f"**簡短**: {term.definitions.brief}",
        ])

        if term.definitions.standard:
            lines.append(f"\n**標準**: {term.definitions.standard}")

        if term.aliases.en or term.aliases.zh:
            lines.extend(["", "## 別名"])
            if term.aliases.en:
                lines.append(f"- 英文: {', '.join(term.aliases.en)}")
            if term.aliases.zh:
                lines.append(f"- 中文: {', '.join(term.aliases.zh)}")

        if term.related_terms:
            lines.extend(["", "## 相關術語"])
            lines.append(", ".join(f"`{t}`" for t in term.related_terms))

        return [TextContent(type="text", text="\n".join(lines))]

    elif name == "validate_terminology":
        text = arguments["text"]
        issues = glossary.validate(text)

        if not issues:
            return [TextContent(type="text", text="✅ 用詞驗證通過，無需修正")]

        lines = ["## 用詞驗證結果", "", f"發現 {len(issues)} 個問題：", ""]
        for issue in issues:
            lines.append(f"- **第 {issue.line} 行**: 「{issue.text}」")
            lines.append(f"  - 建議改為: {issue.suggestion}")

        return [TextContent(type="text", text="\n".join(lines))]

    elif name == "add_term_links":
        text = arguments["text"]
        fmt = arguments.get("format", "markdown")
        base_url = "https://astroicers.github.io/security-glossary-tw/glossary"

        result = glossary.add_links(text, format=fmt, base_url=base_url)
        return [TextContent(type="text", text=result)]

    elif name == "list_pending_terms":
        import yaml
        pending_dir = GLOSSARY_PATH / "pending"
        pending_files = list(pending_dir.glob("*.yaml"))

        if not pending_files:
            return [TextContent(type="text", text="目前沒有待審核的術語")]

        lines = ["## 待審核術語", "", f"共 {len(pending_files)} 個待審術語：", ""]

        for f in pending_files:
            with open(f, "r", encoding="utf-8") as fp:
                data = yaml.safe_load(fp)

            term = data.get("term", {})
            discovery = data.get("discovery", {})

            lines.append(f"### {term.get('term_en', '未知')}")
            lines.append(f"- 檔案: `{f.name}`")
            lines.append(f"- 中文: {term.get('term_zh', '未知')}")
            lines.append(f"- 定義: {term.get('definitions', {}).get('brief', '無')}")
            lines.append(f"- 分類: {term.get('category', '未知')}")
            if discovery.get("confidence"):
                lines.append(f"- 信心度: {discovery['confidence']:.0%}")
            lines.append("")

        return [TextContent(type="text", text="\n".join(lines))]

    return [TextContent(type="text", text=f"未知工具: {name}")]
