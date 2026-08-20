# test: test_docs_commit_types 防線補洞——list 相等取代子字串、去 pyyaml 依賴、錨點看守

Closes #11

## 背景

PR #10(issue #7)引入的 `tests/test_docs_commit_types.py` 是 commit 型別漂移防線,
但對抗式複審找到三個洞(皆不擋 merge、後補):

- **F1(🟡)子字串斷言對 gate 端首/尾型別移除靜默漏過**
  舊斷言為 `"|".join(types) in content`。實測自 gate regex 移除 `ci`(尾)、`feat`(首)、
  `report|ci`(尾 2)皆**靜默通過**——移除後的 join 仍是 AGENTS.md 該行的連續子字串。
  漏過方向恰是防線目的:gate 收窄後,文件仍在廣告已被拒絕的型別。
- **F2(🟡)pyyaml 非根環境宣告依賴**
  根 pyproject 的 dev group 無 pyyaml;CI 綠是靠 `uv run --package security-weekly-mcp-server pytest`
  借到 mcp-server 的 runtime 依賴。治理測試的存活不該綁應用套件的依賴集。
- **F5(🔵)錨點無看守**
  CONTRIBUTING.md 指向 `AGENTS.md#分支與提交`,但無測試斷言該標題存在——改節名會讓
  指路連結靜默斷掉,而那是單一事實源的唯一入口。

## 變更

只動 `tests/test_docs_commit_types.py` 一支檔案。AGENTS.md、CONTRIBUTING.md、asp-gate.yaml
均未改——三者原本就一致,本次補的是防線本身的靈敏度。

**F1 → list 相等取代子字串**
新增 `_agents_md_commit_types()`,以 regex 從 AGENTS.md 的 `` `型別…(scope): 摘要` `` code span
也抽出清單(並斷言全檔僅一處,避免抽到別處而失去看守意義),再由
`_assert_types_consistent()` 做 **list 相等**比對(含順序)。失敗訊息列出兩邊差集,直接指出
漂移方向。

**F2 → 移除 pyyaml 依賴**
`_gate_commit_types()` 改以 re 掃 raw 文字:先切出 `  - id: commit-format` 到下一個
`  - id: ` 之間的區塊(仍保留「有且僅有一項」斷言),再從區塊內抽 `pattern:`。
本檔不再 `import yaml`,根環境 `uv sync` 後即可收集執行,無需改動任何 pyproject。
採 issue 提供的兩個選項中的後者——治理測試自帶零依賴比新增 dev 依賴更穩,
不會因日後應用依賴集調整再度失聯。

**F5 → 錨點看守**
新增 `test_contributing_anchors_into_agents_md_resolve`:抽出 CONTRIBUTING.md 中所有
`](AGENTS.md#…)` 錨點,以 GitHub 風格 slug 規則(小寫、去標點、空白轉連字號、CJK 原樣保留)
比對 AGENTS.md 實際標題。寫成**通用的連結完整性檢查**而非只硬編一個節名,
日後新增指路連結自動納入看守。

**負向驗證入庫**
新增 `test_type_list_comparison_catches_removal`(parametrize 首/中/尾三位置):
以 `pytest.raises(AssertionError)` 驗證 `_assert_types_consistent` 對三個位置的移除都會轉紅。
負向驗證因此成為 CI 的常駐斷言,而非一次性的人工實測——若日後有人把比對改回子字串語意,
這條會先轉紅。

## AC 逐條對照

- [x] **Given gate regex 移除首/尾任一型別,When 跑測試,Then
  `test_agents_md_lists_all_gate_types` 轉紅(負向驗證含首、中、尾三位置)**
  — 實測直接改 `asp-gate.yaml` 的 pattern 後跑測試(改完即還原):

  | 移除 | 剩餘 gate 清單 | 結果 |
  | --- | --- | --- |
  | `feat`(首) | `fix\|docs\|refactor\|test\|chore\|report\|ci` | 1 failed, 6 passed |
  | `test`(中) | `feat\|fix\|docs\|refactor\|chore\|report\|ci` | 1 failed, 6 passed |
  | `ci`(尾) | `feat\|fix\|docs\|refactor\|test\|chore\|report` | 1 failed, 6 passed |
  | `report\|ci`(尾 2) | `feat\|fix\|docs\|refactor\|test\|chore` | 1 failed, 6 passed |

  四種在舊版皆靜默通過。反方向(文件端漂移:從 AGENTS.md 移除 `report`)亦轉紅。
  三位置的負向驗證另以 parametrize 測試常駐在 suite 內。

- [x] **Given 根環境 `uv sync` + `uv run pytest tests/test_docs_commit_types.py`,
  Then 可收集執行(無 ImportError)**
  — 本檔已無 `import yaml`(僅 `re`、`pathlib`、`pytest`,全為根 dev group 已有或標準庫)。
  容器內無 `uv`,改以等效驗證:注入 sitecustomize 於 `sys.meta_path` 攔截 `yaml` 匯入
  (模擬根環境未安裝 pyyaml),跑本檔仍 **7 passed**。`tests/conftest.py` 只用 pytest,
  不影響收集。

- [x] **Given AGENTS.md「分支與提交」節名變更,Then 有測試轉紅**
  — 實測把 `## 分支與提交` 改為 `## 分支與 Commit` 後跑測試:1 failed, 6 passed
  (`test_contributing_anchors_into_agents_md_resolve` 轉紅,訊息列出斷掉的錨點與現有標題清單)。
  改完即還原。

無做不到的項目。

## 驗證

```
PYTHONPATH=src python3 -m pytest -q tests/test_docs_commit_types.py
→ 7 passed

PYTHONPATH=src python3 -m pytest -q --continue-on-collection-errors
→ 7 passed, 6 errors
```

7 = 原有 3 條 + 錨點看守 1 條 + 負向驗證 3 條(首/中/尾)。

6 個 collection error 為**容器環境既有問題,與本 PR 無關**:
`tests/test_{glossary,news,report,sources_integration,term_approval,term_discovery}_*.py`
匯入 `security_weekly_mcp`,而容器內未安裝第三方 `mcp` 套件、`packages/glossary/` submodule
亦未 checkout。已用 `git stash -u` 在乾淨工作區複驗:同樣 **3 passed, 6 errors**,
錯誤模組與數量完全相同(3 → 7 的差即本 PR 新增的 4 條)。
本 PR 只動一支純檔案讀取的測試,不觸及該匯入鏈。

`ruff` 容器內未安裝,未跑 lint;新增程式碼遵循 repo 既有風格(import 排序、無超過 100 字元的行;
E501 於 `[tool.ruff.lint]` 本就 ignore)。
