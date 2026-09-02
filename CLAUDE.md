本 repo 慣例見 AGENTS.md;專案總覽與 MCP 工具清單見 README.md。
開工順序:AGENTS.md → README.md 對應章節 → CONTRIBUTING.md(貢獻流程細節)。

## Claude Code 專屬

- MCP server 註冊:設定方式見 README.md「設定 Claude Code MCP」(以 `uv run --directory <repo 根> --package security-weekly-mcp-server` 啟動 `security_weekly_mcp.server`)。
- 自然語言介面:skill `~/.claude/skills/security-weekly-tw/`(「產生週報」「審核術語」等觸發);原始碼在本 repo `skill/`。
- 週報產生流程(README.md「週報產生架構」)中的 WebSearch/WebFetch 補充階段由 Claude Code 執行——涵蓋 TWCERT/CC、資安人等無 RSS 來源;查詢模板見 `config/search_templates.yaml`。
