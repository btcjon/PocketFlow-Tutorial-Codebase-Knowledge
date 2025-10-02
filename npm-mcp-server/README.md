# Tutorial Codebase Knowledge MCP Server

An MCP (Model Context Protocol) server that generates comprehensive, beginner-friendly tutorials from any codebase. This tool transforms complex code repositories into structured learning materials with explanations, examples, and visual diagrams.

## Features

- 🚀 **GitHub Repository Analysis**: Analyze any public GitHub repository
- 📁 **Local Directory Support**: Generate tutorials from local codebases  
- 🌍 **Multi-language Support**: Generate tutorials in different languages
- 🔄 **Multiple LLM Providers**: Support for OpenRouter, Gemini, OpenAI, and Anthropic
- 📊 **Visual Diagrams**: Automatic mermaid diagram generation showing relationships
- 📖 **Single File Output**: Combined tutorial in one structured markdown file
- 🎯 **Beginner-Friendly**: Designed for newcomers to understand complex codebases

## Installation

### As an NPM Package

```bash
npm install -g @btcjon/tutorial-codebase-knowledge-mcp
```

### For Claude Desktop

Add this to your Claude Desktop configuration (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "tutorial-codebase-knowledge": {
      "command": "npx",
      "args": ["@btcjon/tutorial-codebase-knowledge-mcp"]
    }
  }
}
```

## Configuration

The server requires an LLM provider API key. Set one of the following environment variables:

```bash
# For OpenRouter (recommended)
export OPENROUTER_API_KEY="your-api-key"

# For other providers
export GEMINI_API_KEY="your-api-key"
export OPENAI_API_KEY="your-api-key" 
export ANTHROPIC_API_KEY="your-api-key"
```

## Usage

### Available Tools

#### `generate_tutorial`
Generate a comprehensive tutorial from a codebase.

**Parameters:**
- `source` (required): GitHub repository URL or local directory path
- `source_type` (optional): "repo" or "dir" (auto-detected)
- `output_dir` (optional): Where to save the tutorial
- `language` (optional): Tutorial language (default: English)
- `llm_provider` (optional): LLM provider (openrouter, gemini, openai, anthropic)

**Examples:**
```
Generate a tutorial for https://github.com/langchain-ai/langchain
Generate a tutorial for my local project at /Users/me/myproject and save it to ~/Desktop/docs
```

#### `list_generated_tutorials`
List all tutorials in a directory.

**Parameters:**
- `directory` (optional): Directory to search (default: ./mydocs)

#### `get_tutorial_content`
Read the content of a generated tutorial file.

**Parameters:**
- `tutorial_path` (required): Path to the tutorial file

### Output Structure

Generated tutorials include:

1. **Project Summary**: High-level overview with visual relationship diagram
2. **Table of Contents**: Clickable navigation with anchor links
3. **Chapter-by-Chapter Breakdown**: 
   - Core abstractions and concepts
   - Code examples with explanations
   - Implementation details
   - Analogies for beginners
4. **Mermaid Diagrams**: Visual representation of component relationships

### Smart Output Locations

- **GitHub repos**: Saved to `~/Dropbox/tutorial-docs/tutorial_<repo>_<timestamp>.md`
- **Local directories**: Saved to `<directory>/mydocs/tutorial_<dirname>_<timestamp>.md`
- **Custom location**: Use the `output_dir` parameter

## How It Works

1. **Repository Analysis**: Fetches and analyzes codebase structure
2. **Abstraction Identification**: AI identifies key concepts and patterns
3. **Relationship Mapping**: Maps connections between components
4. **Chapter Ordering**: Determines optimal learning sequence
5. **Content Generation**: Creates beginner-friendly explanations
6. **Tutorial Assembly**: Combines everything into a single structured document

## Requirements

- Node.js 16+
- Python 3.11+ (for the underlying analysis engine)
- Required Python packages: `pocketflow`, `google-generativeai`, `requests`, `pyyaml`

## Development

```bash
git clone https://github.com/btcjon/PocketFlow-Tutorial-Codebase-Knowledge.git
cd PocketFlow-Tutorial-Codebase-Knowledge/npm-mcp-server
npm install
npm run build
npm link  # For local testing
```

## License

MIT License - see LICENSE file for details.

## Contributing

Contributions are welcome! Please see the main repository for guidelines.