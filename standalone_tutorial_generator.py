#!/usr/bin/env python3
"""
Standalone Tutorial Generator
==============================

Self-contained script for generating beginner-friendly tutorials from codebases.
All dependencies bundled into a single file for maximum portability.

REQUIREMENTS
------------
External Python packages (install via pip):
    pip install requests pyyaml google-generativeai

Environment variables (at least one required):
    GEMINI_API_KEY      - For Google Gemini (recommended, free tier available)
    OPENROUTER_API_KEY  - For OpenRouter (paid service)
    GITHUB_TOKEN        - Optional, for private repos and higher rate limits

USAGE
-----
Basic usage - analyze a GitHub repository:
    python standalone_tutorial_generator.py --repo https://github.com/user/repo

Analyze a local directory:
    python standalone_tutorial_generator.py --dir /path/to/project

Advanced options:
    python standalone_tutorial_generator.py --repo https://github.com/user/repo \
        --max-abstractions 8 \
        --llm-provider openrouter \
        --language spanish \
        --include "*.py" "*.js" \
        --exclude "tests/*" "build/*" \
        --max-size 200000 \
        --no-cache

OPTIONS
-------
Source (required, choose one):
    --repo URL          GitHub repository URL
    --dir PATH          Local directory path

Configuration:
    -n, --name          Project name (auto-detected if omitted)
    -t, --token         GitHub personal access token
    -o, --output        Output directory (default: ./output)

Filtering:
    -i, --include       File patterns to include (e.g., "*.py" "*.js")
    -e, --exclude       File patterns to exclude (e.g., "tests/*")
    -s, --max-size      Max file size in bytes (default: 100000)

Generation:
    --language          Tutorial language (default: english)
    --max-abstractions  Number of core concepts to identify (default: 10)
    --llm-provider      LLM provider: gemini or openrouter (default: gemini)
    --no-cache          Disable LLM response caching

OUTPUT
------
Generates a single markdown file in docs/<project_name>/<project_name>_tutorial.md
containing:
    - Project summary with relationship diagram (Mermaid)
    - Table of contents with anchor links
    - Beginner-friendly chapters explaining core concepts
    - Code examples and analogies

EXAMPLES
--------
Analyze popular repository with custom settings:
    python standalone_tutorial_generator.py \
        --repo https://github.com/fastapi/fastapi \
        --max-abstractions 6 \
        --include "*.py" "*.md"

Analyze local project, save to custom location:
    python standalone_tutorial_generator.py \
        --dir ~/projects/myapp \
        --output ~/tutorials \
        --exclude "venv/*" "*.pyc"

Generate tutorial in Spanish:
    python standalone_tutorial_generator.py \
        --repo https://github.com/django/django \
        --language spanish

WORKFLOW
--------
The script executes 8 sequential steps:
    1. FetchRepo         - Download/read repository files
    2. IdentifyAbstractions - Extract 5-10 core concepts via LLM
    3. AnalyzeRelationships - Map connections between concepts
    4. OrderChapters     - Determine optimal tutorial structure
    5. WriteChapters     - Generate detailed chapter content
    6. CombineTutorial   - Assemble chapters with diagrams
    7. MergeToSingleFile - Combine into single markdown file
    8. MoveToDocs        - Move to docs/ folder

CACHING
-------
LLM responses are cached in llm_cache.json to speed up re-runs and reduce costs.
Use --no-cache to force fresh LLM calls (useful when testing prompt changes).

LOGS
----
All LLM calls are logged to logs/llm_calls_YYYYMMDD.log for debugging.

TROUBLESHOOTING
---------------
Context length errors:
    - Reduce --max-abstractions (try 5-6)
    - Add more --exclude patterns
    - Increase --max-size to filter large files

Rate limit errors (GitHub):
    - Set GITHUB_TOKEN environment variable
    - Wait for rate limit reset (error shows wait time)

Missing API key:
    export GEMINI_API_KEY="your-key-here"
    # or
    export OPENROUTER_API_KEY="your-key-here"

ARCHITECTURE
------------
This script is a standalone version of the PocketFlow-based Tutorial-Codebase-Knowledge
project. All workflow logic and utilities are bundled into a single file for portability,
while maintaining the same 8-step sequential processing pipeline.
"""

import os
import re
import yaml
import json
import logging
import argparse
import requests
import base64
import tempfile
import time
import fnmatch
from datetime import datetime
from typing import Union, Set, Dict, Any, List, Tuple
from urllib.parse import urlparse

# ============================================================================
# LLM UTILITIES
# ============================================================================

# Configure logging
log_directory = os.getenv("LOG_DIR", "logs")
os.makedirs(log_directory, exist_ok=True)
log_file = os.path.join(log_directory, f"llm_calls_{datetime.now().strftime('%Y%m%d')}.log")

logger = logging.getLogger("llm_logger")
logger.setLevel(logging.INFO)
logger.propagate = False
file_handler = logging.FileHandler(log_file, encoding='utf-8')
file_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
logger.addHandler(file_handler)

cache_file = "llm_cache.json"

def _count_tokens(text: str) -> int:
    """Estimate token count (rough estimate of 4 chars per token)"""
    return len(text) // 4

def _ensure_prompt_fits_context(prompt: str, max_tokens: int = 900000) -> str:
    """Ensure prompt fits within context limits by truncating if necessary"""
    token_count = _count_tokens(prompt)

    if token_count <= max_tokens:
        return prompt

    logger.warning(f"Prompt too long ({token_count} tokens), truncating to fit {max_tokens} tokens")

    target_chars = int(max_tokens * 3.5)

    if len(prompt) <= target_chars:
        return prompt

    keep_start = target_chars // 3
    keep_end = target_chars // 3

    truncated_prompt = (
        prompt[:keep_start] +
        f"\n\n... [CONTENT TRUNCATED - Original length: {len(prompt)} chars, {token_count} tokens] ...\n\n" +
        prompt[-keep_end:]
    )

    logger.info(f"Truncated prompt from {len(prompt)} to {len(truncated_prompt)} characters")
    return truncated_prompt

def _check_cache(prompt: str) -> str:
    """Check if response exists in cache"""
    try:
        if os.path.exists(cache_file):
            with open(cache_file, "r", encoding="utf-8") as f:
                cache = json.load(f)
                if prompt in cache:
                    logger.info("Cache hit!")
                    return cache[prompt]
    except Exception as e:
        logger.warning(f"Cache read error: {e}")
    return None

def _save_to_cache(prompt: str, response: str):
    """Save response to cache"""
    try:
        cache = {}
        if os.path.exists(cache_file):
            with open(cache_file, "r", encoding="utf-8") as f:
                cache = json.load(f)

        cache[prompt] = response

        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(cache, f, indent=2)

    except Exception as e:
        logger.warning(f"Cache write error: {e}")

def _call_gemini(prompt: str) -> str:
    """Call Google Gemini API"""
    from google import genai

    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY", os.getenv("GOOGLE_API_KEY")))
    response = client.models.generate_content(
        model="gemini-2.0-flash-exp", contents=prompt
    )
    return response.text

def _call_openrouter(prompt: str) -> str:
    """Call OpenRouter API"""
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise ValueError("OPENROUTER_API_KEY not found in environment variables")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    data = {
        "model": os.getenv("OPENROUTER_MODEL", "google/gemini-2.5-flash-preview-09-2025"),
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7
    }

    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers=headers,
        json=data
    )

    if response.status_code == 400 and "maximum context length" in response.text:
        data["transforms"] = ["middle-out"]
        logger.warning("Prompt too long, retrying with middle-out transform")
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=data
        )

    if response.status_code != 200:
        raise Exception(f"OpenRouter API error: {response.status_code} - {response.text}")

    return response.json()["choices"][0]["message"]["content"]

def call_llm(prompt: str, use_cache: bool = True) -> str:
    """
    Call an LLM with the given prompt and return the response.

    Args:
        prompt: The text prompt to send to the LLM
        use_cache: Whether to check cache before calling and save response after (default: True)

    Returns:
        The LLM's text response

    Raises:
        Exception: If LLM API call fails

    Environment Variables:
        LLM_PROVIDER: Provider to use (gemini, openrouter)
        GEMINI_API_KEY: Required for Gemini
        OPENROUTER_API_KEY: Required for OpenRouter
        OPENROUTER_MODEL: Model to use with OpenRouter (default: google/gemini-2.5-flash)

    Cache:
        Responses are cached in llm_cache.json with prompt as key
        Logs written to logs/llm_calls_YYYYMMDD.log
    """
    prompt = _ensure_prompt_fits_context(prompt)
    logger.info(f"PROMPT: {prompt[:500]}..." if len(prompt) > 500 else f"PROMPT: {prompt}")

    if use_cache:
        response_from_cache = _check_cache(prompt)
        if response_from_cache:
            return response_from_cache

    provider = os.getenv("LLM_PROVIDER", "gemini").lower()

    try:
        if provider == "gemini":
            response = _call_gemini(prompt)
        elif provider == "openrouter":
            response = _call_openrouter(prompt)
        else:
            logger.warning(f"Unknown LLM provider: {provider}. Falling back to Gemini.")
            response = _call_gemini(prompt)

        if use_cache:
            _save_to_cache(prompt, response)

        logger.info(f"RESPONSE: {response}")
        return response

    except Exception as e:
        logger.error(f"Error calling LLM: {e}")
        raise

# ============================================================================
# FILE CRAWLING UTILITIES
# ============================================================================

def crawl_local_files(
    directory,
    include_patterns=None,
    exclude_patterns=None,
    max_file_size=None,
    use_relative_paths=True,
):
    """
    Crawl files in a local directory with filtering options.

    Args:
        directory: Path to local directory to crawl
        include_patterns: Set of file patterns to include (e.g., {"*.py", "*.js"})
        exclude_patterns: Set of directory/file patterns to exclude (e.g., {"tests/*", "*.pyc"})
        max_file_size: Maximum file size in bytes (files larger are skipped)
        use_relative_paths: Whether to use paths relative to directory (default: True)

    Returns:
        dict: {"files": {filepath: content}}

    Example:
        files = crawl_local_files(
            "/path/to/project",
            include_patterns={"*.py", "*.md"},
            exclude_patterns={"tests/*", "venv/*"},
            max_file_size=100000
        )
    """
    if not os.path.isdir(directory):
        raise ValueError(f"Directory does not exist: {directory}")

    files_dict = {}

    for root, dirs, files in os.walk(directory):
        excluded_dirs = set()
        for d in dirs:
            dirpath_rel = os.path.relpath(os.path.join(root, d), directory)
            if exclude_patterns:
                for pattern in exclude_patterns:
                    if fnmatch.fnmatch(dirpath_rel, pattern) or fnmatch.fnmatch(d, pattern):
                        excluded_dirs.add(d)
                        break

        for d in list(dirs):
            if d in excluded_dirs:
                dirs.remove(d)

        for filename in files:
            filepath = os.path.join(root, filename)
            relpath = os.path.relpath(filepath, directory) if use_relative_paths else filepath

            excluded = False
            if exclude_patterns:
                for pattern in exclude_patterns:
                    if fnmatch.fnmatch(relpath, pattern):
                        excluded = True
                        break

            included = False
            if include_patterns:
                for pattern in include_patterns:
                    if fnmatch.fnmatch(relpath, pattern):
                        included = True
                        break
            else:
                included = True

            if not included or excluded:
                continue

            if max_file_size and os.path.getsize(filepath) > max_file_size:
                continue

            try:
                with open(filepath, "r", encoding="utf-8-sig") as f:
                    content = f.read()
                files_dict[relpath] = content
            except Exception as e:
                print(f"Warning: Could not read file {filepath}: {e}")

    return {"files": files_dict}

def crawl_github_files(
    repo_url,
    token=None,
    max_file_size: int = 1 * 1024 * 1024,
    use_relative_paths: bool = False,
    include_patterns: Union[str, Set[str]] = None,
    exclude_patterns: Union[str, Set[str]] = None
):
    """
    Crawl files from a GitHub repository via GitHub API.

    Args:
        repo_url: GitHub repository URL (e.g., https://github.com/owner/repo)
        token: GitHub personal access token (optional but recommended for rate limits)
        max_file_size: Maximum file size in bytes (default: 1MB)
        use_relative_paths: Whether to use relative paths (default: False)
        include_patterns: Pattern(s) for files to include (e.g., {"*.py", "*.js"})
        exclude_patterns: Pattern(s) for files to exclude (e.g., {"tests/*"})

    Returns:
        dict: {
            "files": {filepath: content},
            "stats": {
                "downloaded_count": int,
                "skipped_count": int,
                "skipped_files": [(path, size), ...],
                "base_path": str,
                "include_patterns": set,
                "exclude_patterns": set
            }
        }

    Environment Variables:
        GITHUB_TOKEN: Personal access token for private repos and higher rate limits

    Example:
        files = crawl_github_files(
            "https://github.com/fastapi/fastapi",
            token=os.getenv("GITHUB_TOKEN"),
            include_patterns={"*.py", "*.md"},
            max_file_size=500000
        )
    """
    if include_patterns and isinstance(include_patterns, str):
        include_patterns = {include_patterns}
    if exclude_patterns and isinstance(exclude_patterns, str):
        exclude_patterns = {exclude_patterns}

    def should_include_file(file_path: str, file_name: str) -> bool:
        if not include_patterns:
            include_file = True
        else:
            include_file = any(fnmatch.fnmatch(file_name, pattern) for pattern in include_patterns)

        if exclude_patterns and include_file:
            exclude_file = any(fnmatch.fnmatch(file_path, pattern) for pattern in exclude_patterns)
            return not exclude_file

        return include_file

    parsed_url = urlparse(repo_url)
    path_parts = parsed_url.path.strip('/').split('/')

    if len(path_parts) < 2:
        raise ValueError(f"Invalid GitHub URL: {repo_url}")

    owner = path_parts[0]
    repo = path_parts[1]

    headers = {"Accept": "application/vnd.github.v3+json"}
    if token:
        headers["Authorization"] = f"token {token}"

    ref = None
    specific_path = ""

    files = {}
    skipped_files = []

    def fetch_contents(path):
        url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"
        params = {"ref": ref} if ref else {}

        response = requests.get(url, headers=headers, params=params)

        if response.status_code == 403 and 'rate limit exceeded' in response.text.lower():
            reset_time = int(response.headers.get('X-RateLimit-Reset', 0))
            wait_time = max(reset_time - time.time(), 0) + 1
            print(f"Rate limit exceeded. Waiting for {wait_time:.0f} seconds...")
            time.sleep(wait_time)
            return fetch_contents(path)

        if response.status_code != 200:
            print(f"Error fetching {path}: {response.status_code}")
            return

        contents = response.json()

        if not isinstance(contents, list):
            contents = [contents]

        for item in contents:
            item_path = item["path"]

            if use_relative_paths and specific_path:
                if item_path.startswith(specific_path):
                    rel_path = item_path[len(specific_path):].lstrip('/')
                else:
                    rel_path = item_path
            else:
                rel_path = item_path

            if item["type"] == "file":
                if not should_include_file(rel_path, item["name"]):
                    continue

                file_size = item.get("size", 0)
                if file_size > max_file_size:
                    skipped_files.append((item_path, file_size))
                    continue

                if "download_url" in item and item["download_url"]:
                    file_response = requests.get(item["download_url"], headers=headers)

                    if file_response.status_code == 200:
                        files[rel_path] = file_response.text
                        print(f"Downloaded: {rel_path} ({file_size} bytes)")

            elif item["type"] == "dir":
                fetch_contents(item_path)

    fetch_contents(specific_path)

    return {
        "files": files,
        "stats": {
            "downloaded_count": len(files),
            "skipped_count": len(skipped_files),
            "skipped_files": skipped_files,
            "base_path": specific_path if use_relative_paths else None,
            "include_patterns": include_patterns,
            "exclude_patterns": exclude_patterns
        }
    }

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_content_for_indices(files_data, indices, max_chars_per_file=6000):
    """
    Extract and truncate file content for specific indices.

    Args:
        files_data: List of (path, content) tuples
        indices: List of indices to extract
        max_chars_per_file: Maximum characters per file, larger files are truncated (default: 6000)

    Returns:
        dict: {"index # path": content} mapping with truncated content for large files

    Note:
        Large files are truncated by keeping first half and last half with ellipsis in middle
    """
    content_map = {}
    for i in indices:
        if 0 <= i < len(files_data):
            path, content = files_data[i]
            if len(content) > max_chars_per_file:
                half_limit = max_chars_per_file // 2
                truncated_content = (
                    content[:half_limit] +
                    f"\n\n... [Content truncated - showing first {half_limit} and last {half_limit} chars of {len(content)} total] ...\n\n" +
                    content[-half_limit:]
                )
            else:
                truncated_content = content
            content_map[f"{i} # {path}"] = truncated_content
    return content_map

# ============================================================================
# CORE PROCESSING FUNCTIONS
# ============================================================================

def fetch_repo(config: Dict[str, Any]) -> List[Tuple[str, str]]:
    """
    Fetch repository files from GitHub or local directory.

    Args:
        config: Configuration dictionary containing:
            - repo_url: GitHub URL (if analyzing remote repo)
            - local_dir: Local directory path (if analyzing local code)
            - github_token: GitHub token for API access
            - include_patterns: Set of file patterns to include
            - exclude_patterns: Set of file patterns to exclude
            - max_file_size: Maximum file size in bytes

    Returns:
        List of (filepath, content) tuples

    Raises:
        ValueError: If no files are fetched

    Example:
        config = {
            "repo_url": "https://github.com/user/repo",
            "include_patterns": {"*.py"},
            "exclude_patterns": {"tests/*"},
            "max_file_size": 100000
        }
        files = fetch_repo(config)
    """
    repo_url = config.get("repo_url")
    local_dir = config.get("local_dir")

    if repo_url:
        print(f"Crawling repository: {repo_url}...")
        result = crawl_github_files(
            repo_url=repo_url,
            token=config.get("github_token"),
            include_patterns=config["include_patterns"],
            exclude_patterns=config["exclude_patterns"],
            max_file_size=config["max_file_size"],
            use_relative_paths=True,
        )
    else:
        print(f"Crawling directory: {local_dir}...")
        result = crawl_local_files(
            directory=local_dir,
            include_patterns=config["include_patterns"],
            exclude_patterns=config["exclude_patterns"],
            max_file_size=config["max_file_size"],
            use_relative_paths=True
        )

    files_list = list(result.get("files", {}).items())
    if len(files_list) == 0:
        raise ValueError("Failed to fetch files")
    print(f"Fetched {len(files_list)} files.")
    return files_list

def identify_abstractions(files_data, config):
    """
    Identify core abstractions/concepts in the codebase using LLM analysis.

    Args:
        files_data: List of (filepath, content) tuples
        config: Configuration dict containing:
            - project_name: Name of the project
            - max_abstraction_num: Max number of abstractions to identify (5-10)
            - use_cache: Whether to cache LLM responses
            - llm_provider: LLM provider to use (gemini/openrouter)

    Returns:
        List of abstraction dicts:
        [
            {
                "name": "Core Concept Name",
                "description": "Beginner-friendly explanation with analogy",
                "files": [0, 3, 7]  # Relevant file indices
            },
            ...
        ]

    Process:
        1. Creates context from all files (truncated for large files)
        2. Sends to LLM with prompt to identify 5-10 core abstractions
        3. Validates YAML response and file indices
        4. Returns structured abstraction data
    """
    print(f"Identifying abstractions using LLM ({config['llm_provider']})...")

    os.environ["LLM_PROVIDER"] = config["llm_provider"]

    def create_llm_context(files_data, max_chars_per_file=4000):
        context = ""
        file_info = []
        for i, (path, content) in enumerate(files_data):
            if len(content) > max_chars_per_file:
                half_limit = max_chars_per_file // 2
                truncated_content = (
                    content[:half_limit] +
                    f"\n... [Truncated - showing first {half_limit} and last {half_limit} chars of {len(content)} total] ...\n" +
                    content[-half_limit:]
                )
            else:
                truncated_content = content

            entry = f"--- File Index {i}: {path} ---\n{truncated_content}\n\n"
            context += entry
            file_info.append((i, path))

        return context, file_info

    context, file_info = create_llm_context(files_data)
    file_listing_for_prompt = "\n".join([f"- {idx} # {path}" for idx, path in file_info])

    prompt = f"""
For the project `{config['project_name']}`:

Codebase Context:
{context}

Analyze the codebase context.
Identify the top 5-{config['max_abstraction_num']} core most important abstractions to help those new to the codebase.

For each abstraction, provide:
1. A concise `name`.
2. A beginner-friendly `description` explaining what it is with a simple analogy, in around 100 words.
3. A list of relevant `file_indices` (integers) using the format `idx # path/comment`.

List of file indices and paths present in the context:
{file_listing_for_prompt}

Format the output as a YAML list of dictionaries:

```yaml
- name: |
    Query Processing
  description: |
    Explains what the abstraction does.
    It's like a central dispatcher routing requests.
  file_indices:
    - 0 # path/to/file1.py
    - 3 # path/to/related.py
```"""

    response = call_llm(prompt, use_cache=config['use_cache'])

    yaml_str = response.strip().split("```yaml")[1].split("```")[0].strip()
    abstractions = yaml.safe_load(yaml_str)

    validated_abstractions = []
    for item in abstractions:
        validated_indices = []
        for idx_entry in item["file_indices"]:
            if isinstance(idx_entry, int):
                idx = idx_entry
            elif isinstance(idx_entry, str) and "#" in idx_entry:
                idx = int(idx_entry.split("#")[0].strip())
            else:
                idx = int(str(idx_entry).strip())
            validated_indices.append(idx)

        validated_abstractions.append({
            "name": item["name"],
            "description": item["description"],
            "files": sorted(list(set(validated_indices)))
        })

    print(f"Identified {len(validated_abstractions)} abstractions.")
    return validated_abstractions

def analyze_relationships(abstractions, files_data, config):
    """
    Analyze relationships and connections between identified abstractions.

    Args:
        abstractions: List of abstraction dicts from identify_abstractions()
        files_data: List of (filepath, content) tuples
        config: Configuration dict with project_name, use_cache, llm_provider

    Returns:
        Dict with:
        {
            "summary": "High-level project summary with markdown formatting",
            "details": [
                {
                    "from": 0,  # Source abstraction index
                    "to": 2,    # Target abstraction index
                    "label": "Manages"  # Relationship description
                },
                ...
            ]
        }

    Process:
        1. Creates context with abstractions and relevant file snippets
        2. LLM generates project summary and relationship graph
        3. Validates that every abstraction appears in at least one relationship
        4. Returns structured relationship data for Mermaid diagram generation
    """
    print(f"Analyzing relationships using LLM ({config['llm_provider']})...")

    os.environ["LLM_PROVIDER"] = config["llm_provider"]

    context = "Identified Abstractions:\n"
    all_relevant_indices = set()
    abstraction_info_for_prompt = []

    for i, abstr in enumerate(abstractions):
        file_indices_str = ", ".join(map(str, abstr["files"]))
        info_line = f"- Index {i}: {abstr['name']} (Relevant file indices: [{file_indices_str}])\n  Description: {abstr['description']}"
        context += info_line + "\n"
        abstraction_info_for_prompt.append(f"{i} # {abstr['name']}")
        all_relevant_indices.update(abstr["files"])

    context += "\nRelevant File Snippets (Referenced by Index and Path):\n"
    relevant_files_content_map = get_content_for_indices(files_data, sorted(list(all_relevant_indices)), max_chars_per_file=3000)
    file_context_str = "\n\n".join(f"--- File: {idx_path} ---\n{content}" for idx_path, content in relevant_files_content_map.items())
    context += file_context_str

    abstraction_listing = "\n".join(abstraction_info_for_prompt)
    num_abstractions = len(abstractions)

    prompt = f"""
Based on the following abstractions and relevant code snippets from the project `{config['project_name']}`:

List of Abstraction Indices and Names:
{abstraction_listing}

Context (Abstractions, Descriptions, Code):
{context}

Please provide:
1. A high-level `summary` of the project's main purpose and functionality in a few beginner-friendly sentences. Use markdown formatting with **bold** and *italic* text to highlight important concepts.
2. A list (`relationships`) describing the key interactions between these abstractions. For each relationship, specify:
    - `from_abstraction`: Index of the source abstraction (e.g., `0 # AbstractionName1`)
    - `to_abstraction`: Index of the target abstraction (e.g., `1 # AbstractionName2`)
    - `label`: A brief label for the interaction **in just a few words** (e.g., "Manages", "Inherits", "Uses").

IMPORTANT: Make sure EVERY abstraction is involved in at least ONE relationship (either as source or target).

Format the output as YAML:

```yaml
summary: |
  A brief, simple explanation of the project.
relationships:
  - from_abstraction: 0 # AbstractionName1
    to_abstraction: 1 # AbstractionName2
    label: "Manages"
```"""

    response = call_llm(prompt, use_cache=config['use_cache'])

    yaml_str = response.strip().split("```yaml")[1].split("```")[0].strip()
    relationships_data = yaml.safe_load(yaml_str)

    validated_relationships = []
    for rel in relationships_data["relationships"]:
        from_idx = int(str(rel["from_abstraction"]).split("#")[0].strip())
        to_idx = int(str(rel["to_abstraction"]).split("#")[0].strip())
        validated_relationships.append({
            "from": from_idx,
            "to": to_idx,
            "label": rel["label"],
        })

    print("Generated project summary and relationship details.")
    return {
        "summary": relationships_data["summary"],
        "details": validated_relationships,
    }

def order_chapters(abstractions, relationships, config):
    """Determine optimal chapter order"""
    print("Determining chapter order using LLM...")

    abstraction_info_for_prompt = [f"- {i} # {a['name']}" for i, a in enumerate(abstractions)]
    abstraction_listing = "\n".join(abstraction_info_for_prompt)

    context = f"Project Summary:\n{relationships['summary']}\n\n"
    context += "Relationships (Indices refer to abstractions above):\n"
    for rel in relationships["details"]:
        from_name = abstractions[rel["from"]]["name"]
        to_name = abstractions[rel["to"]]["name"]
        context += f"- From {rel['from']} ({from_name}) to {rel['to']} ({to_name}): {rel['label']}\n"

    prompt = f"""
Given the following project abstractions and their relationships for the project `{config['project_name']}`:

Abstractions (Index # Name):
{abstraction_listing}

Context about relationships and project summary:
{context}

If you are going to make a tutorial for `{config['project_name']}`, what is the best order to explain these abstractions, from first to last?

Output the ordered list of abstraction indices, including the name in a comment for clarity. Use the format `idx # AbstractionName`.

```yaml
- 2 # FoundationalConcept
- 0 # CoreClassA
```"""

    response = call_llm(prompt, use_cache=config['use_cache'])

    yaml_str = response.strip().split("```yaml")[1].split("```")[0].strip()
    ordered_indices_raw = yaml.safe_load(yaml_str)

    ordered_indices = []
    for entry in ordered_indices_raw:
        if isinstance(entry, int):
            idx = entry
        elif isinstance(entry, str) and "#" in entry:
            idx = int(entry.split("#")[0].strip())
        else:
            idx = int(str(entry).strip())
        ordered_indices.append(idx)

    print(f"Determined chapter order (indices): {ordered_indices}")
    return ordered_indices

def write_chapters(chapter_order, abstractions, files_data, config):
    """Write individual chapter content"""
    chapters = []
    chapters_written_so_far = []

    all_chapters = []
    chapter_filenames = {}

    for i, abstraction_index in enumerate(chapter_order):
        chapter_num = i + 1
        chapter_name = abstractions[abstraction_index]["name"]
        safe_name = "".join(c if c.isalnum() else "_" for c in chapter_name).lower()
        filename = f"{i+1:02d}_{safe_name}.md"
        all_chapters.append(f"{chapter_num}. [{chapter_name}]({filename})")
        chapter_filenames[abstraction_index] = {
            "num": chapter_num,
            "name": chapter_name,
            "filename": filename,
        }

    full_chapter_listing = "\n".join(all_chapters)

    for i, abstraction_index in enumerate(chapter_order):
        abstraction_details = abstractions[abstraction_index]
        abstraction_name = abstraction_details["name"]
        abstraction_description = abstraction_details["description"]
        chapter_num = i + 1

        print(f"Writing chapter {chapter_num} for: {abstraction_name} using LLM...")

        related_file_indices = abstraction_details.get("files", [])
        related_files_content_map = get_content_for_indices(files_data, related_file_indices, max_chars_per_file=6000)

        file_context_str = "\n\n".join(
            f"--- File: {idx_path.split('# ')[1] if '# ' in idx_path else idx_path} ---\n{content}"
            for idx_path, content in related_files_content_map.items()
        )

        previous_chapters_summary = "\n---\n".join(chapters_written_so_far)

        prompt = f"""
Write a very beginner-friendly tutorial chapter (in Markdown format) for the project `{config['project_name']}` about the concept: "{abstraction_name}". This is Chapter {chapter_num}.

Concept Details:
- Name: {abstraction_name}
- Description:
{abstraction_description}

Complete Tutorial Structure:
{full_chapter_listing}

Context from previous chapters:
{previous_chapters_summary if previous_chapters_summary else "This is the first chapter."}

Relevant Code Snippets:
{file_context_str if file_context_str else "No specific code snippets provided."}

Instructions:
- Start with heading: `# Chapter {chapter_num}: {abstraction_name}`
- Begin with high-level motivation explaining what problem this solves
- Break complex abstractions into key concepts
- Explain with examples, inputs/outputs
- Keep code blocks under 10 lines
- Use mermaid diagrams for complex concepts
- Use analogies and examples
- End with summary and transition to next chapter

Now, provide the Markdown content:
"""

        chapter_content = call_llm(prompt, use_cache=config['use_cache'])

        actual_heading = f"# Chapter {chapter_num}: {abstraction_name}"
        if not chapter_content.strip().startswith(f"# Chapter {chapter_num}"):
            lines = chapter_content.strip().split("\n")
            if lines and lines[0].strip().startswith("#"):
                lines[0] = actual_heading
                chapter_content = "\n".join(lines)
            else:
                chapter_content = f"{actual_heading}\n\n{chapter_content}"

        chapters_written_so_far.append(chapter_content)
        chapters.append(chapter_content)

    print(f"Finished writing {len(chapters)} chapters.")
    return chapters

def combine_tutorial(chapter_order, abstractions, relationships, chapters, config):
    """Combine all chapters into final tutorial"""
    print(f"Combining tutorial...")

    output_path = os.path.join(config.get("output_dir", "output"), config["project_name"])
    os.makedirs(output_path, exist_ok=True)

    # Generate Mermaid diagram
    mermaid_lines = ["flowchart TD"]
    for i, abstr in enumerate(abstractions):
        node_id = f"A{i}"
        sanitized_name = abstr["name"].replace('"', "")
        mermaid_lines.append(f'    {node_id}["{sanitized_name}"]')

    for rel in relationships["details"]:
        from_node_id = f"A{rel['from']}"
        to_node_id = f"A{rel['to']}"
        edge_label = rel["label"].replace('"', "").replace("\n", " ")
        if len(edge_label) > 30:
            edge_label = edge_label[:27] + "..."
        mermaid_lines.append(f'    {from_node_id} -- "{edge_label}" --> {to_node_id}')

    mermaid_diagram = "\n".join(mermaid_lines)

    # Create merged tutorial
    combined_content = f"# Tutorial: {config['project_name']}\n\n"
    combined_content += f"{relationships['summary']}\n\n"
    combined_content += f"**Source Repository:** [{config.get('repo_url', 'Local Directory')}]({config.get('repo_url', '#')})\n\n"
    combined_content += "```mermaid\n" + mermaid_diagram + "\n```\n\n"
    combined_content += "## Table of Contents\n\n"

    for i, abstraction_index in enumerate(chapter_order, 1):
        chapter_name = abstractions[abstraction_index]["name"]
        anchor = f"chapter-{i}-{chapter_name.lower().replace(' ', '-').replace(':', '').replace(',', '')}"
        anchor = "".join(c for c in anchor if c.isalnum() or c == "-")
        combined_content += f"{i}. [{chapter_name}](#{anchor})\n"

    combined_content += "\n---\n\n"

    for chapter_content in chapters:
        chapter_content = chapter_content.strip()
        if "Generated by [AI Codebase Knowledge Builder]" in chapter_content:
            chapter_content = chapter_content.split("---\n\nGenerated by [AI Codebase Knowledge Builder]")[0].rstrip()
        combined_content += chapter_content + "\n\n---\n\n"

    combined_content += "Generated by [AI Codebase Knowledge Builder](https://github.com/The-Pocket/Tutorial-Codebase-Knowledge)\n"

    single_file_name = f"{config['project_name']}_tutorial.md"
    single_file_path = os.path.join(output_path, single_file_name)

    with open(single_file_path, "w", encoding="utf-8") as f:
        f.write(combined_content)

    print(f"Created {single_file_name} in {output_path}")

    # Move to docs
    docs_dir = os.path.join("docs", config["project_name"])
    os.makedirs("docs", exist_ok=True)

    if os.path.exists(docs_dir):
        import shutil
        shutil.rmtree(docs_dir)

    import shutil
    shutil.move(output_path, docs_dir)

    print(f"\nTutorial complete! Output: {docs_dir}/{single_file_name}")
    return docs_dir

# ============================================================================
# MAIN EXECUTION
# ============================================================================

DEFAULT_INCLUDE_PATTERNS = {
    "*.py", "*.js", "*.jsx", "*.ts", "*.tsx", "*.go", "*.java", "*.pyi", "*.pyx",
    "*.c", "*.cc", "*.cpp", "*.h", "*.md", "*.rst", "*Dockerfile",
    "*Makefile", "*.yaml", "*.yml",
}

DEFAULT_EXCLUDE_PATTERNS = {
    "assets/*", "data/*", "images/*", "public/*", "static/*", "temp/*",
    "*docs/*", "*venv/*", "*.venv/*", "*test*", "*tests/*", "*examples/*",
    "v1/*", "*dist/*", "*build/*", "*experimental/*", "*deprecated/*",
    "*misc/*", "*legacy/*", ".git/*", ".github/*", ".next/*", ".vscode/*",
    "*obj/*", "*bin/*", "*node_modules/*", "*.log"
}

def main():
    parser = argparse.ArgumentParser(description="Generate a tutorial for a GitHub codebase or local directory.")

    source_group = parser.add_mutually_exclusive_group(required=True)
    source_group.add_argument("--repo", help="URL of the public GitHub repository.")
    source_group.add_argument("--dir", help="Path to local directory.")

    parser.add_argument("-n", "--name", help="Project name (optional, derived from repo/directory if omitted).")
    parser.add_argument("-t", "--token", help="GitHub personal access token.")
    parser.add_argument("-o", "--output", default="output", help="Base directory for output (default: ./output).")
    parser.add_argument("-i", "--include", nargs="+", help="Include file patterns.")
    parser.add_argument("-e", "--exclude", nargs="+", help="Exclude file patterns.")
    parser.add_argument("-s", "--max-size", type=int, default=100000, help="Maximum file size in bytes.")
    parser.add_argument("--language", default="english", help="Language for the generated tutorial.")
    parser.add_argument("--no-cache", action="store_true", help="Disable LLM response caching.")
    parser.add_argument("--max-abstractions", type=int, default=10, help="Maximum number of abstractions.")
    parser.add_argument("--llm-provider", default=os.environ.get("LLM_PROVIDER", "openrouter"),
                       choices=["openrouter", "gemini"],
                       help="LLM provider to use.")

    args = parser.parse_args()

    github_token = None
    if args.repo:
        github_token = args.token or os.environ.get('GITHUB_TOKEN')
        if not github_token:
            print("Warning: No GitHub token provided. You might hit rate limits.")

    project_name = args.name
    if not project_name:
        if args.repo:
            project_name = args.repo.split("/")[-1].replace(".git", "")
        else:
            project_name = os.path.basename(os.path.abspath(args.dir))

    config = {
        "repo_url": args.repo,
        "local_dir": args.dir,
        "project_name": project_name,
        "github_token": github_token,
        "output_dir": args.output,
        "include_patterns": set(args.include) if args.include else DEFAULT_INCLUDE_PATTERNS,
        "exclude_patterns": set(args.exclude) if args.exclude else DEFAULT_EXCLUDE_PATTERNS,
        "max_file_size": args.max_size,
        "language": args.language,
        "use_cache": not args.no_cache,
        "max_abstraction_num": args.max_abstractions,
        "llm_provider": args.llm_provider,
    }

    print(f"Starting tutorial generation for: {args.repo or args.dir}")
    print(f"LLM caching: {'Disabled' if args.no_cache else 'Enabled'}")

    # Execute workflow
    files = fetch_repo(config)
    abstractions = identify_abstractions(files, config)
    relationships = analyze_relationships(abstractions, files, config)
    chapter_order = order_chapters(abstractions, relationships, config)
    chapters = write_chapters(chapter_order, abstractions, files, config)
    final_output = combine_tutorial(chapter_order, abstractions, relationships, chapters, config)

if __name__ == "__main__":
    main()
