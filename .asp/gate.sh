#!/usr/bin/env bash
# ⚠️ 由 `asp render gate` 產生 — 勿手改(單一事實源:asp-gate.yaml)
# source sha256: 7cd45c24767e09ac1c79365ec37df60694c7f455dfd919939576001e89d02485
# gate 子集:lint, gitleaks, commit-format
set -u
STRICT="${ASP_GATE_STRICT:-0}"
WARNINGS=0

skip() { echo "⏭  $1: 略過($2)"; }

run_check() {  # id severity required_bin cmd...
  local id="$1" sev="$2" req="$3"; shift 3
  if ! command -v "$req" >/dev/null 2>&1; then
    if [ "$STRICT" = "1" ] && [ "$sev" = "blocker" ]; then
      echo "❌ BLOCKER $id: 工具缺失 $req(strict 模式)"; exit 1
    fi
    skip "$id" "工具未安裝:$req(vendoring 由 P2 base image 落地)"; return 0
  fi
  if "$@" >/dev/null 2>&1; then
    echo "✅ $id"
  else
    case "$sev" in
      blocker) echo "❌ BLOCKER $id"; exit 1 ;;
      warning) echo "⚠️  $id(warning)"; WARNINGS=$((WARNINGS+1)) ;;
      *)       echo "ℹ️  $id(info)" ;;
    esac
  fi
}

run_check 'lint:yaml' warning 'yamllint' 'yamllint' '.'
run_check 'lint:markdown' warning 'markdownlint-cli2' 'markdownlint-cli2' '**/*.md'
run_check 'gitleaks' blocker 'gitleaks' 'gitleaks' 'protect' '--staged' '--config' '.asp/gitleaks.toml'
if [ -z "$(git log -1 --no-merges --format=%s 2>/dev/null)" ]; then
  skip 'commit-format' '無非 merge commit 可驗(淺 clone)'
else
  run_check 'commit-format' blocker git bash -c 'git log -1 --no-merges --format=%s | grep -qE "^(feat|fix|docs|refactor|test|chore|report|ci)(\([a-z0-9-]+\))?: .+"'
fi

echo "gate 通過(warnings=$WARNINGS)"
exit 0
