#!/bin/bash

# MCP Setup Script for Local Machine
# Sets up both Claude Desktop and Claude Code MCP configurations

echo "🚀 Setting up MCP for Tutorial Codebase Knowledge Generator..."
echo

# Get the project directory
PROJECT_DIR="/Users/jonbennett/Dropbox/Coding-Main/Tutorial-Codebase-Knowledge"
CLAUDE_DESKTOP_CONFIG="$HOME/Library/Application Support/Claude/claude_desktop_config.json"
CLAUDE_CODE_CONFIG="$PROJECT_DIR/.claude/mcp_config.json"

echo "📁 Project directory: $PROJECT_DIR"
echo

# Check if we're in the right directory
if [ ! -f "$PROJECT_DIR/MCP/mcp_server_simple.py" ]; then
    echo "❌ Error: Cannot find MCP server files. Please run this from the project directory."
    exit 1
fi

# Function to prompt for API keys
get_api_keys() {
    echo "🔑 API Key Configuration"
    echo "Enter your API keys (press Enter to skip any you don't have):"
    echo
    
    read -p "Gemini API Key: " GEMINI_KEY
    read -p "OpenAI API Key: " OPENAI_KEY
    read -p "Anthropic API Key: " ANTHROPIC_KEY
    read -p "OpenRouter API Key: " OPENROUTER_KEY
    
    echo
    echo "🎯 Choose default LLM provider:"
    echo "1) Gemini (recommended - fast and free)"
    echo "2) OpenAI (GPT-4)"
    echo "3) Anthropic (Claude)"
    echo "4) OpenRouter (multiple models)"
    read -p "Choice (1-4): " PROVIDER_CHOICE
    
    case $PROVIDER_CHOICE in
        1) LLM_PROVIDER="gemini" ;;
        2) LLM_PROVIDER="openai" ;;
        3) LLM_PROVIDER="anthropic" ;;
        4) LLM_PROVIDER="openrouter" ;;
        *) LLM_PROVIDER="gemini" ;;
    esac
}

# Create config with API keys
create_config() {
    local config_file="$1"
    local args_path="$2"
    local cwd_path="$3"
    
    cat > "$config_file" << EOF
{
  "mcpServers": {
    "tutorial-codebase-knowledge": {
      "command": "python",
      "args": ["$args_path"],
      "cwd": "$cwd_path",
      "env": {
        "PYTHONPATH": "$PROJECT_DIR",
        "LLM_PROVIDER": "$LLM_PROVIDER"$([ -n "$GEMINI_KEY" ] && echo ",
        \"GEMINI_API_KEY\": \"$GEMINI_KEY\"")$([ -n "$OPENAI_KEY" ] && echo ",
        \"OPENAI_API_KEY\": \"$OPENAI_KEY\"")$([ -n "$ANTHROPIC_KEY" ] && echo ",
        \"ANTHROPIC_API_KEY\": \"$ANTHROPIC_KEY\"")$([ -n "$OPENROUTER_KEY" ] && echo ",
        \"OPENROUTER_API_KEY\": \"$OPENROUTER_KEY\"")
      }
    }
  }
}
EOF
}

# Get API keys from user
get_api_keys

# Setup Claude Desktop
echo "⚙️  Setting up Claude Desktop..."
mkdir -p "$(dirname "$CLAUDE_DESKTOP_CONFIG")"
create_config "$CLAUDE_DESKTOP_CONFIG" "mcp_server_simple.py" "$PROJECT_DIR/MCP"
echo "✅ Claude Desktop config created: $CLAUDE_DESKTOP_CONFIG"

# Setup Claude Code
echo "⚙️  Setting up Claude Code..."
mkdir -p "$PROJECT_DIR/.claude"
create_config "$CLAUDE_CODE_CONFIG" "MCP/mcp_server_simple.py" "$PROJECT_DIR"
echo "✅ Claude Code config created: $CLAUDE_CODE_CONFIG"

echo
echo "🎉 Setup complete!"
echo
echo "📋 Next steps:"
echo "1. Restart Claude Desktop"
echo "2. Try: 'Generate a tutorial for https://github.com/fastapi/fastapi'"
echo "3. In Claude Code, try: 'Generate a tutorial for this project'"
echo
echo "📖 Tutorials will be saved to: $PROJECT_DIR/docs/"
echo
echo "💡 Need help? Check: $PROJECT_DIR/MCP/LOCAL_MACHINE_SETUP.md"