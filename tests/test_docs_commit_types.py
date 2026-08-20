"""文件與 gate 設定的 commit 型別一致性測試

asp-gate.yaml 的 commit-format regex 是允許型別的單一事實源。
AGENTS.md「分支與提交」複述該清單供人閱讀，CONTRIBUTING.md 則只指向 AGENTS.md。
本測試防止三者再度漂移（issue #7），並看守 CONTRIBUTING 指向 AGENTS.md 的錨點（issue #11）。

刻意不 import yaml：治理測試的存活不該綁應用套件的依賴集（issue #11 F2）。
本檔只讀原始文字，用 re 抽取，根環境 `uv sync` 後即可收集執行。
"""

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parent.parent
GATE_PATH = REPO_ROOT / "asp-gate.yaml"
AGENTS_PATH = REPO_ROOT / "AGENTS.md"
CONTRIBUTING_PATH = REPO_ROOT / "CONTRIBUTING.md"


def _gate_commit_types() -> list[str]:
    """從 asp-gate.yaml 的 commit-format 檢查取出允許的型別（依序）"""
    content = GATE_PATH.read_text(encoding="utf-8")
    blocks = re.findall(
        r"^  - id: commit-format$(.*?)(?=^  - id: |\Z)",
        content,
        flags=re.MULTILINE | re.DOTALL,
    )
    assert len(blocks) == 1, "asp-gate.yaml 應有且僅有一項 commit-format 檢查"
    match = re.search(r"^\s*pattern: '\^\(([a-z]+(?:\|[a-z]+)*)\)", blocks[0], flags=re.MULTILINE)
    assert match, f"無法從 commit-format 區塊解析型別清單：{blocks[0]!r}"
    return match.group(1).split("|")


def _agents_md_commit_types() -> list[str]:
    """從 AGENTS.md 的 `型別...(scope): 摘要` code span 取出型別清單（依序）"""
    content = AGENTS_PATH.read_text(encoding="utf-8")
    spans = re.findall(r"`([a-z]+(?:\|[a-z]+)*)\(scope\)", content)
    assert len(spans) == 1, (
        f"AGENTS.md 應有且僅有一處 `型別…(scope): 摘要` 形式的 commit 型別清單，實得 {spans}"
    )
    return spans[0].split("|")


def _assert_types_consistent(gate_types: list[str], doc_types: list[str]) -> None:
    """單一事實源的比對規則：list 相等（含順序）

    刻意不用子字串比對——`"|".join(types) in content` 對「gate 端移除首/尾型別」
    靜默通過（移除後的 join 仍是原句的連續子字串），而那正是防線要擋的方向：
    gate 收窄後文件仍在廣告已被拒絕的型別（issue #11 F1）。
    """
    assert gate_types == doc_types, (
        f"commit 型別清單漂移：asp-gate.yaml={gate_types}、AGENTS.md={doc_types}；"
        f"僅在 gate={sorted(set(gate_types) - set(doc_types))}、"
        f"僅在 AGENTS.md={sorted(set(doc_types) - set(gate_types))}"
    )


def _slugify_heading(text: str) -> str:
    """GitHub 風格標題錨點：小寫、去標點、空白轉連字號（CJK 原樣保留）"""
    slug = re.sub(r"[^\w\s-]", "", text.strip().lower())
    return re.sub(r"\s+", "-", slug)


def _agents_md_heading_slugs() -> set[str]:
    content = AGENTS_PATH.read_text(encoding="utf-8")
    return {
        _slugify_heading(h)
        for h in re.findall(r"^#{1,6}\s+(.*\S)\s*$", content, flags=re.MULTILINE)
    }


class TestCommitTypesSingleSourceOfTruth:
    """commit 型別清單的單一事實源"""

    def test_agents_md_lists_all_gate_types(self):
        """AGENTS.md 的型別清單與 gate regex 完全一致（順序亦同）"""
        _assert_types_consistent(_gate_commit_types(), _agents_md_commit_types())

    @pytest.mark.parametrize("position", ["首", "中", "尾"])
    def test_type_list_comparison_catches_removal(self, position):
        """負向驗證：gate 端移除首/中/尾任一型別，比對都必須轉紅（issue #11 F1）"""
        doc_types = _agents_md_commit_types()
        assert len(doc_types) >= 3, "型別清單不足 3 項，無法驗證首/中/尾三個位置"
        index = {"首": 0, "中": len(doc_types) // 2, "尾": len(doc_types) - 1}[position]
        mutated_gate = [t for i, t in enumerate(doc_types) if i != index]
        with pytest.raises(AssertionError):
            _assert_types_consistent(mutated_gate, doc_types)

    def test_contributing_points_to_agents_md(self):
        """CONTRIBUTING.md 指向 AGENTS.md，而非自己維護第二份清單"""
        content = CONTRIBUTING_PATH.read_text(encoding="utf-8")
        assert "AGENTS.md" in content, "CONTRIBUTING.md 應指向 AGENTS.md 的型別清單"

    def test_contributing_has_no_second_type_list(self):
        """CONTRIBUTING.md 不得再出現 `type:` - 說明 形式的第二份清單"""
        content = CONTRIBUTING_PATH.read_text(encoding="utf-8")
        bullets = re.findall(r"^- `([a-z]+):`", content, flags=re.MULTILINE)
        assert not bullets, (
            f"CONTRIBUTING.md 重新出現 commit 型別清單 {bullets}，"
            "請改為指向 AGENTS.md 以維持單一事實源"
        )

    def test_contributing_anchors_into_agents_md_resolve(self):
        """CONTRIBUTING.md 指向 AGENTS.md 的錨點都對得上實際標題（issue #11 F5）

        指路連結是單一事實源的唯一入口；改了 AGENTS.md 節名會讓它靜默斷掉。
        """
        content = CONTRIBUTING_PATH.read_text(encoding="utf-8")
        anchors = re.findall(r"\]\(AGENTS\.md#([^)\s]+)\)", content)
        assert anchors, "CONTRIBUTING.md 應以錨點連結指向 AGENTS.md 的 commit 型別章節"
        slugs = _agents_md_heading_slugs()
        broken = [a for a in anchors if _slugify_heading(a) not in slugs]
        assert not broken, (
            f"CONTRIBUTING.md 的錨點 {broken} 在 AGENTS.md 找不到對應標題；"
            f"現有標題錨點：{sorted(slugs)}"
        )
