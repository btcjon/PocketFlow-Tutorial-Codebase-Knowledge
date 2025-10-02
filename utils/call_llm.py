from google import genai
import os
import logging
import json
import requests
from datetime import datetime
import tiktoken

# Configure logging
log_directory = os.getenv("LOG_DIR", "logs")
os.makedirs(log_directory, exist_ok=True)
log_file = os.path.join(
    log_directory, f"llm_calls_{datetime.now().strftime('%Y%m%d')}.log"
)

# Set up logger
logger = logging.getLogger("llm_logger")
logger.setLevel(logging.INFO)
logger.propagate = False  # Prevent propagation to root logger
file_handler = logging.FileHandler(log_file, encoding='utf-8')
file_handler.setFormatter(
    logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
)
logger.addHandler(file_handler)

# Simple cache configuration
cache_file = "llm_cache.json"


def call_llm(prompt: str, use_cache: bool = True) -> str:
    """
    Call an LLM with the given prompt and return the response.
    The LLM provider is determined by the LLM_PROVIDER environment variable.
    If not set, it falls back to the provider specified in code.
    """
    # Check and truncate prompt if too long
    prompt = _ensure_prompt_fits_context(prompt)
    
    # Log the prompt
    logger.info(f"PROMPT: {prompt[:500]}..." if len(prompt) > 500 else f"PROMPT: {prompt}")

    # Check cache if enabled
    if use_cache:
        response_from_cache = _check_cache(prompt)
        if response_from_cache:
            return response_from_cache

    # Get the LLM provider from environment or shared dictionary
    provider = os.getenv("LLM_PROVIDER", "gemini").lower()
    
    # Call the appropriate LLM based on provider
    try:
        if provider == "gemini":
            response = _call_gemini(prompt)
        elif provider == "openai":
            response = _call_openai(prompt)
        elif provider == "anthropic":
            response = _call_anthropic(prompt)
        elif provider == "openrouter":
            response = _call_openrouter(prompt)
        else:
            # Default to Gemini if unknown provider
            logger.warning(f"Unknown LLM provider: {provider}. Falling back to Gemini.")
            response = _call_gemini(prompt)
        
        # Cache the response if caching is enabled
        if use_cache:
            _save_to_cache(prompt, response)
        
        # Log the response
        logger.info(f"RESPONSE: {response}")
        
        return response
        
    except Exception as e:
        logger.error(f"Error calling LLM: {e}")
        raise


def _call_gemini(prompt: str) -> str:
    """Call Google Gemini API"""
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY", os.getenv("GOOGLE_API_KEY")))
    response = client.models.generate_content(
        model="google/gemini-2.5-flash", contents=prompt
    )
    return response.text


def _call_openai(prompt: str) -> str:
    """Call OpenAI API"""
    from openai import OpenAI
    
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content


def _call_anthropic(prompt: str) -> str:
    """Call Anthropic Claude API"""
    import anthropic
    
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    response = client.messages.create(
        model="claude-3-haiku-20240307",
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}]
    )
    return response.content[0].text


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
        "model": os.getenv("OPENROUTER_MODEL", "google/gemini-2.5-flash"),
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7
    }
    
    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers=headers,
        json=data
    )
    
    if response.status_code == 400 and "maximum context length" in response.text:
        # Try with middle-out transform as suggested by the error
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


def _count_tokens(text: str) -> int:
    """Estimate token count using tiktoken (works for most models)"""
    try:
        encoding = tiktoken.get_encoding("cl100k_base")  # GPT-4 encoding
        return len(encoding.encode(text))
    except Exception:
        # Fallback: rough estimate of 4 chars per token
        return len(text) // 4


def _ensure_prompt_fits_context(prompt: str, max_tokens: int = 900000) -> str:
    """Ensure prompt fits within context limits by truncating if necessary"""
    token_count = _count_tokens(prompt)
    
    if token_count <= max_tokens:
        return prompt
    
    logger.warning(f"Prompt too long ({token_count} tokens), truncating to fit {max_tokens} tokens")
    
    # Calculate target character count (rough estimate)
    target_chars = int(max_tokens * 3.5)  # Conservative estimate
    
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


# Azure OpenAI Support
def _call_azure_openai(prompt: str) -> str:
    """Call Azure OpenAI API"""
    from openai import AzureOpenAI
    
    client = AzureOpenAI(
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-01"),
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
    )
    
    response = client.chat.completions.create(
        model=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4"),
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content