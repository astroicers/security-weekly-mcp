.PHONY: help test test-all test-quick lint lint-fix format format-check \
        audit-quick audit-health asp-refresh install sync server dev

.DEFAULT_GOAL := help

help:  ## 列出所有可用目標
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

install:  ## 安裝所有依賴
	uv sync

sync:  ## 同步依賴並更新 submodule
	git submodule update --init --recursive
	uv sync

test:  ## 執行快速測試（排除 slow/integration）
	uv run pytest tests/ -v --tb=short -m "not slow and not integration" \
		--cov=security_weekly_mcp --cov-report=term-missing

test-all:  ## 執行全部測試（含 slow marker）
	uv run pytest tests/ -v --tb=short \
		--cov=security_weekly_mcp --cov-report=term-missing --cov-report=xml

test-quick:  ## 快速跑（無 coverage，開發用）
	uv run pytest tests/ -x --tb=short -m "not slow and not integration" -q

lint:  ## ruff check（linting）
	uv run ruff check packages/mcp-server/

lint-fix:  ## ruff check --fix（自動修正）
	uv run ruff check --fix packages/mcp-server/

format:  ## ruff format（格式化）
	uv run ruff format packages/mcp-server/

format-check:  ## 檢查格式（不修改）
	uv run ruff format --check packages/mcp-server/

audit-quick:  ## 依賴安全審計（pip-audit）
	uv run pip-audit --strict

audit-health:  ## ASP 7+2 維度完整健康審計
	@bash ~/.claude/asp/scripts/audit-fallback.sh

asp-refresh:  ## 重新產生 audit baseline（.asp-audit-baseline.json）
	@bash ~/.claude/asp/scripts/audit-fallback.sh 2>&1 | tee /tmp/asp-audit-output.txt
	@echo '{"generated":"'$$(date -u +%Y-%m-%dT%H:%M:%SZ)'","source":"audit-fallback.sh"}' \
		> .asp-audit-baseline.json
	@echo "Baseline 已更新：.asp-audit-baseline.json"

server:  ## 以 stdio 模式啟動 MCP Server
	uv run --package security-weekly-mcp-server python -m security_weekly_mcp.server

dev:  ## 以 MCP Inspector 開發模式啟動
	uv run --package security-weekly-mcp-server mcp dev \
		packages/mcp-server/src/security_weekly_mcp/server.py
