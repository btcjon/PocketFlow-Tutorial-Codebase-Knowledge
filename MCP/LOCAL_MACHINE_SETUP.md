# Local Machine MCP Setup Guide

> **For Jon's Local Machine** - Super simplified! Just copy configs and use.

## Quick Setup (2 steps)

Since everything is already installed and configured on your machine, just add the MCP server to your clients.

### 1. Claude Desktop Setup

Copy the pre-made config:

```bash
cp MCP/claude_desktop_config.json ~/Library/Application\ Support/Claude/claude_desktop_config.json
```

Or manually add this to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "tutorial-codebase-knowledge": {
      "command": "python",
      "args": ["mcp_server_simple.py"],
      "cwd": "/Users/jonbennett/Dropbox/Coding-Main/Tutorial-Codebase-Knowledge/MCP",
      "env": {
        "PYTHONPATH": "/Users/jonbennett/Dropbox/Coding-Main/Tutorial-Codebase-Knowledge"
      }
    }
  }
}
```

### 2. Claude Code Setup

Copy the pre-made config:

```bash
mkdir -p .claude
cp MCP/claude_code_config.json .claude/mcp_config.json
```

Or manually create `.claude/mcp_config.json`:

```json
{
  "mcpServers": {
    "tutorial-codebase-knowledge": {
      "command": "python",
      "args": ["MCP/mcp_server_simple.py"],
      "cwd": "/Users/jonbennett/Dropbox/Coding-Main/Tutorial-Codebase-Knowledge",
      "env": {
        "PYTHONPATH": "/Users/jonbennett/Dropbox/Coding-Main/Tutorial-Codebase-Knowledge"
      }
    }
  }
}
```

## Usage - Super Simple!

### Claude Desktop
Restart Claude Desktop, then just ask naturally:

```
Generate a tutorial for https://github.com/fastapi/fastapi
Create documentation for /Users/jonbennett/Dropbox/Coding-Main/some-project
Make a tutorial in Spanish for https://github.com/microsoft/vscode
```

### Claude Code  
The MCP server is automatically available. Just ask:

```
Generate a tutorial for this codebase
Analyze this project and create beginner documentation  
Create a tutorial for the current directory
```

**That's it!** No need to specify API keys, models, or providers - everything is handled automatically.

## Output Locations

**All tutorials are saved to:**
```
/Users/jonbennett/Dropbox/Coding-Main/Tutorial-Codebase-Knowledge/docs/{project_name}/
```

**Important:** The tutorials are ALWAYS saved in this central location, not in your current project. This keeps all generated documentation organized in one place.

**Example:**
- Analyzing `https://github.com/fastapi/fastapi` creates:
  ```
  /Users/jonbennett/Dropbox/Coding-Main/Tutorial-Codebase-Knowledge/docs/fastapi/
  ├── index.md
  ├── 01_concept.md
  ├── 02_concept.md
  └── ...
  ```

**To access your tutorials:**
1. Navigate to the central docs folder
2. Or create a symlink in your project: `ln -s /Users/jonbennett/Dropbox/Coding-Main/Tutorial-Codebase-Knowledge/docs/{project_name} ./tutorial`

## Advanced Configuration

## Behind the Scenes

**Model Used**: `anthropic/claude-3-opus:beta` via OpenRouter (high quality, configured in your environment)

**File Patterns**: Automatically includes common code files (`.py`, `.js`, `.ts`, etc.) and excludes test/build directories

**Output Directory**: Always saves to `/Users/jonbennett/Dropbox/Coding-Main/Tutorial-Codebase-Knowledge/docs/{project_name}/`

## Troubleshooting

**"MCP server not found":** Restart Claude Desktop/Code after config changes

**"No response":** Tutorial generation takes 5-10 minutes - be patient!

**"Permission denied":** Check that the paths in the config are correct

## What You Get

```
docs/{project_name}/
├── index.md              # Overview with project summary and diagram
├── 01_concept.md          # First key concept  
├── 02_concept.md          # Second key concept
├── 03_concept.md          # Third key concept
└── ...                    # Up to 10 concepts total
```

Each tutorial includes:
- ✅ Beginner-friendly explanations
- ✅ Code examples with context  
- ✅ Mermaid diagrams showing relationships
- ✅ Cross-references between concepts