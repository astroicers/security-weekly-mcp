# Contributing Guide

感謝您對 Security Weekly MCP 的貢獻興趣！

## 開發環境設定

### 前置需求

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) (Python 套件管理器)
- [Typst](https://typst.app/) (PDF 編譯，可選)

### 安裝步驟

```bash
# Clone 專案（含 submodule）
git clone --recursive https://github.com/astroicers/security-weekly-mcp.git
cd security-weekly-mcp

# 安裝依賴
uv sync

# 執行測試
uv run pytest
```

## 專案結構

```
security-weekly-mcp/
├── packages/
│   ├── glossary/          # Git Submodule (security-glossary-tw)
│   └── mcp-server/        # MCP Server 主程式
├── skill/                 # Claude Code Skill 定義
├── config/                # 設定檔
├── scripts/               # 自動化腳本
└── tests/                 # 單元測試
```

## 開發流程

### 1. 建立功能分支

```bash
git checkout -b feature/your-feature-name
```

### 2. 撰寫程式碼

- 遵循 PEP 8 和專案現有風格
- 使用 `ruff` 進行程式碼檢查
- 為新功能撰寫測試

### 3. 執行測試

```bash
# 執行所有測試
uv run pytest

# 執行特定測試
uv run pytest tests/test_term_approval.py -v

# 跳過慢速網路測試
uv run pytest -m "not slow"

# 覆蓋率報告
uv run pytest --cov=security_weekly_mcp --cov-report=html
```

### 4. 程式碼檢查

```bash
# Linting
uv run ruff check packages/

# 格式檢查
uv run ruff format --check packages/
```

### 5. 提交變更

```bash
git add .
git commit -m "feat: add your feature description"
```

提交訊息格式：
- `feat:` - 新功能
- `fix:` - Bug 修復
- `docs:` - 文件更新
- `test:` - 測試相關
- `refactor:` - 重構
- `chore:` - 雜項維護

### 6. 建立 Pull Request

- 清楚描述變更內容
- 確保 CI 測試通過
- 關聯相關 Issue

## MCP 工具開發

### 新增工具

1. 在 `packages/mcp-server/src/security_weekly_mcp/tools/` 選擇對應模組
2. 在 `list_tools()` 加入工具定義
3. 在 `call_tool()` 實作邏輯
4. 撰寫單元測試
5. 更新 `README.md` 工具清單

### 工具定義範例

```python
Tool(
    name="your_tool_name",
    description="工具描述（中文）",
    inputSchema={
        "type": "object",
        "properties": {
            "param1": {
                "type": "string",
                "description": "參數說明"
            }
        },
        "required": ["param1"]
    }
)
```

## 測試規範

- 每個 MCP 工具至少要有基本測試
- 使用 `pytest.mark.asyncio` 標記非同步測試
- 使用 `pytest.fixture` 共享測試資源
- 網路相關測試標記 `@pytest.mark.slow`

## 術語庫貢獻

術語庫是獨立的 Git Submodule，請在 [security-glossary-tw](https://github.com/astroicers/security-glossary-tw) 提交術語相關 PR。

## 問題回報

請在 [GitHub Issues](https://github.com/astroicers/security-weekly-mcp/issues) 回報問題，並提供：

- 問題描述
- 重現步驟
- 預期行為
- 環境資訊（Python 版本、作業系統）

## 授權

提交 PR 即表示同意以 MIT 授權貢獻您的程式碼。
