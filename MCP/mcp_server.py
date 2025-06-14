#!/usr/bin/env python3
"""
MCP Server for Tutorial Codebase Knowledge Generator

This server provides tools to generate comprehensive tutorials from codebases,
either from GitHub repositories or local directories.
"""

import os
import json
import asyncio
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# Import the existing tutorial generation logic
from flow import create_tutorial_flow
from nodes import FetchRepo

# Initialize the MCP server
server = Server("tutorial-codebase-knowledge")

@server.list_tools()
async def list_tools() -> List[Tool]:
    """List available tools."""
    return [
        Tool(
            name="generate_tutorial",
            description="Generate a comprehensive tutorial from a codebase. Just provide the GitHub URL or local directory path. The process typically takes 5-10 minutes.",
            inputSchema={
                "type": "object",
                "properties": {
                    "source": {
                        "type": "string",
                        "description": "GitHub repository URL (e.g. https://github.com/user/repo) or local directory path"
                    },
                    "language": {
                        "type": "string",
                        "description": "Language for the tutorial (default: English)"
                    }
                },
                "required": ["source"]
            }
        ),
        Tool(
            name="list_generated_tutorials",
            description="List all generated tutorials in a directory",
            inputSchema={
                "type": "object",
                "properties": {
                    "directory": {
                        "type": "string",
                        "description": "Directory to search for tutorials (default: ~/Dropbox/tutorial-docs)"
                    }
                }
            }
        ),
        Tool(
            name="get_tutorial_content",
            description="Read the content of a generated tutorial",
            inputSchema={
                "type": "object",
                "properties": {
                    "tutorial_path": {
                        "type": "string",
                        "description": "Path to the tutorial file"
                    }
                },
                "required": ["tutorial_path"]
            }
        )
    ]

@server.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle tool calls."""
    
    if name == "generate_tutorial":
        result = await generate_tutorial(
            source=arguments["source"],
            language=arguments.get("language", "English")
        )
        return [TextContent(type="text", text=result["message"])]
    
    elif name == "list_generated_tutorials":
        result = await list_generated_tutorials(
            directory=arguments.get("directory")
        )
        if result["count"] == 0:
            message = result.get("message", "No tutorials found.")
        else:
            message = f"Found {result['count']} tutorials in {result['directory']}:\n\n"
            for tutorial in result["tutorials"]:
                message += f"- {tutorial['filename']} ({tutorial['size']} bytes, modified: {tutorial['modified']})\n"
        return [TextContent(type="text", text=message)]
    
    elif name == "get_tutorial_content":
        result = await get_tutorial_content(
            tutorial_path=arguments["tutorial_path"]
        )
        if result["success"]:
            return [TextContent(type="text", text=result["content"])]
        else:
            return [TextContent(type="text", text=result["message"])]
    
    else:
        return [TextContent(type="text", text=f"Unknown tool: {name}")]

async def generate_tutorial(
    source: str,
    language: str = "English"
) -> Dict[str, Any]:
    """
    Generate a comprehensive tutorial from a codebase.
    
    Args:
        source: GitHub repository URL or local directory path
        language: Language for the tutorial (default: English)
    
    Returns:
        Dictionary containing:
        - success: Boolean indicating if generation succeeded
        - tutorial_path: Path to the generated tutorial folder
        - relative_path: Path relative to current directory
        - message: Success or error message with file location
    
    Tutorials are automatically saved to:
    /Users/jonbennett/Dropbox/Coding-Main/Tutorial-Codebase-Knowledge/docs/{project_name}/
    """
    try:
        # Auto-detect source type
        if source.startswith(("http://", "https://", "git@")):
            source_type = "repo"
        else:
            source_type = "dir"
        
        # Create the tutorial flow
        flow = create_tutorial_flow()
        
        # Initialize shared data like main.py does
        shared = {
            "repo_url": source if source_type == "repo" else None,
            "local_dir": source if source_type == "dir" else None,
            "project_name": None,  # Will be derived by FetchRepo
            "github_token": os.environ.get('GITHUB_TOKEN'),
            "output_dir": "output",  # Will be moved to docs by MoveToDocs
            
            # Default file patterns (from main.py)
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
            
            "language": language,
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
        
        # Run the flow synchronously (since we're in async context)
        await asyncio.get_event_loop().run_in_executor(
            None, 
            flow.run, 
            shared
        )
        
        # The tutorial is now saved in the docs folder by MoveToDocs
        docs_path = shared.get("final_docs_dir")
        if not docs_path:
            raise Exception("Tutorial generation failed - no output directory created")
        
        # Get absolute and relative paths
        abs_path = os.path.abspath(docs_path)
        rel_path = os.path.relpath(docs_path, os.getcwd())
        
        return {
            "success": True,
            "tutorial_path": abs_path,
            "relative_path": rel_path,
            "message": f"Tutorial successfully generated!\n\nSaved to: {rel_path}\nFull path: {abs_path}\n\nThe tutorial includes multiple files (index.md and chapter files).\nYou can now commit this documentation to your repository."
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": f"Error generating tutorial: {str(e)}"
        }

async def list_generated_tutorials(
    directory: Optional[str] = None
) -> Dict[str, Any]:
    """
    List all generated tutorials in a directory.
    
    Args:
        directory: Directory to search for tutorials (default: ~/Dropbox/tutorial-docs)
                  You can use ~ for home directory (e.g., "~/Desktop/docs")
    
    Returns:
        Dictionary containing:
        - tutorials: List of tutorial files with metadata
        - count: Number of tutorials found
        - directory: The directory that was searched
    """
    try:
        if directory is None:
            # Default to ~/Dropbox/tutorial-docs/
            directory = os.path.expanduser("~/Dropbox/tutorial-docs")
        else:
            # Expand ~ and make absolute
            directory = os.path.expanduser(directory)
            if not os.path.isabs(directory):
                directory = os.path.join(os.getcwd(), directory)
        
        if not os.path.exists(directory):
            return {
                "tutorials": [],
                "count": 0,
                "directory": directory,
                "message": f"No tutorials found. Directory {directory} does not exist yet. Generate a tutorial to create it!"
            }
        
        tutorials = []
        for file in Path(directory).glob("tutorial_*.md"):
            stat = file.stat()
            tutorials.append({
                "filename": file.name,
                "path": str(file),
                "size": stat.st_size,
                "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
            })
        
        tutorials.sort(key=lambda x: x["modified"], reverse=True)
        
        return {
            "tutorials": tutorials,
            "count": len(tutorials),
            "directory": directory
        }
        
    except Exception as e:
        return {
            "tutorials": [],
            "count": 0,
            "message": f"Error listing tutorials: {str(e)}"
        }

async def get_tutorial_content(
    tutorial_path: str
) -> Dict[str, Any]:
    """
    Read the content of a generated tutorial.
    
    Args:
        tutorial_path: Path to the tutorial file
    
    Returns:
        Dictionary containing:
        - content: The tutorial content
        - success: Boolean indicating if read succeeded
    """
    try:
        tutorial_path = os.path.expanduser(tutorial_path)
        
        with open(tutorial_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return {
            "success": True,
            "content": content,
            "path": tutorial_path
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": f"Error reading tutorial: {str(e)}"
        }

async def main():
    """Run the MCP server."""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream, 
            write_stream,
            initialization_options={}
        )

if __name__ == "__main__":
    asyncio.run(main())