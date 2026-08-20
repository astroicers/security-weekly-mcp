"""文件與 gate 設定的 commit 型別一致性測試

asp-gate.yaml 的 commit-format regex 是允許型別的單一事實源。
AGENTS.md「分支與提交」複述該清單供人閱讀，CONTRIBUTING.md 則只指向 AGENTS.md。
本測試防止三者再度漂移（issue #7）。
"""

import re
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).parent.parent
GATE_PATH = REPO_ROOT / "asp-gate.yaml"
AGENTS_PATH = REPO_ROOT / "AGENTS.md"
CONTRIBUTING_PATH = REPO_ROOT / "CONTRIBUTING.md"


def _gate_commit_types() -> list[str]:
    """從 asp-gate.yaml 的 commit-format 檢查取出允許的型別"""
    config = yaml.safe_load(GATE_PATH.read_text(encoding="utf-8"))
    checks = [c for c in config["checks"] if c["id"] == "commit-format"]
    assert len(checks) == 1, "asp-gate.yaml 應有且僅有一項 commit-format 檢查"
    pattern = checks[0]["args"]["pattern"]
    match = re.search(r"\^\(([a-z|]+)\)", pattern)
    assert match, f"無法從 commit-format pattern 解析型別清單：{pattern}"
    return match.group(1).split("|")


class TestCommitTypesSingleSourceOfTruth:
    """commit 型別清單的單一事實源"""

    def test_agents_md_lists_all_gate_types(self):
        """AGENTS.md 的型別清單與 gate regex 完全一致（順序亦同）"""
        types = _gate_commit_types()
        content = AGENTS_PATH.read_text(encoding="utf-8")
        assert "|".join(types) in content, (
            f"AGENTS.md 未包含 gate 的型別清單 {'|'.join(types)}，兩者已漂移"
        )

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
