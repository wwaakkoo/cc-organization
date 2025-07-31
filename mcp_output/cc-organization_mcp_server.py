#!/usr/bin/env python3
"""
Auto-generated MCP Server for cc-organization
Repository: /home/hi_ry/cc-organization
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
REPO_NAME = "cc-organization"
REPO_PATH = Path("/home/hi_ry/cc-organization")
PROJECT_TYPE = "general"

server = Server(REPO_NAME)

@server.list_tools()
async def handle_list_tools() -> List[types.Tool]:
    """List available tools"""
    return [
        types.Tool(
            name="read_file",
            description=f"Read any file from the {REPO_NAME} repository",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "File path relative to repository root"
                    }
                },
                "required": ["path"]
            }
        ),
        types.Tool(
            name="search_files",
            description=f"Search for files in the {REPO_NAME} repository",
            inputSchema={
                "type": "object",
                "properties": {
                    "pattern": {
                        "type": "string",
                        "description": "File name pattern"
                    },
                    "language": {
                        "type": "string",
                        "description": "Programming language filter"
                    }
                },
                "required": ["pattern"]
            }
        ),
        types.Tool(
            name="search_code",
            description=f"Search for code patterns in {REPO_NAME}",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Code pattern to search"
                    },
                    "file_type": {
                        "type": "string",
                        "description": "File extension filter"
                    }
                },
                "required": ["query"]
            }
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
            raise ValueError(f"Unknown tool: {name}")
    except Exception as e:
        return [types.TextContent(type="text", text=f"Error: {str(e)}")]

async def read_file(path: str) -> List[types.TextContent]:
    """Read file content"""
    file_path = REPO_PATH / path
    
    if not file_path.exists():
        return [types.TextContent(type="text", text=f"File not found: {path}")]
    
    if not file_path.is_file():
        return [types.TextContent(type="text", text=f"Path is not a file: {path}")]
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return [types.TextContent(
            type="text",
            text=f"File: {path}\n\n{content}"
        )]
    except Exception as e:
        return [types.TextContent(type="text", text=f"Error reading file: {str(e)}")]

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
        lang_extensions = {
            'python': ['.py'],
            'javascript': ['.js', '.jsx'],
            'typescript': ['.ts', '.tsx'],
            'json': ['.json'],
            'yaml': ['.yml', '.yaml']
        }
        
        if language in lang_extensions:
            extensions = lang_extensions[language]
            matches = [m for m in matches if any(m.endswith(ext) for ext in extensions)]
    
    result = f"Found {len(matches)} files matching pattern '{pattern}':"
    if language:
        result += f" (language: {language})"
    
    result += "\n\n" + "\n".join(matches[:50])  # Limit to 50 results
    
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
                        matches.append(f"{rel_path}:{i}: {line.strip()}")
                        
                        if len(matches) >= 100:  # Limit results
                            break
            except:
                continue
    
    result = f"Found {len(matches)} matches for '{query}':"
    if file_type:
        result += f" (file type: {file_type})"
    
    result += "\n\n" + "\n".join(matches[:50])
    
    return [types.TextContent(type="text", text=result)]

@server.list_resources()
async def handle_list_resources() -> List[types.Resource]:
    """List available resources"""
    resources = []
    
    # Important files as resources
    important_files = ['mcp_output/cc-organization_mcp_server.py', '.tmux.conf', 'README-en.md', 'ARCHITECTURE.md', 'README.md', 'CLAUDE.md', 'setup.sh', 'LICENSE', 'repo_mcp_generator.py', 'MCP_USAGE_GUIDE.md', 'run_mcp_generator.sh', 'agent-send.sh', 'mcp_output/cc-organization_usage.md', 'scripts/monitor.sh', 'scripts/quick-setup.sh', 'instructions/worker.md', 'instructions/boss.md', 'instructions/president.md']
    for file_path in important_files[:10]:
        resources.append(types.Resource(
            uri=f"file://{file_path}",
            name=f"{REPO_NAME}/{file_path}",
            description=f"Important file in {REPO_NAME}"
        ))
    
    # Repository overview
    resources.append(types.Resource(
        uri=f"repo://{REPO_NAME}/overview",
        name=f"{REPO_NAME} Overview",
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
        overview = {
            "name": REPO_NAME,
            "path": str(REPO_PATH),
            "type": PROJECT_TYPE,
            "languages": {'markdown': 9, 'shell': 5, 'text': 1, 'python': 2, 'config': 1},
            "file_count": 18,
            "important_files": ['mcp_output/cc-organization_mcp_server.py', '.tmux.conf', 'README-en.md', 'ARCHITECTURE.md', 'README.md', 'CLAUDE.md', 'setup.sh', 'LICENSE', 'repo_mcp_generator.py', 'MCP_USAGE_GUIDE.md', 'run_mcp_generator.sh', 'agent-send.sh', 'mcp_output/cc-organization_usage.md', 'scripts/monitor.sh', 'scripts/quick-setup.sh', 'instructions/worker.md', 'instructions/boss.md', 'instructions/president.md']
        }
        return json.dumps(overview, indent=2)
    else:
        raise ValueError(f"Unknown resource URI: {uri}")

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
                    experimental_capabilities={}
                )
            )
        )

if __name__ == "__main__":
    asyncio.run(main())
