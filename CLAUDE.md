# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Tutorial-Codebase-Knowledge is an AI-powered tool that transforms complex codebases into beginner-friendly tutorials. It uses PocketFlow to orchestrate a workflow that analyzes code repositories and generates comprehensive tutorials explaining code structure and key concepts.

## Common Development Commands

```bash
# Run the main application to analyze a GitHub repository
python main.py --repo <github-url>

# Run the main application to analyze a local directory
python main.py --dir <path>

# Test LLM provider configurations
python test_llm_providers.py

# List available models for all providers
python list_models.py
```

## High-Level Architecture

The application follows a sequential workflow pattern implemented using PocketFlow:

1. **Entry Points**:
   - `main.py` - CLI interface that accepts GitHub URLs or local directories
   - `flow.py` - Defines the PocketFlow workflow with 7 sequential nodes

2. **Workflow Nodes** (defined in `nodes.py`):
   - `FetchRepo` - Downloads/reads repository files
   - `IdentifyAbstractions` - Extracts key concepts and patterns
   - `AnalyzeRelationships` - Maps connections between abstractions
   - `OrderChapters` - Determines optimal tutorial structure
   - `WriteChapters` - Generates tutorial content for each abstraction
   - `CombineTutorial` - Assembles final tutorial document
   - `MoveToDocs` - Moves generated tutorial from output folder to docs folder

3. **Key Components**:
   - `utils/call_llm.py` - Unified interface for multiple LLM providers (Gemini, OpenAI, Anthropic, OpenRouter)
   - `utils/crawl_github_files.py` - GitHub repository file fetching
   - `utils/crawl_local_files.py` - Local directory file reading
   - Caching system in `logs/` for efficient re-processing
   - Output tutorials saved to `output/` directory

4. **Configuration**:
   - LLM providers configured via environment variables in `.env`
   - Default models and settings specified in utility modules
   - File filtering and size limits configurable in crawl utilities

## Key Design Patterns

- **Workflow Pattern**: Sequential processing with each node building on previous results
- **Provider Abstraction**: Single interface supporting multiple LLM providers
- **Caching Strategy**: Results cached by repository URL/path to avoid redundant processing
- **Error Handling**: Graceful fallbacks when providers are unavailable

## MCP Server Usage

This tool is now available as an MCP (Model Context Protocol) server, allowing it to be used from Claude Desktop or other MCP-compatible tools.

### Local MCP Server (Recommended)

The local MCP server saves tutorials directly to `./mydocs` in your current working directory, making it perfect for documenting projects you're actively working on.

#### Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. The server is already configured in Claude Desktop. Just restart Claude Desktop to use it.

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
→ Saves to: ~/Dropbox/tutorial-docs/tutorial_langchain_20250525_103045.md

"Generate a tutorial for my local project at /Users/me/myproject"
→ Saves to: /Users/me/myproject/mydocs/tutorial_myproject_20250525_103045.md
```

**With custom output:**
```
"Generate a tutorial for https://github.com/example/repo and save it to ~/Desktop/docs"
→ Saves to: ~/Desktop/docs/tutorial_repo_20250525_103045.md

"List all tutorials in ~/Dropbox/tutorial-docs"
→ Shows all tutorials in the default location
```

**Pro tip:** When analyzing a local project, the tutorial is saved directly in that project's `mydocs` folder, making it easy to commit the documentation with your code!