#!/usr/bin/env python3
"""
Standalone Tutorial Generator V2 - Simplified
==============================================

Streamlined version with simplified GitHub crawling and reliable OpenRouter LLM calls.

REQUIREMENTS
------------
    pip install requests pyyaml

Environment variables:
    OPENROUTER_API_KEY  - Required for LLM calls
    GITHUB_TOKEN        - Optional, for private repos

USAGE
-----
Basic:
    python standalone_tutorial_generator_v2.py --repo https://github.com/user/repo

Advanced:
    python standalone_tutorial_generator_v2.py --repo https://github.com/user/repo \
        --max-abstractions 6 \
        --max-size 50000

OUTPUT
------
    docs/<project_name>/<project_name>_tutorial.md
"""

import os
import re
import yaml
import json
import logging
import argparse
import requests
from datetime import datetime
from typing import Set, Dict, Any, List, Tuple
import fnmatch

# ============================================================================
# LOGGING SETUP
# ============================================================================

log_directory = "logs"
os.makedirs(log_directory, exist_ok=True)
log_file = os.path.join(log_directory, f"llm_calls_{datetime.now().strftime('%Y%m%d')}.log")

logger = logging.getLogger("llm_logger")
logger.setLevel(logging.INFO)
logger.propagate = False
file_handler = logging.FileHandler(log_file, encoding='utf-8')
file_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
logger.addHandler(file_handler)

cache_file = "llm_cache.json"

# ============================================================================
# LLM FUNCTIONS (OpenRouter only for simplicity)
# ============================================================================

def call_llm(prompt: str, use_cache: bool = True) -> str:
    """Call OpenRouter LLM with caching"""
    logger.info(f"PROMPT: {prompt[:300]}...")

    if use_cache and os.path.exists(cache_file):
        try:
            with open(cache_file, "r") as f:
                cache = json.load(f)
                if prompt in cache:
                    logger.info("Cache hit!")
                    return cache[prompt]
        except:
            pass

    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise ValueError("OPENROUTER_API_KEY not set")

    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        },
        json={
            "model": "google/gemini-2.5-flash-preview-09-2025",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7
        }
    )

    if response.status_code != 200:
        raise Exception(f"OpenRouter error: {response.status_code} - {response.text}")

    result = response.json()["choices"][0]["message"]["content"]
    logger.info(f"RESPONSE: {result[:300]}...")

    if use_cache:
        try:
            cache = {}
            if os.path.exists(cache_file):
                with open(cache_file, "r") as f:
                    cache = json.load(f)
            cache[prompt] = result
            with open(cache_file, "w") as f:
                json.dump(cache, f, indent=2)
        except:
            pass

    return result

# ============================================================================
# SIMPLIFIED GITHUB CRAWLER
# ============================================================================

def crawl_github_simple(repo_url: str, token: str = None, include: Set[str] = None,
                       exclude: Set[str] = None, max_size: int = 100000) -> List[Tuple[str, str]]:
    """
    Simplified GitHub crawler - just fetch default branch files directly.
    No complex branch detection or SSH support.
    """
    # Parse owner/repo from URL
    parts = repo_url.rstrip('/').replace('.git', '').split('/')
    owner = parts[-2]
    repo = parts[-1]

    print(f"Fetching files from {owner}/{repo}...")

    headers = {"Accept": "application/vnd.github.v3+json"}
    if token:
        headers["Authorization"] = f"token {token}"

    files = []

    def should_include(path: str, name: str) -> bool:
        """Check if file should be included based on patterns"""
        if include and not any(fnmatch.fnmatch(name, p) for p in include):
            return False
        if exclude and any(fnmatch.fnmatch(path, p) for p in exclude):
            return False
        return True

    def fetch_dir(path: str = ""):
        """Recursively fetch directory contents"""
        url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"

        try:
            response = requests.get(url, headers=headers, timeout=30)

            if response.status_code == 403:
                print(f"Rate limit hit. Waiting 60 seconds...")
                import time
                time.sleep(60)
                return fetch_dir(path)

            if response.status_code != 200:
                print(f"Error fetching {path}: {response.status_code}")
                return

            items = response.json()

            for item in items:
                item_path = item["path"]

                if item["type"] == "file":
                    if not should_include(item_path, item["name"]):
                        continue

                    size = item.get("size", 0)
                    if size > max_size:
                        print(f"Skip {item_path} (too large: {size} bytes)")
                        continue

                    # Download file content
                    download_url = item.get("download_url")
                    if download_url:
                        content_resp = requests.get(download_url, timeout=30)
                        if content_resp.status_code == 200:
                            try:
                                content = content_resp.text
                                files.append((item_path, content))
                                print(f"✓ {item_path} ({size} bytes)")
                            except:
                                print(f"✗ {item_path} (encoding error)")

                elif item["type"] == "dir":
                    # Recursively fetch subdirectory
                    fetch_dir(item_path)

        except Exception as e:
            print(f"Error fetching {path}: {e}")

    # Start from root
    fetch_dir("")

    print(f"\nFetched {len(files)} files total")
    return files

# ============================================================================
# LOCAL CRAWLER
# ============================================================================

def crawl_local_simple(directory: str, include: Set[str] = None,
                      exclude: Set[str] = None, max_size: int = 100000) -> List[Tuple[str, str]]:
    """Simplified local file crawler"""
    files = []

    for root, dirs, filenames in os.walk(directory):
        # Filter out excluded directories
        if exclude:
            dirs[:] = [d for d in dirs if not any(fnmatch.fnmatch(d, p) for p in exclude)]

        for filename in filenames:
            filepath = os.path.join(root, filename)
            relpath = os.path.relpath(filepath, directory)

            # Check patterns
            if include and not any(fnmatch.fnmatch(filename, p) for p in include):
                continue
            if exclude and any(fnmatch.fnmatch(relpath, p) for p in exclude):
                continue

            # Check size
            try:
                size = os.path.getsize(filepath)
                if max_size and size > max_size:
                    continue

                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                    files.append((relpath, content))
                    print(f"✓ {relpath}")
            except:
                continue

    print(f"\nFetched {len(files)} files")
    return files

# ============================================================================
# CORE WORKFLOW
# ============================================================================

def truncate_content(content: str, max_chars: int = 4000) -> str:
    """Truncate large content keeping beginning and end"""
    if len(content) <= max_chars:
        return content
    half = max_chars // 2
    return content[:half] + f"\n\n... [truncated {len(content) - max_chars} chars] ...\n\n" + content[-half:]

def identify_abstractions(files: List[Tuple[str, str]], project_name: str, max_num: int, use_cache: bool) -> List[Dict]:
    """Step 1: Identify core abstractions"""
    print(f"\n[1/6] Identifying {max_num} core abstractions...")

    # Build context
    context = ""
    for i, (path, content) in enumerate(files):
        context += f"--- File {i}: {path} ---\n{truncate_content(content, 3000)}\n\n"

    file_list = "\n".join([f"- {i} # {path}" for i, (path, _) in enumerate(files)])

    prompt = f"""Analyze this codebase for project "{project_name}".

Files:
{file_list}

Context:
{context}

Identify the top {max_num} core concepts/abstractions.

For each, provide:
- name: Concise name
- description: Beginner-friendly explanation (~100 words)
- file_indices: Relevant file indices (e.g., [0, 3, 7])

Output as YAML:
```yaml
- name: Core Concept Name
  description: What it does and why it matters...
  file_indices: [0, 3]
```"""

    response = call_llm(prompt, use_cache)
    yaml_str = response.split("```yaml")[1].split("```")[0].strip()
    abstractions = yaml.safe_load(yaml_str)

    # Validate and clean
    result = []
    for item in abstractions:
        indices = [int(str(i).split('#')[0].strip()) if isinstance(i, str) else i
                  for i in item["file_indices"]]
        result.append({
            "name": item["name"],
            "description": item["description"],
            "files": indices
        })

    print(f"✓ Identified {len(result)} abstractions")
    return result

def analyze_relationships(abstractions: List[Dict], files: List[Tuple[str, str]],
                         project_name: str, use_cache: bool) -> Dict:
    """Step 2: Analyze relationships"""
    print("\n[2/6] Analyzing relationships...")

    # Build context with relevant files
    context = "Abstractions:\n"
    for i, a in enumerate(abstractions):
        context += f"{i}. {a['name']}: {a['description'][:100]}...\n"

    prompt = f"""For project "{project_name}", analyze relationships between these abstractions:

{context}

Provide:
1. summary: High-level project summary (3-4 sentences with **bold** for key terms)
2. relationships: List of connections between abstractions

Output as YAML:
```yaml
summary: |
  Project does X by using **CoreConcept** to achieve Y...
relationships:
  - from_abstraction: 0 # Name1
    to_abstraction: 1 # Name2
    label: "Uses"
```"""

    response = call_llm(prompt, use_cache)
    yaml_str = response.split("```yaml")[1].split("```")[0].strip()
    data = yaml.safe_load(yaml_str)

    # Extract indices
    relationships = []
    for rel in data["relationships"]:
        from_idx = int(str(rel["from_abstraction"]).split('#')[0].strip())
        to_idx = int(str(rel["to_abstraction"]).split('#')[0].strip())
        relationships.append({"from": from_idx, "to": to_idx, "label": rel["label"]})

    print(f"✓ Found {len(relationships)} relationships")
    return {"summary": data["summary"], "details": relationships}

def order_chapters(abstractions: List[Dict], relationships: Dict, project_name: str, use_cache: bool) -> List[int]:
    """Step 3: Determine chapter order"""
    print("\n[3/6] Ordering chapters...")

    abs_list = "\n".join([f"{i}. {a['name']}" for i, a in enumerate(abstractions)])

    prompt = f"""For tutorial about "{project_name}", determine best order to explain these concepts:

{abs_list}

Order from foundational/user-facing to detailed/implementation.

Output as YAML list of indices:
```yaml
- 2 # FoundationalConcept
- 0 # CoreFeature
```"""

    response = call_llm(prompt, use_cache)
    yaml_str = response.split("```yaml")[1].split("```")[0].strip()
    ordered = yaml.safe_load(yaml_str)

    result = [int(str(x).split('#')[0].strip()) for x in ordered]
    print(f"✓ Chapter order: {result}")
    return result

def write_chapter(abstraction: Dict, chapter_num: int, files: List[Tuple[str, str]],
                 project_name: str, use_cache: bool) -> str:
    """Step 4: Write a single chapter"""
    name = abstraction["name"]
    desc = abstraction["description"]

    # Get relevant file content
    file_context = ""
    for idx in abstraction["files"][:5]:  # Limit to 5 files
        if idx < len(files):
            path, content = files[idx]
            file_context += f"--- {path} ---\n{truncate_content(content, 4000)}\n\n"

    prompt = f"""Write tutorial chapter {chapter_num} for "{project_name}" about: {name}

Description:
{desc}

Code:
{file_context}

Write beginner-friendly chapter with:
- Clear heading: # Chapter {chapter_num}: {name}
- Motivation (what problem it solves)
- How to use it (with examples)
- Internal implementation
- Code blocks under 10 lines
- Simple analogies

Output markdown directly (no ```markdown tags):"""

    response = call_llm(prompt, use_cache)

    # Ensure heading
    if not response.strip().startswith(f"# Chapter {chapter_num}"):
        response = f"# Chapter {chapter_num}: {name}\n\n{response}"

    return response

def generate_tutorial(files: List[Tuple[str, str]], config: Dict) -> str:
    """Main workflow: orchestrate all steps"""

    # Step 1: Identify abstractions
    abstractions = identify_abstractions(
        files, config["project_name"], config["max_abstractions"], config["use_cache"]
    )

    # Step 2: Analyze relationships
    relationships = analyze_relationships(
        abstractions, files, config["project_name"], config["use_cache"]
    )

    # Step 3: Order chapters
    chapter_order = order_chapters(
        abstractions, relationships, config["project_name"], config["use_cache"]
    )

    # Step 4: Write chapters
    print("\n[4/6] Writing chapters...")
    chapters = []
    for i, abs_idx in enumerate(chapter_order):
        print(f"  Writing chapter {i+1}/{len(chapter_order)}: {abstractions[abs_idx]['name']}")
        chapter = write_chapter(
            abstractions[abs_idx], i+1, files, config["project_name"], config["use_cache"]
        )
        chapters.append(chapter)

    # Step 5: Generate Mermaid diagram
    print("\n[5/6] Generating diagram...")
    mermaid = ["flowchart TD"]
    for i, a in enumerate(abstractions):
        mermaid.append(f'    A{i}["{a["name"]}"]')
    for rel in relationships["details"]:
        label = rel["label"].replace('"', '')[:20]
        mermaid.append(f'    A{rel["from"]} -- "{label}" --> A{rel["to"]}')

    # Step 6: Combine into single document
    print("\n[6/6] Combining tutorial...")

    doc = f"# Tutorial: {config['project_name']}\n\n"
    doc += f"{relationships['summary']}\n\n"
    doc += f"**Source:** {config.get('repo_url', 'Local Directory')}\n\n"
    doc += "```mermaid\n" + "\n".join(mermaid) + "\n```\n\n"
    doc += "## Table of Contents\n\n"

    for i, abs_idx in enumerate(chapter_order):
        name = abstractions[abs_idx]["name"]
        anchor = f"chapter-{i+1}-{name.lower().replace(' ', '-')}"
        anchor = re.sub(r'[^a-z0-9\-]', '', anchor)
        doc += f"{i+1}. [{name}](#{anchor})\n"

    doc += "\n---\n\n"

    for chapter in chapters:
        doc += chapter.strip() + "\n\n---\n\n"

    doc += "Generated by [AI Codebase Knowledge Builder](https://github.com/The-Pocket/Tutorial-Codebase-Knowledge)\n"

    return doc

# ============================================================================
# MAIN
# ============================================================================

DEFAULT_INCLUDE = {"*.py", "*.js", "*.jsx", "*.ts", "*.tsx", "*.go", "*.java",
                   "*.c", "*.cpp", "*.h", "*.md", "*.rst", "*.yaml", "*.yml"}
DEFAULT_EXCLUDE = {"*test*", "*docs/*", "*venv/*", "*node_modules/*", "*build/*",
                   "*dist/*", ".git/*", "*.log"}

def main():
    parser = argparse.ArgumentParser(description="Generate tutorial from codebase")

    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--repo", help="GitHub repository URL")
    source.add_argument("--dir", help="Local directory path")

    parser.add_argument("-n", "--name", help="Project name (auto-detected if omitted)")
    parser.add_argument("-t", "--token", help="GitHub token")
    parser.add_argument("-o", "--output", default="docs", help="Output directory (default: docs)")
    parser.add_argument("-i", "--include", nargs="+", help="Include patterns (e.g., *.py *.js)")
    parser.add_argument("-e", "--exclude", nargs="+", help="Exclude patterns")
    parser.add_argument("-s", "--max-size", type=int, default=100000, help="Max file size (bytes)")
    parser.add_argument("--max-abstractions", type=int, default=8, help="Number of abstractions")
    parser.add_argument("--no-cache", action="store_true", help="Disable LLM caching")

    args = parser.parse_args()

    # Derive project name
    if args.name:
        project_name = args.name
    elif args.repo:
        project_name = args.repo.rstrip('/').replace('.git', '').split('/')[-1]
    else:
        project_name = os.path.basename(os.path.abspath(args.dir))

    print(f"=== Tutorial Generator for: {project_name} ===\n")

    # Fetch files
    include = set(args.include) if args.include else DEFAULT_INCLUDE
    exclude = set(args.exclude) if args.exclude else DEFAULT_EXCLUDE

    if args.repo:
        token = args.token or os.getenv("GITHUB_TOKEN")
        files = crawl_github_simple(args.repo, token, include, exclude, args.max_size)
    else:
        files = crawl_local_simple(args.dir, include, exclude, args.max_size)

    if not files:
        print("Error: No files found!")
        return

    # Configure
    config = {
        "project_name": project_name,
        "repo_url": args.repo,
        "max_abstractions": args.max_abstractions,
        "use_cache": not args.no_cache
    }

    # Generate
    tutorial = generate_tutorial(files, config)

    # Save
    output_dir = os.path.join(args.output, project_name)
    os.makedirs(output_dir, exist_ok=True)

    output_file = os.path.join(output_dir, f"{project_name}_tutorial.md")
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(tutorial)

    print(f"\n✅ Tutorial complete: {output_file}")

if __name__ == "__main__":
    main()
