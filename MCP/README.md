# MCP Server for Tutorial Codebase Knowledge

> **What is MCP?** MCP (Model Context Protocol) lets you use this tutorial generator directly from Claude Desktop, making it as easy as asking "Generate a tutorial for this GitHub repo."

## Quick Setup (3 steps)

### 1. Install Dependencies
```bash
# Make sure you're in the main project directory
cd /path/to/Tutorial-Codebase-Knowledge
pip install -r requirements.txt
```

### 2. Add to Claude Desktop
Copy the contents of `mcp_config.json` and add it to your Claude Desktop configuration:

**On Mac:** `~/Library/Application Support/Claude/claude_desktop_config.json`
**On Windows:** `%APPDATA%/Claude/claude_desktop_config.json`

Your config should look like this:
```json
{
  "mcpServers": {
    "tutorial-codebase-knowledge": {
      "command": "python",
      "args": ["mcp_server_simple.py"],
      "cwd": "/path/to/Tutorial-Codebase-Knowledge/MCP",
      "env": {
        "PYTHONPATH": "/path/to/Tutorial-Codebase-Knowledge"
      }
    }
  }
}
```

**Important:** Update the `"cwd"` path to match your actual project location!

### 3. Set up API Keys
Add your preferred LLM API key to your environment:
```bash
# Choose one:
export GEMINI_API_KEY="your-key-here"
export OPENAI_API_KEY="your-key-here"  
export ANTHROPIC_API_KEY="your-key-here"
export OPENROUTER_API_KEY="your-key-here"
```

## Usage

Restart Claude Desktop, then simply ask:

- "Generate a tutorial for https://github.com/user/repo"
- "Create documentation for my project at /path/to/local/project"
- "Make a tutorial for https://github.com/fastapi/fastapi"

The tutorial will be automatically saved to your `docs/` folder with:
- `index.md` - Main overview with project summary
- `01_concept.md`, `02_concept.md`, etc. - Individual chapters
- Mermaid diagrams showing relationships

## What Gets Generated

✅ **Beginner-friendly tutorials** explaining your codebase  
✅ **Multiple chapters** breaking down key concepts  
✅ **Code examples** with explanations  
✅ **Visual diagrams** showing how components relate  
✅ **Saved to docs/** folder for easy access  

## Troubleshooting

**"Tool not found":** Make sure you restarted Claude Desktop after adding the config.

**"Permission denied":** Check that the `cwd` path in your config points to the correct MCP folder location.

**"API error":** Verify your API key is set correctly in your environment variables.

**"No output":** The tutorial generation takes 5-10 minutes. Be patient!

## Advanced Options

You can specify additional options in Claude:

- "Generate a tutorial in Spanish for [repo]"
- "Use OpenAI to generate a tutorial for [repo]"
- "Generate a tutorial and save it to ~/Desktop/my-docs"

## Files in this folder

- `mcp_server_simple.py` - Main MCP server (recommended)
- `mcp_server.py` - Full-featured MCP server  
- `mcp_config.json` - Configuration template
- `claude-desktop-config-snippet.json` - Alternative config format