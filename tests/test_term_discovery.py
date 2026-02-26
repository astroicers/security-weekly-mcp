"""create_pending_term 術語發現功能測試"""

import pytest
import yaml

from security_weekly_mcp.tools import glossary


@pytest.fixture
def temp_glossary(tmp_path):
    """建立臨時術語庫目錄結構"""
    # 建立目錄結構
    terms_dir = tmp_path / "terms"
    meta_dir = tmp_path / "meta"
    src_dir = tmp_path / "src"
    terms_dir.mkdir()
    meta_dir.mkdir()
    src_dir.mkdir()

    # 建立測試用分類檔案
    technologies_file = terms_dir / "technologies.yaml"
    technologies_file.write_text(
        """
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
""",
        encoding="utf-8",
    )

    # 建立 threat_actors 分類檔案（端對端測試用）
    threat_actors_file = terms_dir / "threat_actors.yaml"
    threat_actors_file.write_text(
        """
category:
  id: threat_actors
  name_zh: 威脅行為者

terms: []
""",
        encoding="utf-8",
    )

    return tmp_path


@pytest.fixture
def mock_glossary_path(temp_glossary, monkeypatch):
    """替換 GLOSSARY_PATH 為臨時目錄"""
    monkeypatch.setattr(glossary, "GLOSSARY_PATH", temp_glossary)
    glossary.reset_glossary_cache()
    return temp_glossary


class TestCreatePendingTerm:
    """create_pending_term 工具測試"""

    @pytest.mark.asyncio
    async def test_create_success(self, mock_glossary_path):
        """成功建立待審術語"""
        result = await glossary.call_tool(
            "create_pending_term",
            {
                "id": "salt_typhoon",
                "term_en": "Salt Typhoon",
                "term_zh": "鹽颱風",
                "category": "threat_actors",
                "brief_definition": "中國國家資助的網路間諜組織",
            },
        )
        assert len(result) == 1
        assert "✅" in result[0].text
        assert "salt_typhoon" in result[0].text

        # 驗證檔案已建立
        pending_dir = mock_glossary_path / "pending"
        pending_files = list(pending_dir.glob("*-salt_typhoon.yaml"))
        assert len(pending_files) == 1

        # 驗證檔案內容
        with open(pending_files[0], encoding="utf-8") as f:
            data = yaml.safe_load(f)

        assert data["term"]["id"] == "salt_typhoon"
        assert data["term"]["term_en"] == "Salt Typhoon"
        assert data["term"]["term_zh"] == "鹽颱風"
        assert data["term"]["category"] == "threat_actors"
        assert data["term"]["definitions"]["brief"] == "中國國家資助的網路間諜組織"
        assert data["discovery"]["source"] == "weekly-report"
        assert data["discovery"]["confidence"] == 0.8

    @pytest.mark.asyncio
    async def test_duplicate_in_glossary(self, mock_glossary_path):
        """術語已在術語庫 → 回傳提示"""
        result = await glossary.call_tool(
            "create_pending_term",
            {
                "id": "existing_term",
                "term_en": "Existing Term",
                "term_zh": "現有術語",
                "category": "technologies",
                "brief_definition": "測試用現有術語",
            },
        )
        assert len(result) == 1
        assert "ℹ️" in result[0].text
        assert "已存在" in result[0].text

    @pytest.mark.asyncio
    async def test_duplicate_in_pending(self, mock_glossary_path):
        """術語已在 pending → 回傳提示"""
        # 先建立一個 pending 檔案
        pending_dir = mock_glossary_path / "pending"
        pending_dir.mkdir(exist_ok=True)
        pending_file = pending_dir / "2026-02-20-test_dup.yaml"
        pending_file.write_text(
            """
term:
  id: test_dup
  term_en: Test Dup
  term_zh: 測試重複
  category: technologies
  definitions:
    brief: 重複測試
""",
            encoding="utf-8",
        )

        result = await glossary.call_tool(
            "create_pending_term",
            {
                "id": "test_dup",
                "term_en": "Test Dup",
                "term_zh": "測試重複",
                "category": "technologies",
                "brief_definition": "重複測試",
            },
        )
        assert len(result) == 1
        assert "ℹ️" in result[0].text
        assert "已在待審" in result[0].text

    @pytest.mark.asyncio
    async def test_invalid_id_format(self, mock_glossary_path):
        """無效 ID 格式"""
        result = await glossary.call_tool(
            "create_pending_term",
            {
                "id": "Salt-Typhoon",
                "term_en": "Salt Typhoon",
                "term_zh": "鹽颱風",
                "category": "threat_actors",
                "brief_definition": "中國國家資助的網路間諜組織",
            },
        )
        assert len(result) == 1
        assert "❌" in result[0].text
        assert "無效" in result[0].text

    @pytest.mark.asyncio
    async def test_invalid_category(self, mock_glossary_path):
        """無效分類"""
        result = await glossary.call_tool(
            "create_pending_term",
            {
                "id": "test_invalid_cat",
                "term_en": "Test Invalid Category",
                "term_zh": "測試無效分類",
                "category": "nonexistent_category",
                "brief_definition": "測試用",
            },
        )
        assert len(result) == 1
        assert "❌" in result[0].text
        assert "無效的分類" in result[0].text

    @pytest.mark.asyncio
    async def test_brief_too_long(self, mock_glossary_path):
        """brief_definition 過長"""
        long_brief = "這是一個非常非常非常非常非常非常非常非常非常非常非常非常非常非常非常非常非常非常非常長的術語定義超過了五十個字元的限制"
        result = await glossary.call_tool(
            "create_pending_term",
            {
                "id": "test_long_brief",
                "term_en": "Test Long Brief",
                "term_zh": "測試長定義",
                "category": "technologies",
                "brief_definition": long_brief,
            },
        )
        assert len(result) == 1
        assert "⚠️" in result[0].text
        assert "過長" in result[0].text

    @pytest.mark.asyncio
    async def test_with_optional_fields(self, mock_glossary_path):
        """帶選填欄位"""
        result = await glossary.call_tool(
            "create_pending_term",
            {
                "id": "test_optional",
                "term_en": "Test Optional",
                "term_zh": "測試選填",
                "category": "malware",
                "brief_definition": "測試選填欄位的術語",
                "standard_definition": "這是一個測試用的標準定義，用來驗證選填欄位是否正確寫入 YAML 檔案中",
                "source_url": "https://example.com/report",
                "confidence": 0.95,
            },
        )
        assert len(result) == 1
        assert "✅" in result[0].text

        # 驗證檔案內容
        pending_dir = mock_glossary_path / "pending"
        pending_files = list(pending_dir.glob("*-test_optional.yaml"))
        assert len(pending_files) == 1

        with open(pending_files[0], encoding="utf-8") as f:
            data = yaml.safe_load(f)

        assert data["term"]["definitions"]["standard"] is not None
        assert data["discovery"]["source_url"] == "https://example.com/report"
        assert data["discovery"]["confidence"] == 0.95

    @pytest.mark.asyncio
    async def test_pending_dir_auto_create(self, mock_glossary_path):
        """pending/ 不存在時自動建立"""
        # 確保 pending 目錄不存在
        pending_dir = mock_glossary_path / "pending"
        if pending_dir.exists():
            import shutil

            shutil.rmtree(pending_dir)
        assert not pending_dir.exists()

        result = await glossary.call_tool(
            "create_pending_term",
            {
                "id": "test_auto_create",
                "term_en": "Test Auto Create",
                "term_zh": "自動建立測試",
                "category": "technologies",
                "brief_definition": "測試自動建立 pending 目錄",
            },
        )
        assert len(result) == 1
        assert "✅" in result[0].text

        # 驗證目錄和檔案都已建立
        assert pending_dir.exists()
        pending_files = list(pending_dir.glob("*-test_auto_create.yaml"))
        assert len(pending_files) == 1

    @pytest.mark.asyncio
    async def test_duplicate_term_en_name(self, mock_glossary_path):
        """term_en 與現有術語名稱相同但 ID 不同 → 應被攔截"""
        result = await glossary.call_tool(
            "create_pending_term",
            {
                "id": "existing_term_v2",
                "term_en": "Existing Term",
                "term_zh": "現有術語第二版",
                "category": "technologies",
                "brief_definition": "這是重複名稱的術語",
            },
        )
        assert len(result) == 1
        assert "ℹ️" in result[0].text
        assert "類似術語已存在" in result[0].text
        assert "existing_term" in result[0].text

    @pytest.mark.asyncio
    async def test_brief_exactly_30_chars(self, mock_glossary_path):
        """brief 剛好 30 字元應通過"""
        brief_30 = "一二三四五六七八九十一二三四五六七八九十一二三四五六七八九十"
        assert len(brief_30) == 30
        result = await glossary.call_tool(
            "create_pending_term",
            {
                "id": "test_30_chars",
                "term_en": "Test 30 Chars",
                "term_zh": "測試三十字",
                "category": "technologies",
                "brief_definition": brief_30,
            },
        )
        assert len(result) == 1
        assert "✅" in result[0].text

    @pytest.mark.asyncio
    async def test_brief_31_chars_rejected(self, mock_glossary_path):
        """brief 31 字元應被拒"""
        brief_31 = "一二三四五六七八九十一二三四五六七八九十一二三四五六七八九十一"
        assert len(brief_31) == 31
        result = await glossary.call_tool(
            "create_pending_term",
            {
                "id": "test_31_chars",
                "term_en": "Test 31 Chars",
                "term_zh": "測試三十一字",
                "category": "technologies",
                "brief_definition": brief_31,
            },
        )
        assert len(result) == 1
        assert "⚠️" in result[0].text
        assert "過長" in result[0].text
        assert "≤ 30" in result[0].text

    @pytest.mark.asyncio
    async def test_approve_then_create_detects_duplicate(self, mock_glossary_path):
        """approve 後立即 create 同 ID 術語，應被偵測到（驗證 cache reset）"""
        # Step 1: create pending term
        result = await glossary.call_tool(
            "create_pending_term",
            {
                "id": "new_actor",
                "term_en": "New Actor",
                "term_zh": "新威脅者",
                "category": "threat_actors",
                "brief_definition": "測試用威脅行為者",
            },
        )
        assert "✅" in result[0].text
        filename = result[0].text.split("：")[1].strip()

        # Step 2: approve the pending term
        result = await glossary.call_tool(
            "approve_pending_term",
            {"filename": filename},
        )
        assert "✅" in result[0].text

        # Step 3: create same ID again → should be detected
        result = await glossary.call_tool(
            "create_pending_term",
            {
                "id": "new_actor",
                "term_en": "New Actor",
                "term_zh": "新威脅者",
                "category": "threat_actors",
                "brief_definition": "測試用威脅行為者",
            },
        )
        assert "ℹ️" in result[0].text
        assert "已存在" in result[0].text
