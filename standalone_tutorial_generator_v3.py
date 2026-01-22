#!/usr/bin/env python3
"""
Standalone Tutorial Generator v3
================================
A single-file codebase tutorial generator that consolidates logic from:
- nodes.py (workflow nodes and prompts)
- utils/call_llm.py (LLM calling with caching)
- utils/crawl_github_files.py (GitHub repository crawler)

Default LLM: gemini-flash via LiteLLM (CAPI)

Usage:
    python standalone_tutorial_generator_v3.py https://github.com/owner/repo
    python standalone_tutorial_generator_v3.py https://github.com/owner/repo --max-abstractions 8
    python standalone_tutorial_generator_v3.py https://github.com/owner/repo --language Chinese
    python standalone_tutorial_generator_v3.py https://github.com/owner/repo --provider openrouter
"""

import os
import re
import sys
import json
import yaml
import base64
import logging
import hashlib
import argparse
import requests
import fnmatch
import tempfile
import time
from datetime import datetime
from urllib.parse import urlparse
from typing import Union, Set, List, Dict, Any, Optional, Tuple

# ============================================================================
# CONFIGURATION
# ============================================================================

# Default LLM settings
DEFAULT_PROVIDER = "litellm"
DEFAULT_LITELLM_BASE_URL = "https://litellm.genr8ive.ai/v1"
DEFAULT_LITELLM_API_KEY = "sk-litellm-sai-local"
DEFAULT_LITELLM_MODEL = "gemini-flash"

# File patterns
DEFAULT_INCLUDE_PATTERNS = {
    "*.py", "*.js", "*.jsx", "*.ts", "*.tsx", "*.go", "*.java",
    "*.c", "*.cpp", "*.h", "*.md", "*.rst", "*Dockerfile", "*Makefile",
    "*.yaml", "*.yml"
}
DEFAULT_EXCLUDE_PATTERNS = {
    "*test*", "*tests/*", "*__pycache__/*", "*docs/*", "*venv/*", "*node_modules/*",
    "*build/*", "*dist/*", ".git/*", "*/.git/*", "*.pyc", "*.lock", "*.log",
    "*/.pytest_cache/*", "*/.mypy_cache/*", "*/.ruff_cache/*", "*.min.js", "*.min.css"
}

# Context limits
MAX_CONTEXT_TOKENS = 900000
MAX_CHARS_PER_FILE_IDENTIFY = 4000
MAX_CHARS_PER_FILE_ANALYZE = 3000
MAX_CHARS_PER_FILE_WRITE = 6000

# Large repo handling
MAX_FILES_TO_INCLUDE = 200  # Hard limit on total files
MAX_FILE_SIZE = 512 * 1024  # 512 KB per file (stricter default)
MAX_TOTAL_BYTES = 50 * 1024 * 1024  # 50 MB total across all files

# ============================================================================
# LOGGING SETUP
# ============================================================================

log_directory = os.getenv("LOG_DIR", "logs")
os.makedirs(log_directory, exist_ok=True)
log_file = os.path.join(log_directory, f"llm_calls_{datetime.now().strftime('%Y%m%d')}.log")

logger = logging.getLogger("tutorial_generator")
logger.setLevel(logging.INFO)
logger.propagate = False
file_handler = logging.FileHandler(log_file, encoding='utf-8')
file_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
logger.addHandler(file_handler)

# Console handler for progress
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(logging.Formatter("%(message)s"))
logger.addHandler(console_handler)

# ============================================================================
# LLM UTILITIES
# ============================================================================

CACHE_FILE = "llm_cache.json"


def _count_tokens(text: str) -> int:
    """Estimate token count (rough: ~4 chars per token)"""
    try:
        import tiktoken
        encoding = tiktoken.get_encoding("cl100k_base")
        return len(encoding.encode(text))
    except ImportError:
        return len(text) // 4


def _ensure_prompt_fits_context(prompt: str, max_tokens: int = MAX_CONTEXT_TOKENS) -> str:
    """Ensure prompt fits within context limits by truncating if necessary"""
    token_count = _count_tokens(prompt)

    if token_count <= max_tokens:
        return prompt

    logger.warning(f"Prompt too long ({token_count} tokens), truncating to fit {max_tokens} tokens")

    # Calculate target character count (rough estimate)
    target_chars = int(max_tokens * 3.5)

    if len(prompt) <= target_chars:
        return prompt

    # Keep beginning and end of prompt, truncate middle
    keep_start = target_chars // 3
    keep_end = target_chars // 3

    truncated_prompt = (
        prompt[:keep_start] +
        f"\n\n... [CONTENT TRUNCATED - Original length: {len(prompt)} chars, {token_count} tokens] ...\n\n" +
        prompt[-keep_end:]
    )

    logger.info(f"Truncated prompt from {len(prompt)} to {len(truncated_prompt)} characters")
    return truncated_prompt


def _check_cache(prompt: str) -> Optional[str]:
    """Check if response exists in cache"""
    try:
        if os.path.exists(CACHE_FILE):
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
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
        if os.path.exists(CACHE_FILE):
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                cache = json.load(f)

        cache[prompt] = response

        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(cache, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.warning(f"Cache write error: {e}")


def _call_litellm(prompt: str) -> str:
    """Call LiteLLM proxy API (default provider)"""
    base_url = os.getenv("LITELLM_BASE_URL", DEFAULT_LITELLM_BASE_URL)
    api_key = os.getenv("LITELLM_API_KEY", DEFAULT_LITELLM_API_KEY)
    model = os.getenv("LITELLM_MODEL", DEFAULT_LITELLM_MODEL)

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    data = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7
    }

    # Construct endpoint
    if base_url.endswith('/v1'):
        endpoint = f"{base_url}/chat/completions"
    else:
        endpoint = f"{base_url}/v1/chat/completions"

    response = requests.post(endpoint, headers=headers, json=data, timeout=300)

    if response.status_code != 200:
        raise Exception(f"LiteLLM API error: {response.status_code} - {response.text}")

    return response.json()["choices"][0]["message"]["content"]


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
        "model": os.getenv("OPENROUTER_MODEL", "google/gemini-flash"),
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7
    }

    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers=headers,
        json=data,
        timeout=300
    )

    if response.status_code == 400 and "maximum context length" in response.text:
        data["transforms"] = ["middle-out"]
        logger.warning("Prompt too long, retrying with middle-out transform")
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=data,
            timeout=300
        )

    if response.status_code != 200:
        raise Exception(f"OpenRouter API error: {response.status_code} - {response.text}")

    return response.json()["choices"][0]["message"]["content"]


def _call_gemini(prompt: str) -> str:
    """Call Google Gemini API directly"""
    try:
        from google import genai
        client = genai.Client(api_key=os.getenv("GEMINI_API_KEY", os.getenv("GOOGLE_API_KEY")))
        response = client.models.generate_content(
            model="gemini-flash", contents=prompt
        )
        return response.text
    except ImportError:
        raise ImportError("google-genai package required for direct Gemini calls. Install with: pip install google-genai")


def _call_openai(prompt: str) -> str:
    """Call OpenAI API"""
    try:
        from openai import OpenAI
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        response = client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
    except ImportError:
        raise ImportError("openai package required. Install with: pip install openai")


def _call_anthropic(prompt: str) -> str:
    """Call Anthropic Claude API"""
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        response = client.messages.create(
            model=os.getenv("ANTHROPIC_MODEL", "claude-3-haiku-20240307"),
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text
    except ImportError:
        raise ImportError("anthropic package required. Install with: pip install anthropic")


def call_llm(prompt: str, use_cache: bool = True) -> str:
    """
    Call an LLM with the given prompt and return the response.
    Provider determined by LLM_PROVIDER env var (default: litellm).
    """
    # Truncate prompt if too long
    prompt = _ensure_prompt_fits_context(prompt)

    # Log prompt
    logger.info(f"PROMPT: {prompt[:500]}..." if len(prompt) > 500 else f"PROMPT: {prompt}")

    # Check cache
    if use_cache:
        cached = _check_cache(prompt)
        if cached:
            return cached

    # Get provider
    provider = os.getenv("LLM_PROVIDER", DEFAULT_PROVIDER).lower()

    try:
        if provider == "gemini":
            response = _call_gemini(prompt)
        elif provider == "openai":
            response = _call_openai(prompt)
        elif provider == "anthropic":
            response = _call_anthropic(prompt)
        elif provider == "openrouter":
            response = _call_openrouter(prompt)
        elif provider == "litellm":
            response = _call_litellm(prompt)
        else:
            logger.warning(f"Unknown provider: {provider}. Falling back to LiteLLM.")
            response = _call_litellm(prompt)

        # Cache response
        if use_cache:
            _save_to_cache(prompt, response)

        logger.info(f"RESPONSE: {response[:500]}..." if len(response) > 500 else f"RESPONSE: {response}")
        return response

    except Exception as e:
        logger.error(f"Error calling LLM: {e}")
        raise


# ============================================================================
# GITHUB CRAWLER
# ============================================================================

def crawl_github_files(
    repo_url: str,
    token: Optional[str] = None,
    max_file_size: int = None,
    include_patterns: Optional[Set[str]] = None,
    exclude_patterns: Optional[Set[str]] = None,
    max_files: int = MAX_FILES_TO_INCLUDE,
    max_total_bytes: int = MAX_TOTAL_BYTES
) -> Dict[str, Any]:
    """
    Crawl files from a GitHub repository with large-repo handling.

    Args:
        repo_url: GitHub repository URL
        token: GitHub personal access token (optional, but recommended)
        max_file_size: Maximum file size in bytes (default: 512 KB for large repos)
        include_patterns: File patterns to include (default: code files)
        exclude_patterns: File patterns to exclude (default: test/docs/build)
        max_files: Maximum number of files to include (default: 200)
        max_total_bytes: Maximum total bytes across all files (default: 50 MB)

    Returns:
        dict with 'files' (dict of path->content) and 'stats'
    """
    if max_file_size is None:
        max_file_size = MAX_FILE_SIZE
    if include_patterns is None:
        include_patterns = DEFAULT_INCLUDE_PATTERNS
    if exclude_patterns is None:
        exclude_patterns = DEFAULT_EXCLUDE_PATTERNS

    # Convert single pattern to set
    if isinstance(include_patterns, str):
        include_patterns = {include_patterns}
    if isinstance(exclude_patterns, str):
        exclude_patterns = {exclude_patterns}

    def should_include_file(file_path: str, file_name: str) -> bool:
        """Determine if a file should be included based on patterns"""
        if not include_patterns:
            include_file = True
        else:
            include_file = any(fnmatch.fnmatch(file_name, pattern) for pattern in include_patterns)

        if exclude_patterns and include_file:
            exclude_file = any(fnmatch.fnmatch(file_path, pattern) for pattern in exclude_patterns)
            return not exclude_file

        return include_file

    # Handle SSH URLs
    if repo_url.startswith("git@") or repo_url.endswith(".git"):
        try:
            import git
            with tempfile.TemporaryDirectory() as tmpdirname:
                print(f"Cloning SSH repo {repo_url}...")
                repo = git.Repo.clone_from(repo_url, tmpdirname)

                files = {}
                skipped_files = []

                for root, dirs, filenames in os.walk(tmpdirname):
                    for filename in filenames:
                        abs_path = os.path.join(root, filename)
                        rel_path = os.path.relpath(abs_path, tmpdirname)

                        try:
                            file_size = os.path.getsize(abs_path)
                        except OSError:
                            continue

                        if file_size > max_file_size:
                            skipped_files.append((rel_path, file_size))
                            continue

                        if not should_include_file(rel_path, filename):
                            continue

                        try:
                            with open(abs_path, "r", encoding="utf-8-sig") as f:
                                files[rel_path] = f.read()
                            print(f"Added {rel_path} ({file_size} bytes)")
                        except Exception as e:
                            print(f"Failed to read {rel_path}: {e}")

                return {
                    "files": files,
                    "stats": {
                        "downloaded_count": len(files),
                        "skipped_count": len(skipped_files),
                        "source": "ssh_clone"
                    }
                }
        except ImportError:
            raise ImportError("GitPython required for SSH URLs. Install with: pip install gitpython")

    # Parse GitHub URL
    parsed_url = urlparse(repo_url)
    path_parts = parsed_url.path.strip('/').split('/')

    if len(path_parts) < 2:
        raise ValueError(f"Invalid GitHub URL: {repo_url}")

    owner = path_parts[0]
    repo = path_parts[1]

    # Setup headers
    headers = {"Accept": "application/vnd.github.v3+json"}
    if token:
        headers["Authorization"] = f"token {token}"
    elif os.getenv("GITHUB_TOKEN"):
        headers["Authorization"] = f"token {os.getenv('GITHUB_TOKEN')}"

    # Determine ref/branch
    ref = None
    specific_path = ""

    if len(path_parts) > 2 and path_parts[2] == 'tree':
        # URL has branch/commit info
        if len(path_parts) > 3:
            ref = path_parts[3]
            if len(path_parts) > 4:
                specific_path = '/'.join(path_parts[4:])

    files = {}
    skipped_files = []
    total_bytes = 0

    def fetch_contents(path: str):
        """Recursively fetch repository contents with size limits"""
        nonlocal total_bytes

        # Stop if we've reached file count or total byte limit
        if len(files) >= max_files:
            print(f"Reached file limit ({max_files}), stopping fetch")
            return
        if total_bytes >= max_total_bytes:
            print(f"Reached total size limit ({max_total_bytes / 1024 / 1024:.1f} MB), stopping fetch")
            return

        url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"
        params = {"ref": ref} if ref else {}

        response = requests.get(url, headers=headers, params=params, timeout=(30, 30))

        if response.status_code == 403 and 'rate limit exceeded' in response.text.lower():
            reset_time = int(response.headers.get('X-RateLimit-Reset', 0))
            wait_time = max(reset_time - time.time(), 0) + 1
            print(f"Rate limit exceeded. Waiting {wait_time:.0f}s...")
            time.sleep(wait_time)
            return fetch_contents(path)

        if response.status_code == 404:
            print(f"Error 404: Path '{path}' not found")
            return

        if response.status_code != 200:
            print(f"Error fetching {path}: {response.status_code}")
            return

        contents = response.json()
        if not isinstance(contents, list):
            contents = [contents]

        for item in contents:
            # Check limits before processing each item
            if len(files) >= max_files or total_bytes >= max_total_bytes:
                return

            item_path = item["path"]

            if item["type"] == "file":
                if not should_include_file(item_path, item["name"]):
                    continue

                file_size = item.get("size", 0)
                if file_size > max_file_size:
                    skipped_files.append((item_path, file_size))
                    print(f"Skipping {item_path}: size {file_size} exceeds limit ({max_file_size / 1024:.0f} KB)")
                    continue

                # Check if adding this file would exceed total limit
                if total_bytes + file_size > max_total_bytes:
                    skipped_files.append((item_path, file_size))
                    print(f"Skipping {item_path}: would exceed total size limit")
                    continue

                # Download file
                if item.get("download_url"):
                    file_response = requests.get(item["download_url"], headers=headers, timeout=(30, 30))
                    if file_response.status_code == 200:
                        files[item_path] = file_response.text
                        total_bytes += file_size
                        print(f"Downloaded: {item_path} ({file_size} bytes, total: {total_bytes / 1024 / 1024:.1f} MB)")
                    else:
                        print(f"Failed to download {item_path}")
                else:
                    # Fallback to content API
                    content_response = requests.get(item["url"], headers=headers, timeout=(30, 30))
                    if content_response.status_code == 200:
                        content_data = content_response.json()
                        if content_data.get("encoding") == "base64" and "content" in content_data:
                            files[item_path] = base64.b64decode(content_data["content"]).decode('utf-8')
                            total_bytes += file_size
                            print(f"Downloaded: {item_path} (total: {total_bytes / 1024 / 1024:.1f} MB)")

            elif item["type"] == "dir":
                # Check exclusion before recursing
                if exclude_patterns:
                    if any(fnmatch.fnmatch(item_path, p) for p in exclude_patterns):
                        continue
                fetch_contents(item_path)

    fetch_contents(specific_path)

    return {
        "files": files,
        "stats": {
            "downloaded_count": len(files),
            "skipped_count": len(skipped_files),
            "total_bytes": total_bytes,
            "total_mb": round(total_bytes / 1024 / 1024, 2),
            "include_patterns": list(include_patterns) if include_patterns else None,
            "exclude_patterns": list(exclude_patterns) if exclude_patterns else None,
            "limits_applied": {
                "max_files": max_files,
                "max_file_size_kb": round(max_file_size / 1024, 1),
                "max_total_mb": round(max_total_bytes / 1024 / 1024, 1)
            }
        }
    }


# ============================================================================
# TUTORIAL GENERATION WORKFLOW
# ============================================================================

def get_content_for_indices(
    files_data: List[Tuple[str, str]],
    indices: List[int],
    max_chars_per_file: int = 6000
) -> Dict[str, str]:
    """Get content for specific file indices with smart truncation"""
    content_map = {}
    for i in indices:
        if 0 <= i < len(files_data):
            path, content = files_data[i]
            if len(content) > max_chars_per_file:
                half = max_chars_per_file // 2
                truncated = (
                    content[:half] +
                    f"\n\n... [Truncated - {len(content)} chars total] ...\n\n" +
                    content[-half:]
                )
            else:
                truncated = content
            content_map[f"{i} # {path}"] = truncated
    return content_map


def create_llm_context(
    files_data: List[Tuple[str, str]],
    max_chars_per_file: int = 4000
) -> Tuple[str, List[Tuple[int, str]]]:
    """Create context from files for LLM analysis"""
    context = ""
    file_info = []
    for i, (path, content) in enumerate(files_data):
        if len(content) > max_chars_per_file:
            half = max_chars_per_file // 2
            truncated = (
                content[:half] +
                f"\n... [Truncated - {len(content)} chars total] ...\n" +
                content[-half:]
            )
        else:
            truncated = content

        entry = f"--- File Index {i}: {path} ---\n{truncated}\n\n"
        context += entry
        file_info.append((i, path))

    return context, file_info


def identify_abstractions(
    files_data: List[Tuple[str, str]],
    project_name: str,
    language: str = "english",
    max_abstraction_num: int = 10,
    use_cache: bool = True
) -> List[Dict[str, Any]]:
    """Identify core abstractions in the codebase"""
    print(f"\n{'='*60}")
    print("STEP 1: Identifying Core Abstractions")
    print(f"{'='*60}")

    context, file_info = create_llm_context(files_data, MAX_CHARS_PER_FILE_IDENTIFY)
    file_listing = "\n".join([f"- {idx} # {path}" for idx, path in file_info])

    # Language instructions
    language_instruction = ""
    name_hint = ""
    desc_hint = ""
    if language.lower() != "english":
        lang_cap = language.capitalize()
        language_instruction = f"IMPORTANT: Generate the `name` and `description` for each abstraction in **{lang_cap}** language. Do NOT use English for these fields.\n\n"
        name_hint = f" (value in {lang_cap})"
        desc_hint = f" (value in {lang_cap})"

    prompt = f"""
For the project `{project_name}`:

Codebase Context:
{context}

{language_instruction}Analyze the codebase context.
Identify the top 5-{max_abstraction_num} core most important abstractions to help those new to the codebase.

For each abstraction, provide:
1. A concise `name`{name_hint}.
2. A beginner-friendly `description` explaining what it is with a simple analogy, in around 100 words{desc_hint}.
3. A list of relevant `file_indices` (integers) using the format `idx # path/comment`.

List of file indices and paths present in the context:
{file_listing}

Format the output as a YAML list of dictionaries:

```yaml
- name: |
    Query Processing{name_hint}
  description: |
    Explains what the abstraction does.
    It's like a central dispatcher routing requests.{desc_hint}
  file_indices:
    - 0 # path/to/file1.py
    - 3 # path/to/related.py
- name: |
    Query Optimization{name_hint}
  description: |
    Another core concept, similar to a blueprint for objects.{desc_hint}
  file_indices:
    - 5 # path/to/another.js
# ... up to {max_abstraction_num} abstractions
```"""

    response = call_llm(prompt, use_cache=use_cache)

    # Parse and validate - Robust YAML extraction
    response_clean = response.strip()
    if "```yaml" in response_clean:
        yaml_str = response_clean.split("```yaml")[1].split("```")[0].strip()
    elif "```yml" in response_clean:
        yaml_str = response_clean.split("```yml")[1].split("```")[0].strip()
    elif "```" in response_clean:
        # Fallback for generic code blocks
        parts = response_clean.split("```")
        if len(parts) >= 2:
            yaml_str = parts[1].strip()
        else:
            yaml_str = response_clean
    else:
        # Assume raw YAML if no blocks
        yaml_str = response_clean

    abstractions = yaml.safe_load(yaml_str)

    if not isinstance(abstractions, list):
        raise ValueError("LLM output is not a list")

    validated = []
    file_count = len(files_data)

    for item in abstractions:
        if not isinstance(item, dict) or not all(k in item for k in ["name", "description", "file_indices"]):
            raise ValueError(f"Missing keys in abstraction: {item}")

        # Validate indices
        indices = []
        for idx_entry in item["file_indices"]:
            if isinstance(idx_entry, int):
                idx = idx_entry
            elif isinstance(idx_entry, str) and "#" in idx_entry:
                idx = int(idx_entry.split("#")[0].strip())
            else:
                idx = int(str(idx_entry).strip())

            if 0 <= idx < file_count:
                indices.append(idx)

        validated.append({
            "name": item["name"].strip(),
            "description": item["description"].strip(),
            "files": sorted(list(set(indices)))
        })

    print(f"Identified {len(validated)} abstractions.")
    return validated


def analyze_relationships(
    abstractions: List[Dict[str, Any]],
    files_data: List[Tuple[str, str]],
    project_name: str,
    language: str = "english",
    use_cache: bool = True
) -> Dict[str, Any]:
    """Analyze relationships between abstractions"""
    print(f"\n{'='*60}")
    print("STEP 2: Analyzing Relationships")
    print(f"{'='*60}")

    num_abstractions = len(abstractions)

    # Build context
    context = "Identified Abstractions:\n"
    abstraction_listing = []
    all_indices = set()

    for i, abstr in enumerate(abstractions):
        indices_str = ", ".join(map(str, abstr["files"]))
        context += f"- Index {i}: {abstr['name']} (Files: [{indices_str}])\n  Description: {abstr['description']}\n"
        abstraction_listing.append(f"{i} # {abstr['name']}")
        all_indices.update(abstr["files"])

    # Add file snippets
    context += "\nRelevant File Snippets:\n"
    content_map = get_content_for_indices(files_data, sorted(list(all_indices)), MAX_CHARS_PER_FILE_ANALYZE)
    for idx_path, content in content_map.items():
        context += f"--- File: {idx_path} ---\n{content}\n\n"

    # Language instructions
    language_instruction = ""
    lang_hint = ""
    list_note = ""
    if language.lower() != "english":
        lang_cap = language.capitalize()
        language_instruction = f"IMPORTANT: Generate the `summary` and relationship `label` fields in **{lang_cap}** language. Do NOT use English for these fields.\n\n"
        lang_hint = f" (in {lang_cap})"
        list_note = f" (Names might be in {lang_cap})"

    prompt = f"""
Based on the following abstractions and relevant code snippets from the project `{project_name}`:

List of Abstraction Indices and Names{list_note}:
{chr(10).join(abstraction_listing)}

Context (Abstractions, Descriptions, Code):
{context}

{language_instruction}Please provide:
1. A high-level `summary` of the project's main purpose and functionality in a few beginner-friendly sentences{lang_hint}. Use markdown formatting with **bold** and *italic* text to highlight important concepts.
2. A list (`relationships`) describing the key interactions between these abstractions. For each relationship, specify:
    - `from_abstraction`: Index of the source abstraction (e.g., `0 # AbstractionName1`)
    - `to_abstraction`: Index of the target abstraction (e.g., `1 # AbstractionName2`)
    - `label`: A brief label for the interaction **in just a few words**{lang_hint} (e.g., "Manages", "Inherits", "Uses").
    Ideally the relationship should be backed by one abstraction calling or passing parameters to another.
    Simplify the relationship and exclude those non-important ones.

IMPORTANT: Make sure EVERY abstraction is involved in at least ONE relationship (either as source or target). Each abstraction index must appear at least once across all relationships.

Format the output as YAML:

```yaml
summary: |
  A brief, simple explanation of the project{lang_hint}.
  Can span multiple lines with **bold** and *italic* for emphasis.
relationships:
  - from_abstraction: 0 # AbstractionName1
    to_abstraction: 1 # AbstractionName2
    label: "Manages"{lang_hint}
  - from_abstraction: 2 # AbstractionName3
    to_abstraction: 0 # AbstractionName1
    label: "Provides config"{lang_hint}
  # ... other relationships
```

Now, provide the YAML output:
"""

    response = call_llm(prompt, use_cache=use_cache)

    # Parse and validate - Robust YAML extraction
    response_clean = response.strip()
    if "```yaml" in response_clean:
        yaml_str = response_clean.split("```yaml")[1].split("```")[0].strip()
    elif "```yml" in response_clean:
        yaml_str = response_clean.split("```yml")[1].split("```")[0].strip()
    elif "```" in response_clean:
        # Fallback for generic code blocks
        parts = response_clean.split("```")
        if len(parts) >= 2:
            yaml_str = parts[1].strip()
        else:
            yaml_str = response_clean
    else:
        # Assume raw YAML if no blocks
        yaml_str = response_clean

    data = yaml.safe_load(yaml_str)

    if not isinstance(data, dict) or "summary" not in data or "relationships" not in data:
        raise ValueError("Invalid relationship output format")

    validated_rels = []
    for rel in data["relationships"]:
        from_idx = int(str(rel["from_abstraction"]).split("#")[0].strip())
        to_idx = int(str(rel["to_abstraction"]).split("#")[0].strip())
        if 0 <= from_idx < num_abstractions and 0 <= to_idx < num_abstractions:
            validated_rels.append({
                "from": from_idx,
                "to": to_idx,
                "label": rel["label"]
            })

    print(f"Analyzed {len(validated_rels)} relationships.")
    return {
        "summary": data["summary"],
        "details": validated_rels
    }


def order_chapters(
    abstractions: List[Dict[str, Any]],
    relationships: Dict[str, Any],
    project_name: str,
    language: str = "english",
    use_cache: bool = True
) -> List[int]:
    """Determine optimal chapter order"""
    print(f"\n{'='*60}")
    print("STEP 3: Ordering Chapters")
    print(f"{'='*60}")

    num_abstractions = len(abstractions)

    # Prepare context
    abstraction_listing = "\n".join([f"- {i} # {a['name']}" for i, a in enumerate(abstractions)])

    context = f"Project Summary:\n{relationships['summary']}\n\n"
    context += "Relationships:\n"
    for rel in relationships["details"]:
        from_name = abstractions[rel["from"]]["name"]
        to_name = abstractions[rel["to"]]["name"]
        context += f"- From {rel['from']} ({from_name}) to {rel['to']} ({to_name}): {rel['label']}\n"

    list_note = ""
    if language.lower() != "english":
        list_note = f" (Names might be in {language.capitalize()})"

    prompt = f"""
Given the following project abstractions and their relationships for the project `{project_name}`:

Abstractions (Index # Name){list_note}:
{abstraction_listing}

Context about relationships and project summary:
{context}

If you are going to make a tutorial for `{project_name}`, what is the best order to explain these abstractions, from first to last?
Ideally, first explain those that are the most important or foundational, perhaps user-facing concepts or entry points. Then move to more detailed, lower-level implementation details or supporting concepts.

Output the ordered list of abstraction indices, including the name in a comment for clarity. Use the format `idx # AbstractionName`.

```yaml
- 2 # FoundationalConcept
- 0 # CoreClassA
- 1 # CoreClassB (uses CoreClassA)
- ...
```

Now, provide the YAML output:
"""

    response = call_llm(prompt, use_cache=use_cache)

    # Parse - Robust YAML extraction
    response_clean = response.strip()
    if "```yaml" in response_clean:
        yaml_str = response_clean.split("```yaml")[1].split("```")[0].strip()
    elif "```yml" in response_clean:
        yaml_str = response_clean.split("```yml")[1].split("```")[0].strip()
    elif "```" in response_clean:
        # Fallback for generic code blocks
        parts = response_clean.split("```")
        if len(parts) >= 2:
            yaml_str = parts[1].strip()
        else:
            yaml_str = response_clean
    else:
        # Assume raw YAML if no blocks
        yaml_str = response_clean

    ordered_raw = yaml.safe_load(yaml_str)

    if not isinstance(ordered_raw, list):
        raise ValueError("Order output is not a list")

    ordered = []
    seen = set()
    for entry in ordered_raw:
        if isinstance(entry, int):
            idx = entry
        elif isinstance(entry, str) and "#" in entry:
            idx = int(entry.split("#")[0].strip())
        else:
            idx = int(str(entry).strip())

        if 0 <= idx < num_abstractions and idx not in seen:
            ordered.append(idx)
            seen.add(idx)

    # Ensure all abstractions included
    for i in range(num_abstractions):
        if i not in seen:
            ordered.append(i)

    print(f"Chapter order: {ordered}")
    return ordered


def write_chapters(
    chapter_order: List[int],
    abstractions: List[Dict[str, Any]],
    files_data: List[Tuple[str, str]],
    project_name: str,
    language: str = "english",
    use_cache: bool = True
) -> List[str]:
    """Write tutorial chapters"""
    print(f"\n{'='*60}")
    print("STEP 4: Writing Chapters")
    print(f"{'='*60}")

    # Prepare chapter metadata
    chapter_files = {}
    all_chapters = []
    for i, idx in enumerate(chapter_order):
        name = abstractions[idx]["name"]
        safe_name = "".join(c if c.isalnum() else "_" for c in name).lower()
        filename = f"{i+1:02d}_{safe_name}.md"
        all_chapters.append(f"{i+1}. [{name}]({filename})")
        chapter_files[idx] = {"num": i+1, "name": name, "filename": filename}

    full_listing = "\n".join(all_chapters)
    chapters_written = []
    chapters_content = []

    for i, idx in enumerate(chapter_order):
        abstr = abstractions[idx]
        chapter_num = i + 1
        print(f"\nWriting Chapter {chapter_num}: {abstr['name']}...")

        # Get file content
        content_map = get_content_for_indices(files_data, abstr["files"], MAX_CHARS_PER_FILE_WRITE)
        file_context = "\n\n".join([
            f"--- File: {p.split('# ')[1] if '# ' in p else p} ---\n{c}"
            for p, c in content_map.items()
        ])

        # Previous chapters summary
        prev_summary = "\n---\n".join(chapters_written)

        # Navigation
        prev_chapter = chapter_files[chapter_order[i-1]] if i > 0 else None
        next_chapter = chapter_files[chapter_order[i+1]] if i < len(chapter_order)-1 else None

        # Language instructions
        lang_inst = ""
        concept_note = ""
        struct_note = ""
        prev_note = ""
        inst_note = ""
        mermaid_note = ""
        code_note = ""
        link_note = ""
        tone_note = ""

        if language.lower() != "english":
            lang = language.capitalize()
            lang_inst = f"IMPORTANT: Write this ENTIRE tutorial chapter in **{lang}**. Some input context (like concept name, description, chapter list, previous summary) might already be in {lang}, but you MUST translate ALL other generated content including explanations, examples, technical terms, and potentially code comments into {lang}. DO NOT use English anywhere except in code syntax, required proper nouns, or when specified. The entire output MUST be in {lang}.\n\n"
            concept_note = f" (Note: Provided in {lang})"
            struct_note = f" (Note: Chapter names might be in {lang})"
            prev_note = f" (Note: This summary might be in {lang})"
            inst_note = f" (in {lang})"
            mermaid_note = f" (Use {lang} for labels/text if appropriate)"
            code_note = f" (Translate to {lang} if possible, otherwise keep minimal English for clarity)"
            link_note = f" (Use the {lang} chapter title from the structure above)"
            tone_note = f" (appropriate for {lang} readers)"

        prompt = f"""
{lang_inst}Write a very beginner-friendly tutorial chapter (in Markdown format) for the project `{project_name}` about the concept: "{abstr['name']}". This is Chapter {chapter_num}.

Concept Details{concept_note}:
- Name: {abstr['name']}
- Description:
{abstr['description']}

Complete Tutorial Structure{struct_note}:
{full_listing}

Context from previous chapters{prev_note}:
{prev_summary if prev_summary else "This is the first chapter."}

Relevant Code Snippets (Code itself remains unchanged):
{file_context if file_context else "No specific code snippets provided for this abstraction."}

Instructions for the chapter (Generate content in {language.capitalize()} unless specified otherwise):
- Start with a clear heading (e.g., `# Chapter {chapter_num}: {abstr['name']}`). Use the provided concept name.

- If this is not the first chapter, begin with a brief transition from the previous chapter{inst_note}, referencing it with a proper Markdown link using its name{link_note}.

- Begin with a high-level motivation explaining what problem this abstraction solves{inst_note}. Start with a central use case as a concrete example. The whole chapter should guide the reader to understand how to solve this use case. Make it very minimal and friendly to beginners.

- If the abstraction is complex, break it down into key concepts. Explain each concept one-by-one in a very beginner-friendly way{inst_note}.

- Explain how to use this abstraction to solve the use case{inst_note}. Give example inputs and outputs for code snippets (if the output isn't values, describe at a high level what will happen{inst_note}).

- Each code block should be BELOW 10 lines! If longer code blocks are needed, break them down into smaller pieces and walk through them one-by-one. Aggresively simplify the code to make it minimal. Use comments{code_note} to skip non-important implementation details. Each code block should have a beginner friendly explanation right after it{inst_note}.

- Describe the internal implementation to help understand what's under the hood{inst_note}. First provide a non-code or code-light walkthrough on what happens step-by-step when the abstraction is called{inst_note}. It's recommended to use a simple sequenceDiagram with a dummy example - keep it minimal with at most 5 participants to ensure clarity. If participant name has space, use: `participant QP as Query Processing`. {mermaid_note}.

- Then dive deeper into code for the internal implementation with references to files. Provide example code blocks, but make them similarly simple and beginner-friendly. Explain{inst_note}.

- IMPORTANT: When you need to refer to other core abstractions covered in other chapters, ALWAYS use proper Markdown links like this: [Chapter Title](filename.md). Use the Complete Tutorial Structure above to find the correct filename and the chapter title{link_note}. Translate the surrounding text.

- Use mermaid diagrams to illustrate complex concepts (```mermaid``` format). {mermaid_note}.

- Heavily use analogies and examples throughout{inst_note} to help beginners understand.

- End the chapter with a brief conclusion that summarizes what was learned{inst_note} and provides a transition to the next chapter{inst_note}. If there is a next chapter, use a proper Markdown link: [Next Chapter Title](next_chapter_filename){link_note}.

- Ensure the tone is welcoming and easy for a newcomer to understand{tone_note}.

- Output *only* the Markdown content for this chapter.

Now, directly provide a super beginner-friendly Markdown output (DON'T need ```markdown``` tags):
"""

        content = call_llm(prompt, use_cache=use_cache)

        # Ensure proper heading
        expected_heading = f"# Chapter {chapter_num}: {abstr['name']}"
        if not content.strip().startswith(f"# Chapter {chapter_num}"):
            lines = content.strip().split("\n")
            if lines and lines[0].strip().startswith("#"):
                lines[0] = expected_heading
                content = "\n".join(lines)
            else:
                content = f"{expected_heading}\n\n{content}"

        chapters_written.append(content)
        chapters_content.append(content)

    print(f"\nFinished writing {len(chapters_content)} chapters.")
    return chapters_content


def combine_tutorial(
    chapters: List[str],
    chapter_order: List[int],
    abstractions: List[Dict[str, Any]],
    relationships: Dict[str, Any],
    project_name: str,
    repo_url: str,
    output_dir: str = "output"
) -> str:
    """Combine chapters into final tutorial"""
    print(f"\n{'='*60}")
    print("STEP 5: Combining Tutorial")
    print(f"{'='*60}")

    output_path = os.path.join(output_dir, f"tutorial_{project_name}.md")
    os.makedirs(output_dir, exist_ok=True)

    # Build mermaid diagram
    mermaid_lines = ["flowchart TD"]
    for i, abstr in enumerate(abstractions):
        node_id = f"A{i}"
        label = abstr["name"].replace('"', '')
        mermaid_lines.append(f'    {node_id}["{label}"]')

    for rel in relationships["details"]:
        from_id = f"A{rel['from']}"
        to_id = f"A{rel['to']}"
        label = rel["label"].replace('"', '').replace('\n', ' ')
        if len(label) > 30:
            label = label[:27] + "..."
        mermaid_lines.append(f'    {from_id} -- "{label}" --> {to_id}')

    mermaid_diagram = "\n".join(mermaid_lines)

    # Build content
    content = f"# Tutorial: {project_name}\n\n"
    content += f"{relationships['summary']}\n\n"
    content += f"**Source Repository:** [{repo_url}]({repo_url})\n\n"
    content += "```mermaid\n"
    content += mermaid_diagram + "\n"
    content += "```\n\n"

    # Table of contents
    content += "## Table of Contents\n\n"
    for i, idx in enumerate(chapter_order):
        name = abstractions[idx]["name"]
        anchor = f"chapter-{i+1}-" + "".join(c if c.isalnum() else "-" for c in name.lower())
        content += f"{i+1}. [{name}](#{anchor})\n"

    content += "\n---\n\n"

    # Add chapters
    for i, chapter in enumerate(chapters):
        # Remove attribution if present
        if "Generated by [AI Codebase Knowledge Builder]" in chapter:
            chapter = chapter.split("---\n\nGenerated by [AI Codebase Knowledge Builder]")[0].rstrip()
        content += chapter.strip() + "\n\n---\n\n"

    # Attribution
    content += "Generated by [AI Codebase Knowledge Builder](https://github.com/The-Pocket/Tutorial-Codebase-Knowledge)\n"

    # Write file
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"\nTutorial saved to: {output_path}")
    return output_path


# ============================================================================
# MAIN WORKFLOW
# ============================================================================

def generate_tutorial(
    repo_url: str,
    max_abstractions: int = 10,
    language: str = "english",
    provider: str = "litellm",
    use_cache: bool = True,
    output_dir: str = "output"
) -> str:
    """
    Main entry point: Generate a tutorial from a GitHub repository.

    Args:
        repo_url: GitHub repository URL
        max_abstractions: Maximum number of abstractions to identify
        language: Tutorial language (default: english)
        provider: LLM provider (litellm, openrouter, gemini, openai, anthropic)
        use_cache: Whether to use LLM response caching
        output_dir: Output directory for the tutorial

    Returns:
        Path to the generated tutorial file
    """
    print(f"\n{'='*60}")
    print("TUTORIAL CODEBASE KNOWLEDGE GENERATOR v3")
    print(f"{'='*60}")
    print(f"Repository: {repo_url}")
    print(f"Provider: {provider}")
    print(f"Language: {language}")
    print(f"Max Abstractions: {max_abstractions}")
    print(f"{'='*60}\n")

    # Set provider
    os.environ["LLM_PROVIDER"] = provider

    # Extract project name
    project_name = repo_url.rstrip('/').split('/')[-1].replace('.git', '')

    # Step 0: Crawl repository
    print("Fetching repository files...")
    result = crawl_github_files(repo_url)
    files_dict = result["files"]

    if not files_dict:
        raise ValueError("No files found in repository")

    print(f"Downloaded {len(files_dict)} files")

    # Convert to list of tuples
    files_data = list(files_dict.items())

    # Step 1: Identify abstractions
    abstractions = identify_abstractions(
        files_data, project_name, language, max_abstractions, use_cache
    )

    # Step 2: Analyze relationships
    relationships = analyze_relationships(
        abstractions, files_data, project_name, language, use_cache
    )

    # Step 3: Order chapters
    chapter_order = order_chapters(
        abstractions, relationships, project_name, language, use_cache
    )

    # Step 4: Write chapters
    chapters = write_chapters(
        chapter_order, abstractions, files_data, project_name, language, use_cache
    )

    # Step 5: Combine tutorial
    output_path = combine_tutorial(
        chapters, chapter_order, abstractions, relationships,
        project_name, repo_url, output_dir
    )

    print(f"\n{'='*60}")
    print("TUTORIAL GENERATION COMPLETE!")
    print(f"Output: {output_path}")
    print(f"{'='*60}\n")

    return output_path


# ============================================================================
# CLI ENTRY POINT
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Generate beginner-friendly tutorials from GitHub repositories",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python standalone_tutorial_generator_v3.py https://github.com/owner/repo
  python standalone_tutorial_generator_v3.py https://github.com/owner/repo --max-abstractions 8
  python standalone_tutorial_generator_v3.py https://github.com/owner/repo --language Chinese
  python standalone_tutorial_generator_v3.py https://github.com/owner/repo --provider openrouter

Environment Variables:
  LLM_PROVIDER          LLM provider (litellm, openrouter, gemini, openai, anthropic)
  LITELLM_BASE_URL      LiteLLM proxy URL (default: https://litellm.genr8ive.ai/v1)
  LITELLM_API_KEY       LiteLLM API key
  LITELLM_MODEL         LiteLLM model (default: gemini-flash)
  OPENROUTER_API_KEY    OpenRouter API key
  OPENROUTER_MODEL      OpenRouter model
  GEMINI_API_KEY        Google Gemini API key
  OPENAI_API_KEY        OpenAI API key
  ANTHROPIC_API_KEY     Anthropic API key
  GITHUB_TOKEN          GitHub token for private repos
        """
    )

    parser.add_argument(
        "repo_url",
        help="GitHub repository URL"
    )
    parser.add_argument(
        "--max-abstractions", "-m",
        type=int,
        default=10,
        help="Maximum number of abstractions to identify (default: 10)"
    )
    parser.add_argument(
        "--language", "-l",
        default="english",
        help="Tutorial language (default: english)"
    )
    parser.add_argument(
        "--provider", "-p",
        default=None,
        help="LLM provider (litellm, openrouter, gemini, openai, anthropic). Overrides LLM_PROVIDER env var."
    )
    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Disable LLM response caching"
    )
    parser.add_argument(
        "--output-dir", "-o",
        default="output",
        help="Output directory (default: output)"
    )

    args = parser.parse_args()

    # Determine provider
    provider = args.provider or os.getenv("LLM_PROVIDER", DEFAULT_PROVIDER)

    try:
        output_path = generate_tutorial(
            repo_url=args.repo_url,
            max_abstractions=args.max_abstractions,
            language=args.language,
            provider=provider,
            use_cache=not args.no_cache,
            output_dir=args.output_dir
        )
        print(f"Tutorial successfully generated: {output_path}")
        return 0
    except Exception as e:
        logger.error(f"Error generating tutorial: {e}")
        print(f"\nError: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
