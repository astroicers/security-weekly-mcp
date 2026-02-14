# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- RSS feed generator for weekly reports (`scripts/generate_rss.py`)
- Cross-repo RSS deployment to security-glossary-tw
- RSS subscription at `astroicers.github.io/security-glossary-tw/weekly/feed.xml`

### Changed
- Update pytest-asyncio to >=0.24
- Update pytest-cov to >=5.0
- Add Python 3.13 to CI test matrix
- Expand ruff lint rules (N, UP, ASYNC)
- Add MCP SDK version upper bound (<2.0.0)

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
