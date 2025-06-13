# Our Customizations to Tutorial-Codebase-Knowledge

This file tracks all customizations made to the original Tutorial-Codebase-Knowledge repository.

## Added Features

### 1. MCP (Model Context Protocol) Server Implementation
- **Location**: `MCP/` directory
- **Files Added**:
  - `mcp_server.py` - Original simple implementation
  - `mcp_server_simple.py` - Simplified version
  - `mcp_server_robust.py` - Production-ready version with error handling
  - `setup_mcp.sh` - Setup script for MCP configuration
  - `claude_desktop_config.json` - Claude Desktop configuration
  - `claude_code_config.json` - Claude Code configuration
  - `LOCAL_MACHINE_SETUP.md` - Documentation for local MCP setup
- **Purpose**: Enables using the tool directly from Claude Desktop/Code via MCP protocol

### 2. MoveToDocs Workflow Node
- **File**: `nodes.py` (lines 917-960)
- **Purpose**: Automatically moves generated tutorials from `output/` to `docs/` folder
- **Integration**: Added to workflow in `flow.py`

### 3. Documentation Organization
- **Added Folders**:
  - `docs/claude-squad/` - Generated tutorial example
  - `docs/infinite-agentic-loop/` - Generated tutorial example
  - `docs/nanobrowser/` - Generated tutorial example

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
   - `MCP/` directory (completely custom)
   - `nodes.py` (contains MoveToDocs class)
   - `flow.py` (modified workflow)

2. **Merge Strategy**:
   - The `MCP/` directory is entirely our addition, so conflicts are unlikely
   - For `nodes.py` and `flow.py`, carefully review changes during merges
   - Use `git diff` to compare before merging

3. **Testing After Updates**:
   - Test MCP server: `python MCP/mcp_server_robust.py`
   - Test MoveToDocs: Run a tutorial generation and verify it moves to `docs/`
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