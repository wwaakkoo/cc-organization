# cc-organization MCP Server

## セットアップ

### 1. 依存関係インストール
```bash
pip install mcp
```

### 2. Claude Desktop設定に追加
設定ファイル `~/Library/Application Support/Claude/claude_desktop_config.json` に以下を追加:

```json
{
  "mcpServers": {
    "cc-organization-repo": {
      "command": "python",
      "args": ["mcp_output/cc-organization_mcp_server.py"],
      "env": {
        "REPO_PATH": "/home/hi_ry/cc-organization",
        "REPO_NAME": "cc-organization"
      }
    }
  }
}
```

### 3. Claude Desktop再起動

## 利用可能な機能

### Tools
- `read_file`: ファイル読み取り
- `search_files`: ファイル検索
- `search_code`: コード検索

### Resources
- 重要ファイル (18 files)
- リポジトリ概要

## プロジェクト情報
- **タイプ**: general
- **言語**: markdown, shell, text, python, config
- **ファイル数**: 18
- **重要ファイル**: 18
