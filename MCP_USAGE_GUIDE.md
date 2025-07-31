# リポジトリMCP化システム 利用ガイド

## 概要
任意のリポジトリを自動的にMCP（Model Context Protocol）サーバーに変換し、Claude Desktopで直接操作可能にするシステムです。

## システム機能
- **リポジトリ自動解析**: 多言語対応の構造解析・依存関係・重要度判定
- **MCP設定自動生成**: Tools・Resources・Prompts自動生成
- **Claude Desktop統合**: JSON-RPC over STDIO互換
- **ワンコマンド実行**: エラーハンドリング付きの簡単実行

## 🚀 クイックスタート

### 1. システム起動
```bash
# リポジトリMCP化システム実行
./scripts/quick-setup.sh start

# または手動実行
python mcp-system/repo_to_mcp.py [リポジトリパス]
```

### 2. 出力確認
実行後、以下のファイルが生成されます：
- `mcp_server.py` - MCPサーバー本体
- `claude_desktop_config.json` - Claude Desktop設定（既存設定に追加）

### 3. Claude Desktop連携設定

#### 設定ファイル更新
Claude Desktopの設定ファイルに以下を追加：

**Windows**:
```
C:\Users\[ユーザー名]\AppData\Roaming\Claude\claude_desktop_config.json
```

**macOS**:
```
~/Library/Application Support/Claude/claude_desktop_config.json
```

**Linux**:
```
~/.config/claude/claude_desktop_config.json
```

#### 設定内容例
```json
{
  "mcpServers": {
    "your-repo-mcp": {
      "command": "python",
      "args": ["/path/to/your/mcp_server.py"],
      "env": {}
    }
  }
}
```

### 4. MCPサーバー起動・接続確認
```bash
# MCPサーバー起動テスト
python mcp_server.py

# Claude Desktop再起動
# MCPサーバーが自動認識されることを確認
```

## 📁 対応リポジトリタイプ
- **Python**: Django, Flask, FastAPI, etc.
- **JavaScript/TypeScript**: React, Node.js, Vue.js, etc.
- **Java**: Spring Boot, Maven, Gradle, etc.
- **C/C++**: CMake, Makefile, etc.
- **Go**: Go modules, etc.
- **Rust**: Cargo projects, etc.
- **その他**: 汎用的なファイル構造解析

## 🛠 高度な設定

### カスタム解析設定
```python
# mcp-system/config.py で設定変更可能
ANALYSIS_DEPTH = 3  # 解析深度
EXCLUDE_PATTERNS = ['.git', 'node_modules', '__pycache__']
IMPORTANT_FILES = ['README.md', 'package.json', 'requirements.txt']
```

### 言語別特殊設定
システムは自動的に以下を検出・設定：
- 依存関係ファイル（package.json, requirements.txt, etc.）
- ビルド設定（Makefile, webpack.config.js, etc.）
- 設定ファイル（.env, config.yaml, etc.）

## 🐛 トラブルシューティング

### よくある問題と解決方法

#### 1. MCPサーバーが起動しない
```bash
# ログ確認
tail -f logs/mcp_server.log

# 依存関係確認
pip install -r requirements.txt
```

#### 2. Claude Desktopで認識されない
- Claude Desktop設定ファイルのパスを確認
- JSON構文エラーがないかチェック
- Claude Desktopを完全再起動

#### 3. リポジトリ解析エラー
```bash
# 権限確認
chmod +r -R [リポジトリパス]

# 大容量リポジトリの場合
python repo_to_mcp.py --max-files 1000 [リポジトリパス]
```

#### 4. パフォーマンス問題
```bash
# 除外パターン追加
python repo_to_mcp.py --exclude "*.log,*.tmp,build/*" [リポジトリパス]
```

### デバッグモード
```bash
# 詳細ログ出力
python repo_to_mcp.py --verbose [リポジトリパス]

# 解析結果のみ出力（MCPサーバー生成なし）
python repo_to_mcp.py --analyze-only [リポジトリパス]
```

## 🔧 システム拡張

### 新言語サポート追加
1. `language_analyzers/` に新言語アナライザー追加
2. `config.py` の `SUPPORTED_LANGUAGES` に追加
3. テストケース作成

### カスタムMCPツール追加
1. `mcp_tools/` にツール実装追加
2. `tool_generator.py` でツール生成ロジック更新

## 📊 利用統計・監視
```bash
# 利用統計確認
python scripts/monitor.sh stats

# リアルタイム監視
python scripts/monitor.sh live
```

## 🚨 セキュリティ注意事項
- 機密リポジトリの取り扱いに注意
- MCPサーバーは適切な権限で実行
- ネットワークアクセス制限の設定推奨

## ⚡ パフォーマンス最適化
- 大規模リポジトリ: `--max-files` オプション使用
- 頻繁な更新: キャッシュ機能活用
- メモリ使用量: `--memory-limit` オプション指定

---

## サポート・フィードバック
問題報告・機能要望は Issues または logs/feedback.txt に記録してください。