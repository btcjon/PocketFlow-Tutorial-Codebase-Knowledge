#!/usr/bin/env python3
"""
MCP Server for Tutorial Codebase Knowledge Generator
"""

import asyncio
import json
import sys
from typing import Any
from datetime import datetime
import os
from pathlib import Path

# Import the existing tutorial generation logic
from flow import create_tutorial_flow

async def handle_list_tools(request_id: Any) -> dict:
    """Handle tools/list request."""
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "result": {
            "tools": [
                {
                    "name": "generate_tutorial",
                    "description": "Generate a comprehensive tutorial from a codebase. Just provide the GitHub URL or local directory path.",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "source": {
                                "type": "string",
                                "description": "GitHub repository URL (e.g. https://github.com/user/repo) or local directory path"
                            },
                            "source_type": {
                                "type": "string",
                                "enum": ["repo", "dir"],
                                "description": "Either 'repo' for GitHub URL or 'dir' for local directory (auto-detected if not specified)"
                            },
                            "language": {
                                "type": "string",
                                "description": "Language for the tutorial (default: English)"
                            }
                        },
                        "required": ["source"]
                    }
                }
            ]
        }
    }

async def handle_call_tool(request_id: Any, params: dict) -> dict:
    """Handle tools/call request."""
    tool_name = params.get("name")
    
    if tool_name == "generate_tutorial":
        try:
            args = params.get("arguments", {})
            
            # Auto-detect source type if not provided
            source = args["source"]
            source_type = args.get("source_type")
            
            if not source_type:
                if source.startswith(("http://", "https://", "git@")):
                    source_type = "repo"
                else:
                    source_type = "dir"
            
            # Language is optional, default to English
            language = args.get("language", "English")
            
            # Create the tutorial flow
            flow = create_tutorial_flow()
            
            # Initialize shared data like main.py does
            shared = {
                "repo_url": source if source_type == "repo" else None,
                "local_dir": source if source_type == "dir" else None,
                "project_name": None,  # Will be derived by FetchRepo
                "github_token": os.environ.get('GITHUB_TOKEN'),
                "output_dir": "output",  # Will be moved to docs by MoveToDocs
                
                # Default file patterns
                "include_patterns": {
                    "*.py", "*.js", "*.jsx", "*.ts", "*.tsx", "*.go", "*.java", "*.pyi", "*.pyx",
                    "*.c", "*.cc", "*.cpp", "*.h", "*.md", "*.rst", "Dockerfile",
                    "Makefile", "*.yaml", "*.yml",
                },
                "exclude_patterns": {
                    "assets/*", "data/*", "examples/*", "images/*", "public/*", "static/*", "temp/*",
                    "docs/*", 
                    "venv/*", ".venv/*", "*test*", "tests/*", "docs/*", "examples/*", "v1/*",
                    "dist/*", "build/*", "experimental/*", "deprecated/*", "misc/*", 
                    "legacy/*", ".git/*", ".github/*", ".next/*", ".vscode/*", "obj/*", "bin/*", "node_modules/*", "*.log"
                },
                "max_file_size": 100000,
                
                "language": language.lower(),
                "use_cache": True,
                "max_abstraction_num": 10,
                "llm_provider": os.environ.get("LLM_PROVIDER", "openrouter"),  # Use env config
                
                # Will be populated by nodes
                "files": [],
                "abstractions": [],
                "relationships": {},
                "chapter_order": [],
                "chapters": [],
                "final_output_dir": None,
                "final_docs_dir": None
            }
            
            # Run the flow
            flow.run(shared)
            
            # The tutorial is now saved in the docs folder by MoveToDocs
            docs_path = shared.get("final_docs_dir")
            if not docs_path:
                raise Exception("Tutorial generation failed - no output directory created")
            
            abs_path = os.path.abspath(docs_path)
            rel_path = os.path.relpath(docs_path, os.getcwd())
            
            message = f"Tutorial successfully generated!\n\nSaved to: {rel_path}\nFull path: {abs_path}\n\nThe tutorial includes multiple files (index.md and chapter files)."
            
        except Exception as e:
            message = f"Error generating tutorial: {str(e)}"
        
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "content": [
                    {
                        "type": "text",
                        "text": message
                    }
                ]
            }
        }
    
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "error": {
            "code": -32601,
            "message": f"Unknown tool: {tool_name}"
        }
    }

async def handle_request(request: dict) -> dict:
    """Handle a single request."""
    method = request.get("method")
    request_id = request.get("id")
    params = request.get("params", {})
    
    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "protocolVersion": "0.1.0",
                "capabilities": {
                    "tools": {}
                },
                "serverInfo": {
                    "name": "tutorial-codebase-knowledge",
                    "version": "1.0.0"
                }
            }
        }
    elif method == "tools/list":
        return await handle_list_tools(request_id)
    elif method == "tools/call":
        return await handle_call_tool(request_id, params)
    else:
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {
                "code": -32601,
                "message": f"Method not found: {method}"
            }
        }

async def main():
    """Run the MCP server."""
    print("MCP Server starting...", file=sys.stderr)
    
    # Read from stdin, write to stdout
    while True:
        try:
            line = sys.stdin.readline()
            if not line:
                print("No more input, exiting", file=sys.stderr)
                break
            
            print(f"Received: {line.strip()}", file=sys.stderr)
            
            request = json.loads(line)
            response = await handle_request(request)
            
            print(f"Sending: {json.dumps(response)}", file=sys.stderr)
            print(json.dumps(response))
            sys.stdout.flush()
            
        except json.JSONDecodeError as e:
            print(f"JSON decode error: {e}", file=sys.stderr)
            print(f"Line was: {line}", file=sys.stderr)
        except Exception as e:
            # Log errors to stderr
            print(f"Error: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc(file=sys.stderr)

if __name__ == "__main__":
    asyncio.run(main())