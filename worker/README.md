# Tutorial Codebase Knowledge - Cloudflare Worker

This is a Cloudflare Worker implementation of the Tutorial Codebase Knowledge MCP server. It allows you to generate comprehensive tutorials from any GitHub repository, accessible remotely without any local installation.

## Setup

1. **Install dependencies:**
   ```bash
   cd worker
   npm install
   ```

2. **Create KV namespace:**
   ```bash
   wrangler kv:namespace create "TUTORIAL_KV"
   wrangler kv:namespace create "TUTORIAL_KV" --preview
   ```
   
   Copy the IDs from the output and update them in `wrangler.toml`.

3. **Set up API keys (optional):**
   
   For better tutorial generation, add your OpenAI API key:
   ```bash
   wrangler secret put OPENAI_API_KEY
   ```

4. **Deploy:**
   ```bash
   npm run deploy
   ```

## Usage with Claude Desktop

Add to your Claude Desktop configuration:

```json
{
  "mcpServers": {
    "tutorial-codebase-knowledge": {
      "url": "https://tutorial-codebase-knowledge.your-username.workers.dev",
      "transport": "sse"
    }
  }
}
```

## Available Tools

### generate_tutorial
Generates a comprehensive tutorial from a GitHub repository.

**Parameters:**
- `source` (required): GitHub repository URL
- `source_type`: Currently only supports "repo"
- `language`: Tutorial language (default: English)
- `llm_provider`: LLM provider to use (openai, anthropic, gemini)

**Example:**
```
"Generate a tutorial for https://github.com/example/project"
```

## Features

- ✅ Fully serverless - runs on Cloudflare's edge network
- ✅ No local installation required
- ✅ Automatic GitHub repository analysis
- ✅ Multi-language tutorial generation
- ✅ KV storage for generated tutorials
- ✅ Secure with optional API key authentication

## Development

Run locally:
```bash
npm run dev
```

View logs:
```bash
npm run tail
```

## Architecture

The worker:
1. Fetches repository files from GitHub API
2. Analyzes code structure to identify key abstractions
3. Generates comprehensive tutorial using LLM
4. Stores results in Cloudflare KV
5. Returns tutorial via MCP protocol

## Limitations

- Currently only supports public GitHub repositories
- Limited to 100 files per repository for performance
- Requires API keys for advanced LLM features