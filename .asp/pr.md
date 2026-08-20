# docs: CONTRIBUTING commit 型別清單改指向 AGENTS.md,消除第二份清單漂移

Closes #7

## 背景

PR #6 QA 輪 finding(🟡 warning 1):`CONTRIBUTING.md`「5. 提交變更」自帶一份 commit 型別清單
(`feat|fix|docs|test|refactor|chore`),缺 `report`、`ci`,與 `asp-gate.yaml` 的 commit-format
regex `^(feat|fix|docs|refactor|test|chore|report|ci)(\([a-z0-9-]+\))?: .+` 及 AGENTS.md
「分支與提交」矛盾。屬既有漂移,非 PR #6 引入。

依 issue 的兩個選項,採後者(消除第二份清單):補齊清單只是把漂移風險推遲到下次改 regex,
指向單一事實源才是結構性修法。

## 變更

- `CONTRIBUTING.md`:移除自帶型別清單,改為一句指向 [AGENTS.md「分支與提交」](AGENTS.md#分支與提交),
  並註明單一事實源為 `asp-gate.yaml` 的 `commit-format` 檢查。
  同一個 code block 的 commit 範例訊息一併從英文改為繁體中文(AGENTS.md §語言與風格:
  「文件與 commit 訊息使用繁體中文」),避免修掉一處矛盾又留下另一處。
- `tests/test_docs_commit_types.py`(新增):三條漂移防線,直接讀 `asp-gate.yaml` 解析 regex 型別:
  1. AGENTS.md 的型別清單與 gate regex 逐字一致(順序亦同);
  2. CONTRIBUTING.md 指向 AGENTS.md;
  3. CONTRIBUTING.md 不得再出現 `` - `type:` - 說明 `` 形式的第二份清單。

AGENTS.md 與 `asp-gate.yaml` 本身未改——兩者原本就一致,漂移只在 CONTRIBUTING.md 單邊。

## AC 逐條對照

- [x] **Given CONTRIBUTING.md,When 對照 asp-gate.yaml commit-format regex,Then 型別清單一致
  (或 CONTRIBUTING 直接指向 AGENTS.md 該節,消除第二份清單)**
  — 取括號內的後者:CONTRIBUTING.md 不再有第二份清單,改指向 AGENTS.md「分支與提交」,
  該節已明列 `feat|fix|docs|refactor|test|chore|report|ci` 並自陳與 `asp-gate.yaml` 一致。
  新增測試把「一致」從人工對照變成 CI 可驗的斷言。

無做不到的項目。

## 驗證

```
PYTHONPATH=packages/mcp-server/src python3 -m pytest -q --continue-on-collection-errors
→ 3 passed, 6 errors
```

新增的 3 條測試全綠。負向驗證:分別把清單塞回 CONTRIBUTING.md、把 `report` 從 AGENTS.md 刪掉,
對應測試各自轉紅,還原後轉綠——防線確實會擋。

6 個 collection error 為**容器環境既有問題,與本 PR 無關**:`tests/test_{glossary,news,report,
sources_integration,term_approval,term_discovery}_*.py` 匯入 `security_weekly_mcp`,而容器內未安裝
第三方 `mcp` 套件(`ModuleNotFoundError: No module named 'mcp'`),`packages/glossary/` submodule
亦未 checkout。已用 `git stash -u` 在乾淨工作區複驗:同樣 6 errors,數量與模組完全相同。
本 PR 只動文件與新增一支純檔案讀取的測試,不觸及該匯入鏈。

`ruff` 容器內未安裝,未跑 lint;新增測試檔遵循 repo 既有風格(line-length 100、import 排序)。
