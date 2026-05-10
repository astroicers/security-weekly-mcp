# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- RSS feed generator for weekly reports (`scripts/generate_rss.py`)
- Cross-repo RSS deployment to security-glossary-tw
- RSS subscription at `astroicers.github.io/security-glossary-tw/weekly/feed.xml`
- ASP 合規文件：`docs/adr/ADR-001-mcp-server-architecture.md`（Accepted）
- ASP 合規文件：`docs/specs/SPEC-001-mcp-server.md`（7 欄位含 Done When、副作用、邊界情況）

### Changed
- Update pytest-asyncio to >=0.24
- Update pytest-cov to >=5.0
- Add Python 3.13 to CI test matrix
- Expand ruff lint rules (N, UP, ASYNC)
- Add MCP SDK version upper bound (<2.0.0)
- 修正 README：台灣來源 3→5 個、週報工具 2→3 個、output 格式 .json→.md

## [0.1.0] - 2026-02-15

### Added
- Initial MCP Server release with 17 tools
- 32 security news sources configuration
- Glossary integration (security-glossary-tw submodule)
- Two-phase weekly report architecture
  - `collect_weekly_data.py` for automated data collection
  - `load_weekly_data` and `list_weekly_data` MCP tools
- GitHub Actions workflows
  - CI (test, lint, security audit)
  - Release workflow
  - Weekly data collection
  - Glossary submodule auto-update
- Term approval workflow with validation
- Codecov integration
- CONTRIBUTING.md and config documentation
