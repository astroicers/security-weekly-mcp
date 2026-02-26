"""術語庫 MCP 工具"""

from pathlib import Path
from typing import Any

from mcp.types import TextContent, Tool

# 術語庫路徑
GLOSSARY_PATH = Path(__file__).parent.parent.parent.parent.parent / "glossary"

# 延遲載入 Glossary（單例快取）
_glossary = None
_glossary_initialized = False


def get_glossary():
    """取得術語庫實例（單例快取，提升效能）"""
    global _glossary, _glossary_initialized
    if not _glossary_initialized:
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
        _glossary_initialized = True
    return _glossary


def reset_glossary_cache():
    """重設術語庫快取（用於測試）"""
    global _glossary, _glossary_initialized
    _glossary = None
    _glossary_initialized = False


async def list_tools() -> list[Tool]:
    """列出術語庫相關工具"""
    return [
        Tool(
            name="search_term",
            description="搜尋術語庫，支援英文或中文關鍵字模糊比對",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "搜尋關鍵字"},
                    "limit": {"type": "integer", "description": "最多回傳數量", "default": 10},
                },
                "required": ["query"],
            },
        ),
        Tool(
            name="get_term_definition",
            description="取得術語的完整定義",
            inputSchema={
                "type": "object",
                "properties": {
                    "term_id": {"type": "string", "description": "術語 ID（如 apt, ransomware）"}
                },
                "required": ["term_id"],
            },
        ),
        Tool(
            name="validate_terminology",
            description="驗證文本用詞是否符合台灣繁體中文規範",
            inputSchema={
                "type": "object",
                "properties": {"text": {"type": "string", "description": "要驗證的文本"}},
                "required": ["text"],
            },
        ),
        Tool(
            name="add_term_links",
            description="為文本中的術語加上連結",
            inputSchema={
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "原始文本"},
                    "format": {
                        "type": "string",
                        "enum": ["markdown", "html"],
                        "description": "輸出格式",
                        "default": "markdown",
                    },
                },
                "required": ["text"],
            },
        ),
        Tool(
            name="list_pending_terms",
            description="列出待審核的術語",
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="approve_pending_term",
            description="批准待審術語，將其移至正式術語庫",
            inputSchema={
                "type": "object",
                "properties": {
                    "filename": {
                        "type": "string",
                        "description": "待審術語檔案名稱（如 2026-02-10-salt_typhoon.yaml）",
                    },
                    "edits": {
                        "type": "object",
                        "description": "可選：修改術語欄位（如 term_zh, definitions.brief）",
                        "default": {},
                    },
                },
                "required": ["filename"],
            },
        ),
        Tool(
            name="reject_pending_term",
            description="拒絕待審術語，刪除檔案",
            inputSchema={
                "type": "object",
                "properties": {
                    "filename": {"type": "string", "description": "待審術語檔案名稱"},
                    "reason": {
                        "type": "string",
                        "description": "拒絕原因（記錄用）",
                        "default": "",
                    },
                },
                "required": ["filename"],
            },
        ),
        Tool(
            name="extract_terms",
            description="從文本中自動提取術語庫中的術語，回傳術語列表（含定義）。用於週報產生時自動填充「本期術語」區塊。",
            inputSchema={
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "要分析的文本（可以是週報內容）"},
                    "max_terms": {
                        "type": "integer",
                        "description": "最多回傳的術語數量",
                        "default": 10,
                    },
                },
                "required": ["text"],
            },
        ),
        Tool(
            name="create_pending_term",
            description="建立待審術語。將不在術語庫中的新術語提交待審，自動檢查重複。",
            inputSchema={
                "type": "object",
                "properties": {
                    "id": {
                        "type": "string",
                        "description": "術語 ID（小寫底線分隔，如 salt_typhoon）",
                    },
                    "term_en": {"type": "string", "description": "英文術語"},
                    "term_zh": {"type": "string", "description": "繁體中文術語"},
                    "category": {
                        "type": "string",
                        "enum": [
                            "attack_types",
                            "vulnerabilities",
                            "threat_actors",
                            "malware",
                            "technologies",
                            "frameworks",
                            "compliance",
                        ],
                        "description": "術語分類",
                    },
                    "brief_definition": {
                        "type": "string",
                        "description": "≤30 字簡短定義（台灣繁體中文）",
                    },
                    "standard_definition": {
                        "type": "string",
                        "description": "50-100 字標準定義（選填）",
                    },
                    "source_url": {"type": "string", "description": "來源 URL（選填）"},
                    "confidence": {
                        "type": "number",
                        "description": "信心度 0-1",
                        "default": 0.8,
                    },
                },
                "required": ["id", "term_en", "term_zh", "category", "brief_definition"],
            },
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

        lines.extend(
            [
                "",
                "## 定義",
                "",
                f"**簡短**: {term.definitions.brief}",
            ]
        )

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
            with open(f, encoding="utf-8") as fp:
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

    elif name == "extract_terms":
        import json

        text = arguments["text"]
        max_terms = arguments.get("max_terms", 10)

        # 從文本中找出所有術語
        matches = glossary.find_terms(text)

        # 去重並保留順序
        seen_ids = set()
        unique_terms = []
        for match in matches:
            if match.term_id not in seen_ids:
                seen_ids.add(match.term_id)
                term = glossary.get(match.term_id)
                if term:
                    unique_terms.append(
                        {
                            "term": term.term_zh or term.term_en,
                            "term_en": term.term_en,
                            "term_zh": term.term_zh,
                            "definition": term.definitions.brief,
                            "id": term.id,
                            "url": f"https://astroicers.github.io/security-glossary-tw/glossary/{term.id}",
                        }
                    )
                if len(unique_terms) >= max_terms:
                    break

        return [
            TextContent(type="text", text=json.dumps(unique_terms, ensure_ascii=False, indent=2))
        ]

    elif name == "approve_pending_term":
        from datetime import datetime

        import yaml

        filename = arguments["filename"]
        edits = arguments.get("edits", {})

        pending_dir = GLOSSARY_PATH / "pending"
        pending_file = pending_dir / filename

        if not pending_file.exists():
            return [TextContent(type="text", text=f"❌ 找不到待審檔案：{filename}")]

        # 讀取待審術語
        with open(pending_file, encoding="utf-8") as fp:
            data = yaml.safe_load(fp)

        term_data = data.get("term", {})
        category = term_data.get("category", "technologies")

        # 套用編輯
        if edits:
            for key, value in edits.items():
                if "." in key:
                    # 支援 nested key 如 "definitions.brief"
                    parts = key.split(".")
                    target = term_data
                    for part in parts[:-1]:
                        target = target.setdefault(part, {})
                    target[parts[-1]] = value
                else:
                    term_data[key] = value

        # 驗證必要欄位
        required_fields = ["id", "term_en", "category", "definitions"]
        missing = [f for f in required_fields if f not in term_data]
        if missing:
            return [TextContent(type="text", text=f"❌ 缺少必要欄位：{', '.join(missing)}")]

        # 驗證分類是否有效
        valid_categories = [
            "attack_types",
            "vulnerabilities",
            "threat_actors",
            "malware",
            "technologies",
            "frameworks",
            "compliance",
        ]
        if category not in valid_categories:
            return [
                TextContent(
                    type="text",
                    text=f"❌ 無效的分類：{category}\n有效分類：{', '.join(valid_categories)}",
                )
            ]

        # 驗證 definitions.brief 存在且長度合理
        definitions = term_data.get("definitions", {})
        brief = definitions.get("brief", "")
        if not brief:
            return [TextContent(type="text", text="❌ definitions.brief 不能為空")]
        if len(brief) > 30:
            return [
                TextContent(
                    type="text",
                    text=f"⚠️ definitions.brief 過長（{len(brief)} 字元），建議 ≤ 30 字元",
                )
            ]

        # 更新 metadata
        if "metadata" not in term_data:
            term_data["metadata"] = {}
        term_data["metadata"]["status"] = "approved"
        term_data["metadata"]["approved_at"] = datetime.now().isoformat()

        # 讀取目標分類檔案
        terms_file = GLOSSARY_PATH / "terms" / f"{category}.yaml"
        if not terms_file.exists():
            return [TextContent(type="text", text=f"❌ 找不到分類檔案：{category}.yaml")]

        with open(terms_file, encoding="utf-8") as fp:
            terms_data = yaml.safe_load(fp)

        # 檢查是否已存在
        existing_ids = [t.get("id") for t in terms_data.get("terms", [])]
        if term_data.get("id") in existing_ids:
            return [TextContent(type="text", text=f"❌ 術語 ID 已存在：{term_data.get('id')}")]

        # 新增術語
        terms_data["terms"].append(term_data)

        # 寫回檔案
        with open(terms_file, "w", encoding="utf-8") as fp:
            yaml.dump(terms_data, fp, allow_unicode=True, default_flow_style=False, sort_keys=False)

        # 刪除待審檔案
        pending_file.unlink()

        # 重設快取，確保後續 create_pending_term 能偵測剛入庫的術語
        reset_glossary_cache()

        return [
            TextContent(
                type="text",
                text=f"✅ 術語已批准並新增至 {category}.yaml\n\n"
                f"- ID: `{term_data.get('id')}`\n"
                f"- 名稱: {term_data.get('term_en')} ({term_data.get('term_zh', '')})\n"
                f"- 分類: {category}",
            )
        ]

    elif name == "reject_pending_term":
        filename = arguments["filename"]
        reason = arguments.get("reason", "")

        pending_dir = GLOSSARY_PATH / "pending"
        pending_file = pending_dir / filename

        if not pending_file.exists():
            return [TextContent(type="text", text=f"❌ 找不到待審檔案：{filename}")]

        # 刪除檔案
        pending_file.unlink()

        result = f"✅ 已拒絕並刪除：{filename}"
        if reason:
            result += f"\n原因：{reason}"

        return [TextContent(type="text", text=result)]

    elif name == "create_pending_term":
        import re
        from datetime import date

        import yaml

        term_id = arguments["id"]
        term_en = arguments["term_en"]
        term_zh = arguments["term_zh"]
        category = arguments["category"]
        brief_definition = arguments["brief_definition"]
        standard_definition = arguments.get("standard_definition")
        source_url = arguments.get("source_url")
        confidence = arguments.get("confidence", 0.8)

        # 驗證 ID 格式
        if not re.match(r"^[a-z][a-z0-9_]*$", term_id):
            return [
                TextContent(
                    type="text",
                    text=f"❌ 無效的術語 ID：{term_id}\n格式：小寫字母開頭，僅含小寫字母、數字、底線",
                )
            ]

        # 驗證分類
        valid_categories = [
            "attack_types",
            "vulnerabilities",
            "threat_actors",
            "malware",
            "technologies",
            "frameworks",
            "compliance",
        ]
        if category not in valid_categories:
            return [
                TextContent(
                    type="text",
                    text=f"❌ 無效的分類：{category}\n有效分類：{', '.join(valid_categories)}",
                )
            ]

        # 驗證 brief_definition 長度
        if len(brief_definition) > 30:
            return [
                TextContent(
                    type="text",
                    text=f"⚠️ brief_definition 過長（{len(brief_definition)} 字元），請縮減至 ≤ 30 字元",
                )
            ]

        # 檢查術語庫是否已有此 ID
        if glossary.get(term_id):
            return [
                TextContent(type="text", text=f"ℹ️ 術語已存在於術語庫中：{term_id}")
            ]

        # 檢查術語庫是否已有相同 term_en 名稱
        existing = glossary.get_by_name(term_en)
        if existing:
            return [
                TextContent(
                    type="text",
                    text=f"ℹ️ 類似術語已存在：{existing.id}（{existing.term_en}）",
                )
            ]

        # 檢查 pending 是否已有此 ID
        pending_dir = GLOSSARY_PATH / "pending"
        pending_dir.mkdir(parents=True, exist_ok=True)
        existing_pending = list(pending_dir.glob(f"*-{term_id}.yaml"))
        if existing_pending:
            return [
                TextContent(
                    type="text",
                    text=f"ℹ️ 術語已在待審中：{existing_pending[0].name}",
                )
            ]

        # 組裝 YAML 資料
        today = date.today().isoformat()
        filename = f"{today}-{term_id}.yaml"

        data = {
            "term": {
                "id": term_id,
                "term_en": term_en,
                "term_zh": term_zh,
                "category": category,
                "definitions": {"brief": brief_definition},
            },
            "discovery": {
                "source": "weekly-report",
                "discovered_at": today,
                "confidence": confidence,
            },
        }

        if standard_definition:
            data["term"]["definitions"]["standard"] = standard_definition
        if source_url:
            data["discovery"]["source_url"] = source_url

        # 寫入檔案
        pending_file = pending_dir / filename
        with open(pending_file, "w", encoding="utf-8") as fp:
            yaml.dump(data, fp, allow_unicode=True, default_flow_style=False, sort_keys=False)

        return [
            TextContent(type="text", text=f"✅ 已建立待審術語：{filename}")
        ]

    return [TextContent(type="text", text=f"未知工具: {name}")]
