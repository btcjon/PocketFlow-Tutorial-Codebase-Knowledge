#!/usr/bin/env python3
"""
Direct test of tutorial generation for Khoj repository
"""

import os
from datetime import datetime
from pathlib import Path
from flow import create_tutorial_flow

def test_khoj_tutorial():
    """Test generating a tutorial for Khoj repository."""
    
    # Set up output directory
    output_dir = os.path.expanduser("~/Dropbox/tutorial-docs")
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # Set LLM provider
    os.environ["LLM_PROVIDER"] = "gemini"
    
    # Create the tutorial flow
    flow = create_tutorial_flow()
    
    # Default file patterns (from main.py)
    DEFAULT_INCLUDE_PATTERNS = {
        "*.py", "*.js", "*.jsx", "*.ts", "*.tsx", "*.go", "*.java", "*.pyi", "*.pyx",
        "*.c", "*.cc", "*.cpp", "*.h", "*.md", "*.rst", "Dockerfile",
        "Makefile", "*.yaml", "*.yml",
    }
    
    DEFAULT_EXCLUDE_PATTERNS = {
        "assets/*", "data/*", "examples/*", "images/*", "public/*", "static/*", "temp/*",
        "docs/*", 
        "venv/*", ".venv/*", "*test*", "tests/*", "docs/*", "examples/*", "v1/*",
        "dist/*", "build/*", "experimental/*", "deprecated/*", "misc/*", 
        "legacy/*", ".git/*", ".github/*", ".next/*", ".vscode/*", "obj/*", "bin/*", "node_modules/*", "*.log"
    }
    
    # Prepare input data
    input_data = {
        "language": "English",
        "repo_url": "https://github.com/khoj-ai/khoj",
        "local_dir": None,
        "project_name": None,
        "github_token": os.environ.get('GITHUB_TOKEN'),
        "output_dir": output_dir,
        "include_patterns": DEFAULT_INCLUDE_PATTERNS,
        "exclude_patterns": DEFAULT_EXCLUDE_PATTERNS,
        "max_file_size": 100000,
        "use_cache": True,
        "max_abstraction_num": 10,
        "llm_provider": "gemini",
        "files": [],
        "abstractions": [],
        "relationships": {},
        "chapter_order": [],
        "chapters": [],
        "final_output_dir": None
    }
    
    print("Starting tutorial generation for Khoj...")
    
    # Run the flow
    result = flow.run(input_data)
    
    # Generate output filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_filename = f"tutorial_khoj_{timestamp}.md"
    output_path = os.path.join(output_dir, output_filename)
    
    # Save the tutorial
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(result["tutorial"])
    
    print(f"\nTutorial successfully generated!")
    print(f"Saved to: {output_path}")
    print(f"\nFirst 500 characters:")
    print(result["tutorial"][:500])

if __name__ == "__main__":
    test_khoj_tutorial()