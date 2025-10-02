# CLAUDE.md

## Project Overview

Tutorial-Codebase-Knowledge is an AI-powered tool that transforms complex codebases into beginner-friendly tutorials. It uses PocketFlow to orchestrate a workflow that analyzes code repositories and generates comprehensive tutorials explaining code structure and key concepts.

## Common Development Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run the main application to analyze a GitHub repository
python main.py --repo <github-url>

# Run the main application to analyze a local directory  
python main.py --dir <path>

# Generate tutorial with specific options
python main.py --repo <url> --language "Chinese" --max-abstractions 8 --llm-provider openrouter

# Test LLM provider configurations
python test_llm_providers.py

# List available models for all providers
python list_models.py

# Test direct LLM calls
python utils/call_llm.py

# Build MCP server
cd npm-mcp-server && npm run build

# Development mode for MCP server
cd npm-mcp-server && npm run dev
```

## High-Level Architecture

The application follows a sequential workflow pattern implemented using PocketFlow:

### Core Workflow (8 Sequential Nodes)

1. **FetchRepo** (`nodes.py:31`) - Downloads/reads repository files using `utils/crawl_github_files.py` or `utils/crawl_local_files.py`
2. **IdentifyAbstractions** (`nodes.py:93`) - Extracts 5-10 core concepts and patterns using LLM analysis
3. **AnalyzeRelationships** (`nodes.py:267`) - Maps connections between abstractions and generates project summary
4. **OrderChapters** (`nodes.py:444`) - Determines optimal tutorial structure based on dependencies
5. **WriteChapters** (`nodes.py:571`) - Generates detailed tutorial content for each abstraction (BatchNode)
6. **CombineTutorial** (`nodes.py:787`) - Assembles final tutorial with index and Mermaid diagrams
7. **MergeToSingleFile** (`nodes.py:917`) - Combines all chapters into single tutorial file
8. **MoveToDocs** (`nodes.py:1032`) - Moves generated tutorial from output to docs folder

### Key Components

- **Entry Points**:
  - `main.py` - CLI interface with comprehensive argument parsing
  - `flow.py` - PocketFlow workflow definition with node connections

- **LLM Integration**:
  - `utils/call_llm.py` - Unified interface for multiple providers (Gemini, OpenAI, Anthropic, OpenRouter)
  - Supports caching, logging, and provider fallbacks
  - Environment-based provider selection via `LLM_PROVIDER`

- **File Processing**:
  - Smart file filtering with include/exclude patterns
  - Size limits and content truncation for large files
  - Support for multiple programming languages

- **Output Management**:
  - Multi-format output (separate chapters + combined tutorial)
  - Mermaid diagram generation for relationships
  - Multi-language tutorial support

### MCP Server Architecture

- **NPM Package**: `npm-mcp-server/` - TypeScript implementation wrapping Python engine
- **Tools**: generate_tutorial, list_generated_tutorials, get_tutorial_content
- **Smart Defaults**: Different save locations for GitHub repos vs local directories

## Configuration System

### Environment Variables
- `LLM_PROVIDER` - Provider selection (gemini, openai, anthropic, openrouter)
- `GEMINI_API_KEY` / `GOOGLE_API_KEY` - For Gemini
- `OPENAI_API_KEY` - For OpenAI  
- `ANTHROPIC_API_KEY` - For Claude
- `OPENROUTER_API_KEY` - For OpenRouter
- `GITHUB_TOKEN` - For private repos and rate limiting

### File Patterns (configurable via CLI)
- **Default Include**: `*.py`, `*.js`, `*.jsx`, `*.ts`, `*.tsx`, `*.go`, `*.java`, `*.c`, `*.cpp`, `*.h`, `*.md`, `*.rst`, `*Dockerfile`, `*Makefile`, `*.yaml`, `*.yml`
- **Default Exclude**: `*test*`, `*docs/*`, `*venv/*`, `*node_modules/*`, `*build/*`, `*dist/*`, `.git/*`

## Key Design Patterns

- **Sequential Workflow**: Each node builds on previous results with proper data validation
- **Provider Abstraction**: Single `call_llm()` interface supporting multiple LLM providers
- **Batch Processing**: `WriteChapters` uses BatchNode for parallel chapter generation
- **Caching Strategy**: LLM responses cached with prompt-based keys in `llm_cache.json`
- **Error Handling**: Node-level retries with exponential backoff
- **Content Truncation**: Smart truncation preserving beginning/end of large files

## Testing and Debugging

- No formal test framework - relies on manual testing with real repositories
- LLM call logging in `logs/llm_calls_YYYYMMDD.log`
- Cache inspection via `llm_cache.json`
- Verbose output during workflow execution for debugging

## Development Tips

- Use `--no-cache` flag when testing LLM prompt changes
- Adjust `--max-abstractions` for different complexity codebases  
- Test with `test_llm_providers.py` before running full workflow
- Monitor logs for LLM call patterns and errors
- MCP server requires rebuilding (`npm run build`) after TypeScript changes

## Context Length Issues

If you encounter "maximum context length" errors:

1. **Automatic Handling**: The system now automatically:
   - Counts tokens and truncates prompts before sending to LLM
   - Uses OpenRouter's "middle-out" transform for context compression
   - Applies more aggressive file content truncation for large codebases

2. **Manual Adjustments**:
   - Reduce `--max-abstractions` (try 5-6 instead of 10)
   - Use more restrictive `--include` patterns
   - Add more `--exclude` patterns to filter out large files
   - Increase `--max-size` limit to exclude very large files

3. **Model Selection**: Some models have larger context windows:
   - Claude models: ~200K tokens
   - GPT-4 Turbo: ~128K tokens  
   - Gemini 2.5 Flash: ~1M tokens
   - Set via `OPENROUTER_MODEL` environment variable

## MCP Server Usage

This tool is available as an MCP (Model Context Protocol) server built with TypeScript/Node.js for maximum reliability and compatibility with Claude Desktop.

### NPM-Based MCP Server (Current Implementation)

The MCP server is now packaged as a Node.js application that wraps the Python tutorial generation engine. This provides better reliability and follows the same pattern as official MCP servers.

#### Current Setup

The server is configured in Claude Desktop at:
`~/Library/Application Support/Claude/claude_desktop_config.json`

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

#### Package Structure

- `npm-mcp-server/` - TypeScript MCP server implementation
- `npm-mcp-server/src/index.ts` - Main MCP server with tool definitions
- `npm-mcp-server/build/` - Compiled JavaScript output

#### Key Features

- **Smart output directory selection**:
  - GitHub repos: Saves to `~/Dropbox/tutorial-docs/`
  - Local directories: Saves to `<analyzed_dir>/mydocs/`
  - Custom location: Specify with `output_dir` parameter
- **Version control friendly**: Docs can be committed alongside your code
- **Works offline**: No internet required after setup
- **Privacy**: Your code never leaves your machine

#### Default Save Locations

Since Claude Desktop doesn't have a "current project" context, the tool uses smart defaults:

1. **For GitHub repositories**: `~/Dropbox/tutorial-docs/tutorial_<repo>_<timestamp>.md`
2. **For local directories**: `<directory>/mydocs/tutorial_<dirname>_<timestamp>.md`
3. **Custom location**: Use the `output_dir` parameter (e.g., "~/Desktop/my-docs")

### Remote MCP Server (Cloudflare Worker)

A remote version is also available at `https://tutorial-codebase-knowledge.thesystem.workers.dev` that stores tutorials in Cloudflare KV storage. This is disabled by default but can be enabled in the config.

### Available MCP Tools

1. **generate_tutorial** - Generate a tutorial from any codebase
   - `source`: GitHub URL or local directory path
   - `source_type`: "repo" or "dir"
   - `output_dir`: Where to save (default: ./mydocs)
   - `language`: Tutorial language (default: English)
   - `llm_provider`: gemini, openai, anthropic, or openrouter
   - `llm_model`: Specific model to use (optional)

2. **list_generated_tutorials** - List all tutorials in a directory
   - `directory`: Directory to search (default: ./mydocs)

3. **get_tutorial_content** - Read a generated tutorial
   - `tutorial_path`: Path to the tutorial file

### Example Usage in Claude

When the MCP server is configured, you can use it like this:

**Basic usage:**
```
"Generate a tutorial for https://github.com/langchain-ai/langchain"
� Saves to: ~/Dropbox/tutorial-docs/tutorial_langchain_20250525_103045.md

"Generate a tutorial for my local project at /Users/me/myproject"
� Saves to: /Users/me/myproject/mydocs/tutorial_myproject_20250525_103045.md
```

**With custom output:**
```
"Generate a tutorial for https://github.com/example/repo and save it to ~/Desktop/docs"
� Saves to: ~/Desktop/docs/tutorial_repo_20250525_103045.md

"List all tutorials in ~/Dropbox/tutorial-docs"
� Shows all tutorials in the default location
```

**Pro tip:** When analyzing a local project, the tutorial is saved directly in that project's `mydocs` folder, making it easy to commit the documentation with your code!