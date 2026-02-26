"""術語批准/拒絕功能測試"""

import json
import pytest
import tempfile
import shutil
from pathlib import Path

from security_weekly_mcp.tools import glossary


@pytest.fixture
def temp_glossary(tmp_path):
    """建立臨時術語庫目錄結構"""
    # 建立目錄結構
    pending_dir = tmp_path / "pending"
    terms_dir = tmp_path / "terms"
    meta_dir = tmp_path / "meta"
    pending_dir.mkdir()
    terms_dir.mkdir()
    meta_dir.mkdir()

    # 建立測試用分類檔案
    technologies_file = terms_dir / "technologies.yaml"
    technologies_file.write_text("""
category:
  id: technologies
  name_zh: 技術名詞

terms:
  - id: existing_term
    term_en: Existing Term
    term_zh: 現有術語
    category: technologies
    definitions:
      brief: 測試用現有術語
""", encoding="utf-8")

    # 建立測試用待審術語
    pending_file = pending_dir / "2026-02-14-test_term.yaml"
    pending_file.write_text("""
term:
  id: test_new_term
  term_en: Test New Term
  term_zh: 測試新術語
  category: technologies
  definitions:
    brief: 這是一個測試術語定義
    standard: 標準定義內容
discovery:
  source: test
  confidence: 0.95
""", encoding="utf-8")

    return tmp_path


@pytest.fixture
def mock_glossary_path(temp_glossary, monkeypatch):
    """替換 GLOSSARY_PATH 為臨時目錄"""
    monkeypatch.setattr(glossary, "GLOSSARY_PATH", temp_glossary)
    glossary.reset_glossary_cache()
    return temp_glossary


class TestApprovePendingTerm:
    """approve_pending_term 工具測試"""

    @pytest.mark.asyncio
    async def test_approve_success(self, mock_glossary_path):
        """成功批准術語"""
        result = await glossary.call_tool(
            "approve_pending_term",
            {"filename": "2026-02-14-test_term.yaml"}
        )
        assert len(result) == 1
        assert "✅" in result[0].text
        assert "test_new_term" in result[0].text

        # 驗證術語已加入分類檔案
        import yaml
        terms_file = mock_glossary_path / "terms" / "technologies.yaml"
        with open(terms_file, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        term_ids = [t["id"] for t in data["terms"]]
        assert "test_new_term" in term_ids

        # 驗證待審檔案已刪除
        pending_file = mock_glossary_path / "pending" / "2026-02-14-test_term.yaml"
        assert not pending_file.exists()

    @pytest.mark.asyncio
    async def test_approve_not_found(self, mock_glossary_path):
        """批准不存在的檔案"""
        result = await glossary.call_tool(
            "approve_pending_term",
            {"filename": "nonexistent.yaml"}
        )
        assert len(result) == 1
        assert "❌" in result[0].text
        assert "找不到" in result[0].text

    @pytest.mark.asyncio
    async def test_approve_with_edits(self, mock_glossary_path):
        """批准時修改欄位"""
        result = await glossary.call_tool(
            "approve_pending_term",
            {
                "filename": "2026-02-14-test_term.yaml",
                "edits": {
                    "term_zh": "修改後的術語名稱",
                    "definitions.brief": "修改後的定義"
                }
            }
        )
        assert len(result) == 1
        assert "✅" in result[0].text

        # 驗證修改已套用
        import yaml
        terms_file = mock_glossary_path / "terms" / "technologies.yaml"
        with open(terms_file, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        new_term = next(t for t in data["terms"] if t["id"] == "test_new_term")
        assert new_term["term_zh"] == "修改後的術語名稱"
        assert new_term["definitions"]["brief"] == "修改後的定義"

    @pytest.mark.asyncio
    async def test_approve_duplicate_id(self, mock_glossary_path):
        """批准重複 ID 的術語"""
        # 建立一個 ID 已存在的待審術語
        pending_file = mock_glossary_path / "pending" / "2026-02-14-duplicate.yaml"
        pending_file.write_text("""
term:
  id: existing_term
  term_en: Duplicate Term
  term_zh: 重複術語
  category: technologies
  definitions:
    brief: 這個 ID 已經存在
""", encoding="utf-8")

        result = await glossary.call_tool(
            "approve_pending_term",
            {"filename": "2026-02-14-duplicate.yaml"}
        )
        assert len(result) == 1
        assert "❌" in result[0].text
        assert "已存在" in result[0].text

    @pytest.mark.asyncio
    async def test_approve_missing_required_fields(self, mock_glossary_path):
        """批准缺少必要欄位的術語"""
        pending_file = mock_glossary_path / "pending" / "2026-02-14-incomplete.yaml"
        pending_file.write_text("""
term:
  term_en: Incomplete Term
  term_zh: 不完整術語
""", encoding="utf-8")

        result = await glossary.call_tool(
            "approve_pending_term",
            {"filename": "2026-02-14-incomplete.yaml"}
        )
        assert len(result) == 1
        assert "❌" in result[0].text
        assert "缺少必要欄位" in result[0].text

    @pytest.mark.asyncio
    async def test_approve_invalid_category(self, mock_glossary_path):
        """批准無效分類的術語"""
        pending_file = mock_glossary_path / "pending" / "2026-02-14-invalid_cat.yaml"
        pending_file.write_text("""
term:
  id: invalid_category_term
  term_en: Invalid Category Term
  term_zh: 無效分類術語
  category: nonexistent_category
  definitions:
    brief: 這個分類不存在
""", encoding="utf-8")

        result = await glossary.call_tool(
            "approve_pending_term",
            {"filename": "2026-02-14-invalid_cat.yaml"}
        )
        assert len(result) == 1
        assert "❌" in result[0].text
        assert "無效的分類" in result[0].text

    @pytest.mark.asyncio
    async def test_approve_brief_over_30(self, mock_glossary_path):
        """brief 超過 30 字元應被拒"""
        pending_file = mock_glossary_path / "pending" / "2026-02-14-long_brief.yaml"
        # 31 個中文字元
        brief_31 = "一二三四五六七八九十一二三四五六七八九十一二三四五六七八九十一"
        assert len(brief_31) == 31
        pending_file.write_text(
            f"""
term:
  id: long_brief_term
  term_en: Long Brief Term
  term_zh: 長定義術語
  category: technologies
  definitions:
    brief: {brief_31}
""",
            encoding="utf-8",
        )

        result = await glossary.call_tool(
            "approve_pending_term", {"filename": "2026-02-14-long_brief.yaml"}
        )
        assert len(result) == 1
        assert "⚠️" in result[0].text
        assert "過長" in result[0].text
        assert "≤ 30" in result[0].text

    @pytest.mark.asyncio
    async def test_approve_empty_brief(self, mock_glossary_path):
        """批准空 brief 的術語"""
        pending_file = mock_glossary_path / "pending" / "2026-02-14-no_brief.yaml"
        pending_file.write_text("""
term:
  id: no_brief_term
  term_en: No Brief Term
  term_zh: 無簡述術語
  category: technologies
  definitions:
    standard: 只有標準定義
""", encoding="utf-8")

        result = await glossary.call_tool(
            "approve_pending_term",
            {"filename": "2026-02-14-no_brief.yaml"}
        )
        assert len(result) == 1
        assert "❌" in result[0].text
        assert "brief" in result[0].text


class TestRejectPendingTerm:
    """reject_pending_term 工具測試"""

    @pytest.mark.asyncio
    async def test_reject_success(self, mock_glossary_path):
        """成功拒絕術語"""
        result = await glossary.call_tool(
            "reject_pending_term",
            {"filename": "2026-02-14-test_term.yaml", "reason": "不符合命名規範"}
        )
        assert len(result) == 1
        assert "✅" in result[0].text
        assert "拒絕" in result[0].text
        assert "不符合命名規範" in result[0].text

        # 驗證檔案已刪除
        pending_file = mock_glossary_path / "pending" / "2026-02-14-test_term.yaml"
        assert not pending_file.exists()

    @pytest.mark.asyncio
    async def test_reject_not_found(self, mock_glossary_path):
        """拒絕不存在的檔案"""
        result = await glossary.call_tool(
            "reject_pending_term",
            {"filename": "nonexistent.yaml"}
        )
        assert len(result) == 1
        assert "❌" in result[0].text
        assert "找不到" in result[0].text

    @pytest.mark.asyncio
    async def test_reject_without_reason(self, mock_glossary_path):
        """不提供原因的拒絕"""
        result = await glossary.call_tool(
            "reject_pending_term",
            {"filename": "2026-02-14-test_term.yaml"}
        )
        assert len(result) == 1
        assert "✅" in result[0].text

        # 驗證檔案已刪除
        pending_file = mock_glossary_path / "pending" / "2026-02-14-test_term.yaml"
        assert not pending_file.exists()


class TestApprovalValidation:
    """批准驗證邏輯測試"""

    @pytest.mark.asyncio
    async def test_metadata_added_on_approval(self, mock_glossary_path):
        """批准時應添加 metadata"""
        result = await glossary.call_tool(
            "approve_pending_term",
            {"filename": "2026-02-14-test_term.yaml"}
        )
        assert "✅" in result[0].text

        import yaml
        terms_file = mock_glossary_path / "terms" / "technologies.yaml"
        with open(terms_file, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        new_term = next(t for t in data["terms"] if t["id"] == "test_new_term")
        assert "metadata" in new_term
        assert new_term["metadata"]["status"] == "approved"
        assert "approved_at" in new_term["metadata"]
