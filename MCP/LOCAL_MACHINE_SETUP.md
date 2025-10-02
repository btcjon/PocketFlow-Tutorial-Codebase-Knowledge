# Local Machine MCP Setup Guide

> **For Jon's Local Machine** - Super simplified! NPM-based MCP server now working perfectly.

## Quick Setup (1 step)

The MCP server is now packaged as an NPM module for better reliability and easier maintenance.

### Claude Desktop Setup

The server is already configured in your Claude Desktop at:
`~/Library/Application Support/Claude/claude_desktop_config.json`

Current working configuration:
```json
{
  "mcpServers": {
    "tutorial-codebase-knowledge": {
      "command": "node",
      "args": ["/Users/jonbennett/Dropbox/Coding-Main/Tutorial-Codebase-Knowledge/npm-mcp-server/build/index.js"],
      "env": {
        "LLM_PROVIDER": "openrouter",
        "OPENROUTER_API_KEY": "your-api-key"
      },
      "description": "Generate comprehensive tutorials from codebases"
    }
  }
}
```

### Alternative: NPX Setup (for published version)

When the package is published to NPM, you can use:
```json
{
  "mcpServers": {
    "tutorial-codebase-knowledge": {
      "command": "npx",
      "args": ["@btcjon/tutorial-codebase-knowledge-mcp"],
      "env": {
        "LLM_PROVIDER": "openrouter",
        "OPENROUTER_API_KEY": "your-api-key"
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

**Output Directory**: Always saves to `/Users/jonbennett/Dropbox/Coding-Main/Tutorial-Codebase-Knowledge/docs/{project_name}/` as a single `{project_name}_tutorial.md` file

## Troubleshooting

**"MCP server not found":** Restart Claude Desktop/Code after config changes

**"No response":** Tutorial generation takes 5-10 minutes - be patient!

**"Permission denied":** Check that the paths in the config are correct

## What You Get

```
docs/{project_name}/
└── {project_name}_tutorial.md   # Complete tutorial in one file
```

Each tutorial includes:
- ✅ Project summary with mermaid relationship diagram
- ✅ Table of contents with anchor links
- ✅ Beginner-friendly explanations for all key concepts
- ✅ Code examples with context  
- ✅ Implementation details and analogies
- ✅ Cross-references between concepts
- ✅ Single structured markdown file (no more multiple files!)