# Our Customizations to Tutorial-Codebase-Knowledge

This file tracks all customizations made to the original Tutorial-Codebase-Knowledge repository.

## Added Features

### 1. NPM-Based MCP (Model Context Protocol) Server
- **Location**: `npm-mcp-server/` directory
- **Files Added**:
  - `src/index.ts` - TypeScript MCP server implementation
  - `package.json` - NPM package configuration
  - `tsconfig.json` - TypeScript configuration
  - `README.md` - NPM package documentation
  - `LICENSE` - MIT license
- **Purpose**: Reliable NPM-based MCP server that wraps Python functionality for Claude Desktop integration

### 2. Cloudflare Worker Implementation
- **Location**: `worker/` directory
- **Purpose**: Alternative serverless deployment option using Cloudflare Workers
- **Features**: Remote MCP server accessible via URL

### 3. MoveToDocs Workflow Node
- **File**: `nodes.py` (lines 1032-1070)
- **Purpose**: Automatically moves generated tutorials from `output/` to `docs/` folder
- **Integration**: Added to workflow in `flow.py`

### 4. MergeToSingleFile Workflow Node
- **File**: `nodes.py` (lines 917-1030)
- **Purpose**: Combines index.md and all chapter files into a single `{project_name}_tutorial.md` file
- **Features**:
  - Creates table of contents with anchor links
  - Maintains project summary and mermaid diagram
  - Merges all chapters in proper order
  - Cleans up individual files after merging
- **Integration**: Added between CombineTutorial and MoveToDocs in workflow

### 5. Documentation Organization
- **Added Folders**: Extensive `docs/` directory with 25+ generated tutorial examples

## Modified Files

### 1. `flow.py`
- **Change**: Added `MoveToDocs` import and node to workflow
- **Lines**: Import on line 10, node instantiation on line 23, connection on line 31

### 2. `nodes.py`
- **Change**: Added `MoveToDocs` class at end of file
- **Purpose**: Implements the docs folder organization feature

### 3. `.env` (if exists)
- **Changes**: Custom LLM provider configurations
- **Default Provider**: Set to use OpenRouter or other providers

## Configuration Customizations

### 1. Default LLM Provider
- Changed from Gemini to OpenRouter in some configurations
- Environment variable: `LLM_PROVIDER`

### 2. File Patterns
- May have adjusted include/exclude patterns for specific use cases

### 3. Output Directory Structure
- Modified to use `docs/` as final destination instead of `output/`

## How to Preserve These During Updates

1. **Critical Files to Watch**:
   - `npm-mcp-server/` directory (completely custom NPM implementation)
   - `worker/` directory (completely custom Cloudflare Worker)
   - `nodes.py` (contains MoveToDocs and MergeToSingleFile classes)
   - `flow.py` (modified workflow)

2. **Merge Strategy**:
   - The `npm-mcp-server/` and `worker/` directories are entirely our additions
   - For `nodes.py` and `flow.py`, carefully review changes during merges
   - Use `git diff` to compare before merging

3. **Testing After Updates**:
   - Test NPM MCP server: `cd npm-mcp-server && npm run build && node build/index.js`
   - Test CLI: `python main.py --repo https://github.com/example/repo`
   - Test MoveToDocs: Run tutorial generation and verify it moves to `docs/`
   - Test MergeToSingleFile: Verify single `{project}_tutorial.md` file is created
   - Test with Claude Desktop if configured

## Potential Conflict Areas

1. **nodes.py**: If upstream adds new nodes or modifies the class structure
2. **flow.py**: If upstream changes the workflow sequence
3. **main.py**: If upstream adds new command-line arguments that conflict with ours

## Rollback Plan

If an upstream update breaks our customizations:
```bash
# Create a branch with our version
git checkout -b our-version-backup

# Reset to last known good commit
git reset --hard <last-good-commit>

# Or selectively revert problematic commits
git revert <problematic-commit>
```