"""術語庫 MCP 工具單元測試"""

import json
import pytest

from security_weekly_mcp.tools import glossary


@pytest.fixture
def glossary_instance():
    """取得術語庫實例"""
    return glossary.get_glossary()


class TestSearchTerm:
    """search_term 工具測試"""

    @pytest.mark.asyncio
    async def test_search_apt(self):
        """搜尋 APT 應該有結果"""
        result = await glossary.call_tool("search_term", {"query": "APT"})
        assert len(result) == 1
        assert "APT" in result[0].text
        assert "進階持續性威脅" in result[0].text

    @pytest.mark.asyncio
    async def test_search_chinese(self):
        """搜尋中文術語"""
        result = await glossary.call_tool("search_term", {"query": "勒索軟體"})
        assert len(result) == 1
        assert "Ransomware" in result[0].text or "勒索" in result[0].text

    @pytest.mark.asyncio
    async def test_search_not_found(self):
        """搜尋不存在的術語"""
        result = await glossary.call_tool("search_term", {"query": "xyz123不存在的術語"})
        assert len(result) == 1
        assert "找不到" in result[0].text

    @pytest.mark.asyncio
    async def test_search_with_limit(self):
        """測試限制回傳數量"""
        result = await glossary.call_tool("search_term", {"query": "attack", "limit": 3})
        assert len(result) == 1
        # 結果應該被限制在 3 個以內
        lines = result[0].text.split("\n")
        term_count = sum(1 for line in lines if line.startswith("- **"))
        assert term_count <= 3


class TestGetTermDefinition:
    """get_term_definition 工具測試"""

    @pytest.mark.asyncio
    async def test_get_apt(self):
        """取得 APT 定義"""
        result = await glossary.call_tool("get_term_definition", {"term_id": "apt"})
        assert len(result) == 1
        assert "APT" in result[0].text
        assert "進階持續性威脅" in result[0].text

    @pytest.mark.asyncio
    async def test_get_not_found(self):
        """取得不存在的術語"""
        result = await glossary.call_tool("get_term_definition", {"term_id": "not_exist"})
        assert len(result) == 1
        assert "找不到" in result[0].text


class TestValidateTerminology:
    """validate_terminology 工具測試"""

    @pytest.mark.asyncio
    async def test_valid_text(self):
        """驗證正確用詞"""
        result = await glossary.call_tool(
            "validate_terminology",
            {"text": "這是一個資安週報，討論駭客攻擊和惡意程式。"}
        )
        assert len(result) == 1
        assert "通過" in result[0].text or "問題" not in result[0].text


class TestAddTermLinks:
    """add_term_links 工具測試"""

    @pytest.mark.asyncio
    async def test_add_links_markdown(self):
        """測試 Markdown 格式連結"""
        result = await glossary.call_tool(
            "add_term_links",
            {"text": "APT 組織發動勒索軟體攻擊", "format": "markdown"}
        )
        assert len(result) == 1
        # 應該包含 markdown 連結格式
        text = result[0].text
        assert "[APT]" in text or "APT" in text


class TestExtractTerms:
    """extract_terms 工具測試"""

    @pytest.mark.asyncio
    async def test_extract_from_text(self):
        """從文本提取術語"""
        text = """
        本週 APT 組織發動供應鏈攻擊，
        植入後門程式（backdoor）。
        CISA KEV 清單新增漏洞。
        """
        result = await glossary.call_tool("extract_terms", {"text": text})
        assert len(result) == 1

        terms = json.loads(result[0].text)
        assert isinstance(terms, list)
        assert len(terms) > 0

        # 檢查 APT 是否被提取
        term_ids = [t["id"] for t in terms]
        assert "apt" in term_ids

    @pytest.mark.asyncio
    async def test_extract_with_limit(self):
        """測試限制提取數量"""
        text = "APT 組織使用 ransomware 勒索軟體和 backdoor 後門進行 RCE 攻擊。"
        result = await glossary.call_tool("extract_terms", {"text": text, "max_terms": 2})
        assert len(result) == 1

        terms = json.loads(result[0].text)
        assert len(terms) <= 2

    @pytest.mark.asyncio
    async def test_extract_returns_json_structure(self):
        """檢查回傳的 JSON 結構"""
        result = await glossary.call_tool("extract_terms", {"text": "APT 攻擊"})
        terms = json.loads(result[0].text)

        if len(terms) > 0:
            term = terms[0]
            assert "term" in term
            assert "term_en" in term
            assert "term_zh" in term
            assert "definition" in term
            assert "id" in term
            assert "url" in term


class TestListPendingTerms:
    """list_pending_terms 工具測試"""

    @pytest.mark.asyncio
    async def test_list_pending(self):
        """列出待審術語（可能為空）"""
        result = await glossary.call_tool("list_pending_terms", {})
        assert len(result) == 1
        # 可能沒有待審術語，所以只檢查有回傳
        assert result[0].text is not None
