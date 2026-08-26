#!/usr/bin/env bash
# .asp/checks/render-drift.sh — committed 渲染物漂移檢查(asp-gate.yaml id: render-drift)
#
# 血緣:v4 session-audit.sh Iron Rule A 的信任外移承接(asp-ng issue #32 S1):
# 本地 sha256 自證(hook 驗 hook)退場,改由 Forge rulesets/CODEOWNERS(改動走人審)
# + 本檢查(渲染物與單一事實源一致,「漂移即 P0」——ADR-000 §7)組成完整性保證。
#
# 用法:render-drift.sh [專案根目錄]
#   缺參數取 ${ASP_GATE_PROJ:-.}。驗 committed 渲染物 header 的 `source sha256:`
#   與 asp-gate.yaml 實際 sha256 一致:.asp/gate.sh、.asp/ci.sh、.mega-linter.yml、
#   .github/workflows/asp-ci.yml(存在且帶 header 者才驗;無 header = 非渲染物)。
#   無 asp-gate.yaml / 無渲染物可驗 → exit 200(skip 契約);漂移 → exit 1。
set -u

BASE="${1:-${ASP_GATE_PROJ:-.}}"
SRC="$BASE/asp-gate.yaml"
if [ ! -f "$SRC" ]; then
  echo "⏭  render-drift: 無 asp-gate.yaml($SRC),略過"
  exit 200
fi
if ! command -v sha256sum >/dev/null 2>&1; then
  echo "⏭  render-drift: sha256sum 缺,略過"
  exit 200
fi

WANT=$(sha256sum "$SRC" | cut -d' ' -f1)
FOUND=0
FAIL=0
# asp-ci.yml **刻意不再帶 sha 錨點**(#290;#383 §2.6 定調為永久不得回收——
# 修後 workflow 與源無關,掛 sha 錨點的宣稱恆假,比不掛更糟)。清單保留該檔
# 是為了相容既有消費端(舊渲染物仍帶 header 者照驗);新渲染物無 header 即
# 自動略過。其漂移由 asp-ng 自身 CI 的全檔 diff + 人的 PR 審查承擔。
# 錨點改由 .asp/ci.sh 承接(#383):ci 層檢查清單自此住那一份,且它 worker 推得動。
for f in ".asp/gate.sh" ".asp/ci.sh" ".mega-linter.yml" ".github/workflows/asp-ci.yml"; do
  p="$BASE/$f"
  [ -f "$p" ] || continue
  got=$(grep -m1 -oE 'source sha256: [0-9a-f]{64}' "$p" 2>/dev/null | awk '{print $3}')
  if [ -z "$got" ]; then
    # .asp/gate.sh 與 .asp/ci.sh 是**被實際執行**的渲染物,必帶 header:原本無
    # header 即逐檔跳過,只要另一檔仍帶 header 就整體回報一致——刪 header 即可
    # 讓竄改的渲染物過關(補審 BLOCKER-2;#383 把 ci.sh 一併納入,它自本票起
    # 是 CI 唯一的 ci 層執行路徑)。另兩者容許手寫(非渲染的 lint 設定、無錨點
    # 的 workflow),維持不驗。
    case "$f" in
      ".asp/gate.sh"|".asp/ci.sh")
        echo "❌ render-drift: $f 無 'source sha256:' header——渲染物必帶來源標記,疑遭手改或取代"
        FOUND=1
        FAIL=1
        ;;
    esac
    continue
  fi
  FOUND=1
  if [ "$got" != "$WANT" ]; then
    echo "❌ render-drift: $f 的 source sha256 與 asp-gate.yaml 不符——渲染物漂移即 P0,重跑 asp render gate / asp render ci 後提交"
    FAIL=1
  fi
done

if [ "$FOUND" -eq 0 ]; then
  echo "⏭  render-drift: 無 committed 渲染物可驗,略過"
  exit 200
fi
[ "$FAIL" -eq 0 ] && echo "✅ render-drift: 渲染物與單一事實源(asp-gate.yaml)一致"
exit "$FAIL"
