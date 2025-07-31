#!/bin/bash
# Repository MCP Generator - Quick Run Script

set -e

REPO_PATH=${1:-.}
OUTPUT_DIR=${2:-./mcp_output}

echo "🚀 Repository MCP Generator"
echo "Repository: $REPO_PATH"
echo "Output: $OUTPUT_DIR"
echo ""

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: python3 is not installed"
    exit 1
fi

# Run the generator
echo "📊 Analyzing repository and generating MCP server..."
python3 repo_mcp_generator.py "$REPO_PATH" --output "$OUTPUT_DIR" --verbose

echo ""
echo "✅ MCP Generation Complete!"
echo ""
echo "📁 Generated files in $OUTPUT_DIR/:"
ls -la "$OUTPUT_DIR/"

echo ""
echo "🔧 Next steps:"
echo "1. Install MCP: pip install mcp"
echo "2. Add the config to Claude Desktop settings"
echo "3. Restart Claude Desktop"
echo "4. Use the MCP server!"