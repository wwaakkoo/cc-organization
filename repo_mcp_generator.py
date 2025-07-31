#!/usr/bin/env python3
"""
Repository MCP Generator - Complete Implementation
リポジトリを解析してMCPサーバーを自動生成するツール
"""

import os
import json
import sys
import argparse
import logging
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Set, Any
import subprocess
import mimetypes
from collections import defaultdict

# 設定とログ
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class FileInfo:
    """ファイル情報"""
    path: str
    language: str
    size: int
    importance: int  # 1-10
    functions: List[str]
    classes: List[str]
    dependencies: Set[str]

@dataclass
class RepositoryAnalysis:
    """リポジトリ解析結果"""
    name: str
    root_path: str
    languages: Dict[str, int]  # 言語とファイル数
    files: List[FileInfo]
    structure: Dict[str, Any]
    dependencies: Dict[str, List[str]]
    important_files: List[str]
    project_type: str

class RepositoryAnalyzer:
    """リポジトリ解析エンジン"""
    
    # 言語別ファイル拡張子
    LANGUAGE_EXTENSIONS = {
        'python': ['.py', '.pyw', '.pyi'],
        'javascript': ['.js', '.jsx', '.mjs'],
        'typescript': ['.ts', '.tsx'],
        'java': ['.java'],
        'go': ['.go'],
        'rust': ['.rs'],
        'cpp': ['.cpp', '.cc', '.cxx', '.c++', '.hpp', '.h'],
        'c': ['.c', '.h'],
        'shell': ['.sh', '.bash', '.zsh'],
        'yaml': ['.yml', '.yaml'],
        'json': ['.json'],
        'markdown': ['.md', '.markdown'],
        'docker': ['Dockerfile', '.dockerignore'],
        'config': ['.toml', '.ini', '.cfg', '.conf']
    }
    
    # 重要ファイル判定パターン
    IMPORTANT_PATTERNS = [
        'main.py', 'app.py', 'server.py', '__init__.py',
        'index.js', 'app.js', 'server.js',
        'main.go', 'main.rs', 'Main.java',
        'package.json', 'requirements.txt', 'Cargo.toml', 'go.mod',
        'README.md', 'CHANGELOG.md', 'LICENSE',
        'Dockerfile', 'docker-compose.yml',
        '.gitignore', 'Makefile', 'setup.py'
    ]
    
    def __init__(self, repo_path: str):
        self.repo_path = Path(repo_path).resolve()
        self.ignore_patterns = self._load_ignore_patterns()
    
    def _load_ignore_patterns(self) -> Set[str]:
        """gitignoreファイルから無視パターンを読み込み"""
        ignore_patterns = {
            '.git', '__pycache__', 'node_modules', '.venv', 'venv',
            '.pytest_cache', '.coverage', 'dist', 'build', '.tox',
            '*.pyc', '*.pyo', '*.egg-info', '.DS_Store'
        }
        
        gitignore_path = self.repo_path / '.gitignore'
        if gitignore_path.exists():
            try:
                with open(gitignore_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            ignore_patterns.add(line)
            except Exception as e:
                logger.warning(f"Failed to read .gitignore: {e}")
        
        return ignore_patterns
    
    def _should_ignore(self, path: Path) -> bool:
        """ファイル/ディレクトリを無視するかどうか判定"""
        path_str = str(path.relative_to(self.repo_path))
        
        for pattern in self.ignore_patterns:
            if pattern in path_str or path.name == pattern:
                return True
        
        # バイナリファイル判定
        if path.is_file():
            try:
                mimetype, _ = mimetypes.guess_type(str(path))
                if mimetype and not mimetype.startswith('text/'):
                    return True
            except:
                pass
        
        return False
    
    def _detect_language(self, file_path: Path) -> str:
        """ファイルの言語を検出"""
        suffix = file_path.suffix.lower()
        name = file_path.name.lower()
        
        # 特殊ファイル名
        if name in ['dockerfile', 'makefile']:
            return 'docker' if name == 'dockerfile' else 'make'
        
        # 拡張子ベース
        for lang, extensions in self.LANGUAGE_EXTENSIONS.items():
            if suffix in extensions or name in extensions:
                return lang
        
        return 'text'
    
    def _calculate_importance(self, file_info: FileInfo) -> int:
        """ファイルの重要度を計算 (1-10)"""
        score = 1
        path = Path(file_info.path)
        
        # ファイル名ベース
        if any(pattern in path.name.lower() for pattern in self.IMPORTANT_PATTERNS):
            score += 3
        
        # ディレクトリレベル（ルートに近いほど重要）
        depth = len(path.parts) - len(Path(self.repo_path).parts)
        if depth <= 2:
            score += 2
        
        # ファイルサイズ（適度なサイズが重要）
        if 100 < file_info.size < 10000:
            score += 1
        elif file_info.size > 50000:
            score += 2
        
        # 言語別重要度
        if file_info.language in ['python', 'javascript', 'typescript', 'java', 'go', 'rust']:
            score += 1
        
        # 設定ファイル
        if file_info.language in ['json', 'yaml', 'config']:
            score += 1
        
        return min(score, 10)
    
    def _analyze_file_content(self, file_path: Path) -> Dict[str, List[str]]:
        """ファイル内容を解析してクラス・関数を抽出"""
        functions = []
        classes = []
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            language = self._detect_language(file_path)
            
            if language == 'python':
                # Python関数・クラス抽出
                import re
                functions = re.findall(r'def\s+(\w+)', content)
                classes = re.findall(r'class\s+(\w+)', content)
            
            elif language in ['javascript', 'typescript']:
                # JavaScript/TypeScript関数・クラス抽出
                import re
                functions = re.findall(r'function\s+(\w+)|(\w+)\s*=\s*\(.*?\)\s*=>', content)
                functions = [f[0] or f[1] for f in functions if f[0] or f[1]]
                classes = re.findall(r'class\s+(\w+)', content)
            
            elif language == 'java':
                # Java関数・クラス抽出
                import re
                functions = re.findall(r'public\s+.*?\s+(\w+)\s*\(', content)
                classes = re.findall(r'class\s+(\w+)', content)
            
        except Exception as e:
            logger.debug(f"Failed to analyze {file_path}: {e}")
        
        return {'functions': functions, 'classes': classes}
    
    def _detect_dependencies(self, file_path: Path) -> Set[str]:
        """ファイルの依存関係を検出"""
        dependencies = set()
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            language = self._detect_language(file_path)
            
            if language == 'python':
                import re
                # import文抽出
                imports = re.findall(r'(?:from\s+(\S+)\s+)?import\s+([^\n]+)', content)
                for from_module, import_items in imports:
                    if from_module:
                        dependencies.add(from_module)
                    else:
                        dependencies.add(import_items.split(',')[0].strip())
            
            elif language in ['javascript', 'typescript']:
                import re
                # require/import文抽出
                requires = re.findall(r'require\s*\(\s*[\'"]([^\'"]+)[\'"]', content)
                imports = re.findall(r'import.*?from\s+[\'"]([^\'"]+)[\'"]', content)
                dependencies.update(requires + imports)
            
        except Exception as e:
            logger.debug(f"Failed to detect dependencies in {file_path}: {e}")
        
        return dependencies
    
    def _detect_project_type(self, files: List[FileInfo]) -> str:
        """プロジェクトタイプを検出"""
        languages = [f.language for f in files]
        file_names = [Path(f.path).name.lower() for f in files]
        
        # Web系
        if any(name in file_names for name in ['package.json', 'index.html', 'app.js']):
            return 'web_application'
        
        # Python系
        if 'requirements.txt' in file_names or 'setup.py' in file_names:
            if 'django' in str(files) or 'flask' in str(files):
                return 'python_web'
            else:
                return 'python_library'
        
        # Go
        if 'go.mod' in file_names:
            return 'go_application'
        
        # Rust
        if 'cargo.toml' in file_names:
            return 'rust_application'
        
        # Java
        if 'pom.xml' in file_names or any('java' in lang for lang in languages):
            return 'java_application'
        
        # Docker
        if 'dockerfile' in file_names:
            return 'containerized_application'
        
        return 'general'
    
    def analyze(self) -> RepositoryAnalysis:
        """リポジトリを完全解析"""
        logger.info(f"Analyzing repository: {self.repo_path}")
        
        files = []
        languages = defaultdict(int)
        structure = {}
        
        # ファイル走査
        for file_path in self.repo_path.rglob('*'):
            if file_path.is_file() and not self._should_ignore(file_path):
                try:
                    language = self._detect_language(file_path)
                    languages[language] += 1
                    
                    size = file_path.stat().st_size
                    content_analysis = self._analyze_file_content(file_path)
                    dependencies = self._detect_dependencies(file_path)
                    
                    file_info = FileInfo(
                        path=str(file_path.relative_to(self.repo_path)),
                        language=language,
                        size=size,
                        importance=0,  # 後で計算
                        functions=content_analysis['functions'],
                        classes=content_analysis['classes'],
                        dependencies=dependencies
                    )
                    
                    file_info.importance = self._calculate_importance(file_info)
                    files.append(file_info)
                    
                except Exception as e:
                    logger.debug(f"Failed to analyze {file_path}: {e}")
        
        # 重要ファイル特定
        important_files = [f.path for f in sorted(files, key=lambda x: x.importance, reverse=True)[:20]]
        
        # 依存関係マップ構築
        deps_map = {}
        for file_info in files:
            if file_info.dependencies:
                deps_map[file_info.path] = list(file_info.dependencies)
        
        # プロジェクトタイプ検出
        project_type = self._detect_project_type(files)
        
        return RepositoryAnalysis(
            name=self.repo_path.name,
            root_path=str(self.repo_path),
            languages=dict(languages),
            files=files,
            structure=structure,
            dependencies=deps_map,
            important_files=important_files,
            project_type=project_type
        )

class MCPConfigGenerator:
    """MCP設定生成器"""
    
    def __init__(self, analysis: RepositoryAnalysis):
        self.analysis = analysis
    
    def _generate_tools(self) -> List[Dict[str, Any]]:
        """Tools設定生成"""
        tools = []
        
        # ファイル読み取りツール
        tools.append({
            "name": "read_file",
            "description": f"Read any file from the {self.analysis.name} repository",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "File path relative to repository root"
                    }
                },
                "required": ["path"]
            }
        })
        
        # ファイル検索ツール
        tools.append({
            "name": "search_files",
            "description": f"Search for files in the {self.analysis.name} repository by pattern",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "pattern": {
                        "type": "string",
                        "description": "File name pattern (supports wildcards)"
                    },
                    "language": {
                        "type": "string",
                        "description": "Filter by programming language"
                    }
                },
                "required": ["pattern"]
            }
        })
        
        # コード検索ツール
        tools.append({
            "name": "search_code",
            "description": f"Search for code patterns in the {self.analysis.name} repository",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Code pattern to search for"
                    },
                    "file_type": {
                        "type": "string",
                        "description": "File extension to limit search to"
                    }
                },
                "required": ["query"]
            }
        })
        
        # 言語別特殊ツール
        if 'python' in self.analysis.languages:
            tools.append({
                "name": "analyze_python",
                "description": "Analyze Python code structure and dependencies",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "file_path": {
                            "type": "string",
                            "description": "Python file to analyze"
                        }
                    },
                    "required": ["file_path"]
                }
            })
        
        return tools
    
    def _generate_resources(self) -> List[Dict[str, Any]]:
        """Resources設定生成"""
        resources = []
        
        # 重要ファイルをリソースとして登録
        for file_path in self.analysis.important_files[:10]:  # 上位10件
            file_info = next((f for f in self.analysis.files if f.path == file_path), None)
            if file_info:
                resources.append({
                    "uri": f"file://{file_path}",
                    "name": f"{self.analysis.name}/{file_path}",
                    "description": f"{file_info.language.title()} file - {len(file_info.functions)} functions, {len(file_info.classes)} classes",
                    "mimeType": self._get_mime_type(file_info.language)
                })
        
        # プロジェクト概要
        resources.append({
            "uri": f"repo://{self.analysis.name}/overview",
            "name": f"{self.analysis.name} Overview",
            "description": f"Repository overview: {len(self.analysis.files)} files, {len(self.analysis.languages)} languages",
            "mimeType": "application/json"
        })
        
        return resources
    
    def _generate_prompts(self) -> List[Dict[str, Any]]:
        """Prompts設定生成"""
        prompts = []
        
        # コード解説プロンプト
        prompts.append({
            "name": "explain_code",
            "description": f"Explain code from the {self.analysis.name} repository",
            "arguments": [
                {
                    "name": "file_path",
                    "description": "Path to the file to explain",
                    "required": True
                },
                {
                    "name": "detail_level",
                    "description": "Level of detail (basic, detailed, expert)",
                    "required": False
                }
            ]
        })
        
        # アーキテクチャ分析プロンプト
        prompts.append({
            "name": "analyze_architecture",
            "description": f"Analyze the architecture of the {self.analysis.name} project",
            "arguments": [
                {
                    "name": "focus_area",
                    "description": "Area to focus on (structure, dependencies, patterns)",
                    "required": False
                }
            ]
        })
        
        # プロジェクト固有プロンプト
        if self.analysis.project_type == 'web_application':
            prompts.append({
                "name": "review_web_security",
                "description": f"Review web security aspects of the {self.analysis.name} application",
                "arguments": []
            })
        
        return prompts
    
    def _get_mime_type(self, language: str) -> str:
        """言語からMIMEタイプを取得"""
        mime_map = {
            'python': 'text/x-python',
            'javascript': 'text/javascript',
            'typescript': 'text/typescript',
            'java': 'text/x-java-source',
            'go': 'text/x-go',
            'rust': 'text/x-rust',
            'cpp': 'text/x-c++src',
            'c': 'text/x-csrc',
            'json': 'application/json',
            'yaml': 'text/yaml',
            'markdown': 'text/markdown'
        }
        return mime_map.get(language, 'text/plain')
    
    def generate_config(self) -> Dict[str, Any]:
        """完全なMCP設定を生成"""
        config = {
            "mcpServers": {
                f"{self.analysis.name}-repo": {
                    "command": "python",
                    "args": ["-m", "mcp_repo_server", str(self.analysis.root_path)],
                    "env": {
                        "REPO_PATH": str(self.analysis.root_path),
                        "REPO_NAME": self.analysis.name
                    }
                }
            }
        }
        
        # サーバー実装用メタデータ
        config["_metadata"] = {
            "repo_name": self.analysis.name,
            "repo_path": str(self.analysis.root_path),
            "project_type": self.analysis.project_type,
            "languages": self.analysis.languages,
            "important_files": self.analysis.important_files,
            "tools": self._generate_tools(),
            "resources": self._generate_resources(),
            "prompts": self._generate_prompts()
        }
        
        return config

class MCPServerGenerator:
    """MCPサーバー実装生成器"""
    
    def __init__(self, analysis: RepositoryAnalysis, config: Dict[str, Any]):
        self.analysis = analysis
        self.config = config
    
    def generate_server(self) -> str:
        """MCPサーバーのPythonコードを生成"""
        server_code = f'''#!/usr/bin/env python3
"""
Auto-generated MCP Server for {self.analysis.name}
Repository: {self.analysis.root_path}
"""

import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
import mcp.server.stdio
import mcp.types as types
from mcp.server import NotificationOptions, Server
from mcp.server.models import InitializationOptions

# Repository configuration
REPO_NAME = "{self.analysis.name}"
REPO_PATH = Path("{self.analysis.root_path}")
PROJECT_TYPE = "{self.analysis.project_type}"

server = Server(REPO_NAME)

@server.list_tools()
async def handle_list_tools() -> List[types.Tool]:
    """List available tools"""
    return [
        types.Tool(
            name="read_file",
            description=f"Read any file from the {{REPO_NAME}} repository",
            inputSchema={{
                "type": "object",
                "properties": {{
                    "path": {{
                        "type": "string",
                        "description": "File path relative to repository root"
                    }}
                }},
                "required": ["path"]
            }}
        ),
        types.Tool(
            name="search_files",
            description=f"Search for files in the {{REPO_NAME}} repository",
            inputSchema={{
                "type": "object",
                "properties": {{
                    "pattern": {{
                        "type": "string",
                        "description": "File name pattern"
                    }},
                    "language": {{
                        "type": "string",
                        "description": "Programming language filter"
                    }}
                }},
                "required": ["pattern"]
            }}
        ),
        types.Tool(
            name="search_code",
            description=f"Search for code patterns in {{REPO_NAME}}",
            inputSchema={{
                "type": "object",
                "properties": {{
                    "query": {{
                        "type": "string",
                        "description": "Code pattern to search"
                    }},
                    "file_type": {{
                        "type": "string",
                        "description": "File extension filter"
                    }}
                }},
                "required": ["query"]
            }}
        )
    ]

@server.call_tool()
async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> List[types.TextContent]:
    """Handle tool calls"""
    try:
        if name == "read_file":
            return await read_file(arguments["path"])
        elif name == "search_files":
            return await search_files(arguments["pattern"], arguments.get("language"))
        elif name == "search_code":
            return await search_code(arguments["query"], arguments.get("file_type"))
        else:
            raise ValueError(f"Unknown tool: {{name}}")
    except Exception as e:
        return [types.TextContent(type="text", text=f"Error: {{str(e)}}")]

async def read_file(path: str) -> List[types.TextContent]:
    """Read file content"""
    file_path = REPO_PATH / path
    
    if not file_path.exists():
        return [types.TextContent(type="text", text=f"File not found: {{path}}")]
    
    if not file_path.is_file():
        return [types.TextContent(type="text", text=f"Path is not a file: {{path}}")]
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return [types.TextContent(
            type="text",
            text=f"File: {{path}}\\n\\n{{content}}"
        )]
    except Exception as e:
        return [types.TextContent(type="text", text=f"Error reading file: {{str(e)}}")]

async def search_files(pattern: str, language: Optional[str] = None) -> List[types.TextContent]:
    """Search for files by pattern"""
    import fnmatch
    
    matches = []
    for file_path in REPO_PATH.rglob(pattern):
        if file_path.is_file():
            rel_path = file_path.relative_to(REPO_PATH)
            matches.append(str(rel_path))
    
    if language:
        # Filter by language (simplified)
        lang_extensions = {{
            'python': ['.py'],
            'javascript': ['.js', '.jsx'],
            'typescript': ['.ts', '.tsx'],
            'json': ['.json'],
            'yaml': ['.yml', '.yaml']
        }}
        
        if language in lang_extensions:
            extensions = lang_extensions[language]
            matches = [m for m in matches if any(m.endswith(ext) for ext in extensions)]
    
    result = f"Found {{len(matches)}} files matching pattern '{{pattern}}':"
    if language:
        result += f" (language: {{language}})"
    
    result += "\\n\\n" + "\\n".join(matches[:50])  # Limit to 50 results
    
    return [types.TextContent(type="text", text=result)]

async def search_code(query: str, file_type: Optional[str] = None) -> List[types.TextContent]:
    """Search for code patterns"""
    import re
    
    matches = []
    pattern = re.compile(re.escape(query), re.IGNORECASE)
    
    for file_path in REPO_PATH.rglob('*'):
        if file_path.is_file():
            if file_type and not file_path.name.endswith(file_type):
                continue
            
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()
                
                for i, line in enumerate(lines, 1):
                    if pattern.search(line):
                        rel_path = file_path.relative_to(REPO_PATH)
                        matches.append(f"{{rel_path}}:{{i}}: {{line.strip()}}")
                        
                        if len(matches) >= 100:  # Limit results
                            break
            except:
                continue
    
    result = f"Found {{len(matches)}} matches for '{{query}}':"
    if file_type:
        result += f" (file type: {{file_type}})"
    
    result += "\\n\\n" + "\\n".join(matches[:50])
    
    return [types.TextContent(type="text", text=result)]

@server.list_resources()
async def handle_list_resources() -> List[types.Resource]:
    """List available resources"""
    resources = []
    
    # Important files as resources
    important_files = {self.analysis.important_files}
    for file_path in important_files[:10]:
        resources.append(types.Resource(
            uri=f"file://{{file_path}}",
            name=f"{{REPO_NAME}}/{{file_path}}",
            description=f"Important file in {{REPO_NAME}}"
        ))
    
    # Repository overview
    resources.append(types.Resource(
        uri=f"repo://{{REPO_NAME}}/overview",
        name=f"{{REPO_NAME}} Overview",
        description=f"Repository overview and analysis"
    ))
    
    return resources

@server.read_resource()
async def handle_read_resource(uri: str) -> str:
    """Handle resource reading"""
    if uri.startswith("file://"):
        file_path = uri[7:]  # Remove file:// prefix
        return await read_file(file_path)
    elif uri.startswith("repo://"):
        # Return repository overview
        overview = {{
            "name": REPO_NAME,
            "path": str(REPO_PATH),
            "type": PROJECT_TYPE,
            "languages": {dict(self.analysis.languages)},
            "file_count": {len(self.analysis.files)},
            "important_files": {self.analysis.important_files}
        }}
        return json.dumps(overview, indent=2)
    else:
        raise ValueError(f"Unknown resource URI: {{uri}}")

async def main():
    """Main server entry point"""
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name=REPO_NAME,
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={{}}
                )
            )
        )

if __name__ == "__main__":
    asyncio.run(main())
'''
        
        return server_code

def main():
    """メイン実行インターフェース"""
    parser = argparse.ArgumentParser(description="Repository MCP Generator")
    parser.add_argument("repo_path", help="Path to repository")
    parser.add_argument("--output", "-o", help="Output directory", default="./mcp_output")
    parser.add_argument("--config-only", action="store_true", help="Generate config only")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        # 1. リポジトリ解析
        analyzer = RepositoryAnalyzer(args.repo_path)
        analysis = analyzer.analyze()
        
        logger.info(f"Analysis complete: {len(analysis.files)} files, {len(analysis.languages)} languages")
        
        # 2. MCP設定生成
        config_generator = MCPConfigGenerator(analysis)
        config = config_generator.generate_config()
        
        # 3. 出力ディレクトリ作成
        output_path = Path(args.output)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # 4. 設定ファイル出力
        config_file = output_path / f"{analysis.name}_mcp_config.json"
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        
        logger.info(f"MCP config generated: {config_file}")
        
        if not args.config_only:
            # 5. MCPサーバー生成
            server_generator = MCPServerGenerator(analysis, config)
            server_code = server_generator.generate_server()
            
            server_file = output_path / f"{analysis.name}_mcp_server.py"
            with open(server_file, 'w', encoding='utf-8') as f:
                f.write(server_code)
            
            # 実行権限付与
            server_file.chmod(0o755)
            
            logger.info(f"MCP server generated: {server_file}")
            
            # 6. 使い方ファイル生成
            usage_file = output_path / f"{analysis.name}_usage.md"
            usage_content = f"""# {analysis.name} MCP Server

## セットアップ

### 1. 依存関係インストール
```bash
pip install mcp
```

### 2. Claude Desktop設定に追加
設定ファイル `~/Library/Application Support/Claude/claude_desktop_config.json` に以下を追加:

```json
{{
  "mcpServers": {{
    "{analysis.name}-repo": {{
      "command": "python",
      "args": ["{server_file}"],
      "env": {{
        "REPO_PATH": "{analysis.root_path}",
        "REPO_NAME": "{analysis.name}"
      }}
    }}
  }}
}}
```

### 3. Claude Desktop再起動

## 利用可能な機能

### Tools
- `read_file`: ファイル読み取り
- `search_files`: ファイル検索
- `search_code`: コード検索

### Resources
- 重要ファイル ({len(analysis.important_files)} files)
- リポジトリ概要

## プロジェクト情報
- **タイプ**: {analysis.project_type}
- **言語**: {', '.join(analysis.languages.keys())}
- **ファイル数**: {len(analysis.files)}
- **重要ファイル**: {len(analysis.important_files)}
"""
            
            with open(usage_file, 'w', encoding='utf-8') as f:
                f.write(usage_content)
            
            logger.info(f"Usage guide generated: {usage_file}")
        
        # 7. 成果物サマリ
        print(f"""
🎉 Repository MCP Generator Complete!

📊 Analysis Results:
  Repository: {analysis.name}
  Project Type: {analysis.project_type}
  Languages: {', '.join(analysis.languages.keys())}
  Files: {len(analysis.files)}
  Important Files: {len(analysis.important_files)}

📁 Generated Files:
  Config: {config_file}
  {'Server: ' + str(server_file) if not args.config_only else ''}
  {'Usage: ' + str(usage_file) if not args.config_only else ''}

🚀 Next Steps:
  1. Install dependencies: pip install mcp
  2. Add config to Claude Desktop
  3. Restart Claude Desktop
  4. Start using the MCP server!
""")
        
        # 完了状態記録
        with open("/home/hi_ry/cc-organization/tmp/worker1_done.txt", "w") as f:
            f.write(f"Repository MCP Generator implementation completed at {os.popen('date').read().strip()}")
        
    except Exception as e:
        logger.error(f"Error: {e}")
        with open("/home/hi_ry/cc-organization/tmp/worker1_error.txt", "w") as f:
            f.write(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()