# リポジトリMCP化システム アーキテクチャ設計書

## システム概要
任意のリポジトリを自動的にMCP（Model Context Protocol）サーバーに変換するシステムのアーキテクチャ仕様書

## 🏗 システム構成

### コアコンポーネント
```
repo-to-mcp-system/
├── repository_analyzer/     # リポジトリ解析エンジン
│   ├── structure_analyzer.py    # ディレクトリ構造解析
│   ├── language_detector.py     # 言語・フレームワーク検出
│   ├── dependency_analyzer.py   # 依存関係解析
│   └── importance_scorer.py     # ファイル重要度判定
├── mcp_generator/          # MCP設定生成器
│   ├── tool_generator.py        # MCPツール定義生成
│   ├── resource_generator.py    # リソース定義生成
│   ├── prompt_generator.py      # プロンプト定義生成
│   └── server_template.py       # MCPサーバー雛形
├── execution_interface/    # 実行インターフェース
│   ├── main_controller.py       # メインコントローラー
│   ├── error_handler.py         # エラーハンドリング
│   └── config_manager.py        # 設定管理
└── generated/             # 生成物出力先
    ├── mcp_server.py           # 生成MCPサーバー
    └── claude_desktop_config.json  # Claude Desktop設定
```

## 🔍 リポジトリ解析エンジン

### 構造解析フロー
```python
# 1. ディレクトリ構造スキャン
def analyze_structure(repo_path):
    tree = scan_directory_tree(repo_path)
    return classify_directories(tree)

# 2. 言語・フレームワーク検出
def detect_languages(structure):
    languages = detect_by_extensions(structure)
    frameworks = detect_by_config_files(structure)
    return merge_detection_results(languages, frameworks)

# 3. 依存関係解析
def analyze_dependencies(structure, languages):
    deps = {}
    for lang in languages:
        deps[lang] = parse_dependency_files(lang, structure)
    return deps

# 4. 重要度スコアリング
def score_importance(files, dependencies):
    scores = {}
    for file in files:
        scores[file] = calculate_importance_score(
            file, dependencies, access_frequency, code_complexity
        )
    return scores
```

### サポート言語・フレームワーク
| 言語 | 検出方法 | 依存関係ファイル | 特殊処理 |
|------|----------|------------------|----------|
| Python | .py, requirements.txt | requirements.txt, pyproject.toml | ast構文解析 |
| JavaScript/TypeScript | .js/.ts, package.json | package.json, yarn.lock | tree-sitter解析 |
| Java | .java, pom.xml | pom.xml, build.gradle | Maven/Gradle検出 |
| C/C++ | .c/.cpp, CMakeLists.txt | CMakeLists.txt, Makefile | include解析 |
| Go | .go, go.mod | go.mod, go.sum | module解析 |
| Rust | .rs, Cargo.toml | Cargo.toml, Cargo.lock | crate解析 |

## ⚙️ MCP設定生成器

### Tool生成ロジック
```python
def generate_mcp_tools(analysis_result):
    tools = []
    
    # ファイル操作ツール
    tools.append(create_file_reader_tool(analysis_result.important_files))
    tools.append(create_file_writer_tool(analysis_result.writable_files))
    
    # コード解析ツール
    tools.append(create_code_search_tool(analysis_result.languages))
    tools.append(create_dependency_tool(analysis_result.dependencies))
    
    # ビルド・実行ツール
    if analysis_result.build_system:
        tools.append(create_build_tool(analysis_result.build_system))
    
    return tools
```

### Resource生成ロジック
```python
def generate_mcp_resources(analysis_result):
    resources = []
    
    # 重要ファイルをリソース化
    for file in analysis_result.important_files:
        resources.append({
            "uri": f"file://{file.path}",
            "name": file.name,
            "description": file.description,
            "mimeType": get_mime_type(file.extension)
        })
    
    # プロジェクト概要リソース
    resources.append(create_project_overview_resource(analysis_result))
    
    return resources
```

### Prompt生成ロジック
```python
def generate_mcp_prompts(analysis_result):
    prompts = []
    
    # プロジェクト固有プロンプト
    prompts.append(create_project_context_prompt(analysis_result))
    
    # 言語固有プロンプト
    for lang in analysis_result.languages:
        prompts.append(create_language_specific_prompt(lang, analysis_result))
        
    # タスク固有プロンプト
    prompts.extend(create_task_prompts(analysis_result.project_type))
    
    return prompts
```

## 🚀 実行インターフェース

### メインコントローラーフロー
```python
class MainController:
    def execute(self, repo_path, options):
        try:
            # 1. リポジトリ解析
            analysis = self.analyzer.analyze(repo_path)
            
            # 2. MCP設定生成
            mcp_config = self.generator.generate(analysis)
            
            # 3. MCPサーバー生成
            server_code = self.generator.create_server(mcp_config)
            
            # 4. ファイル出力
            self.output_manager.save(server_code, mcp_config)
            
            return ExecutionResult(success=True, 
                                 output_files=self.output_manager.files)
                                 
        except Exception as e:
            return self.error_handler.handle(e)
```

### エラーハンドリング戦略
```python
class ErrorHandler:
    def handle(self, error):
        if isinstance(error, PermissionError):
            return self.handle_permission_error(error)
        elif isinstance(error, FileNotFoundError):
            return self.handle_file_not_found(error)
        elif isinstance(error, AnalysisError):
            return self.handle_analysis_error(error)
        else:
            return self.handle_unknown_error(error)
```

## 🔌 MCP通信プロトコル

### JSON-RPC over STDIO仕様
```python
# MCPサーバー基本構造
class MCPServer:
    def __init__(self, repo_analysis):
        self.analysis = repo_analysis
        self.tools = self.create_tools()
        self.resources = self.create_resources()
        
    async def handle_request(self, request):
        method = request.get('method')
        
        if method == 'tools/list':
            return self.list_tools()
        elif method == 'tools/call':
            return await self.call_tool(request['params'])
        elif method == 'resources/list':
            return self.list_resources()
        elif method == 'resources/read':
            return await self.read_resource(request['params'])
        else:
            raise MethodNotFound(f"Unknown method: {method}")
```

### Claude Desktop統合仕様
```json
{
  "mcpServers": {
    "generated-repo-mcp": {
      "command": "python",
      "args": ["path/to/generated/mcp_server.py"],
      "env": {
        "REPO_PATH": "/path/to/analyzed/repo",
        "LOG_LEVEL": "INFO"
      }
    }
  }
}
```

## 🎯 パフォーマンス最適化

### メモリ使用量最適化
- ファイル内容の遅延読み込み
- 大容量ファイルのストリーミング処理
- LRUキャッシュによる解析結果保存

### 処理速度最適化
- 並列ファイル解析
- インクリメンタル解析（変更検出）
- インデックス化による高速検索

### スケーラビリティ
| リポジトリサイズ | 処理時間 | メモリ使用量 | 推奨設定 |
|------------------|----------|--------------|----------|
| ~1,000ファイル | 10秒 | 100MB | デフォルト |
| ~10,000ファイル | 60秒 | 500MB | --max-files 5000 |
| ~100,000ファイル | 300秒 | 2GB | --exclude大量パターン |

## 🔒 セキュリティ考慮事項

### アクセス制御
- ファイル読み取り権限の事前チェック
- 実行可能ファイルの検出・警告
- 機密ファイルパターンの自動除外

### データ保護
- 一時ファイルの自動削除
- ログファイルの機密情報マスキング
- 通信内容の暗号化（必要に応じて）

## 🧪 テスト戦略

### 単体テスト
- 各コンポーネントの独立テスト
- モックを使用した依存関係分離
- エッジケース・異常系テスト

### 統合テスト
- 実際のリポジトリでのエンドツーエンドテスト
- Claude Desktop連携テスト
- パフォーマンステスト

### 品質保証
- コードカバレッジ90%以上
- 静的解析（pylint, mypy）
- セキュリティスキャン

## 🚀 拡張性設計

### プラグインアーキテクチャ
```python
class LanguagePlugin:
    def detect(self, structure): pass
    def analyze_dependencies(self, structure): pass
    def generate_tools(self, analysis): pass
```

### 設定駆動アーキテクチャ
- YAML/JSON設定ファイル
- 環境変数オーバーライド
- ランタイム設定変更

## 📊 監視・ログ

### ログ戦略
- 構造化ログ（JSON形式）
- ログレベル別出力
- エラー追跡・アラート

### メトリクス収集
- 処理時間・成功率
- リソース使用量
- ユーザー操作統計

---

本アーキテクチャは拡張性・保守性・性能を重視した設計となっており、様々なリポジトリタイプに対応可能な柔軟な構造を提供します。