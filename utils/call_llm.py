from google import genai
import os
import logging
import json
import requests
from datetime import datetime

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
file_handler = logging.FileHandler(log_file)
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
    # Log the prompt
    logger.info(f"PROMPT: {prompt}")

    # Check cache if enabled
    if use_cache:
        response_from_cache = _check_cache(prompt)
        if response_from_cache:
            return response_from_cache

    # Get the LLM provider from environment or shared dictionary
    provider = os.getenv("LLM_PROVIDER", "gemini").lower()
    
    # Call the appropriate LLM based on provider
    if provider == "gemini":
        response_text = _call_gemini(prompt)
    elif provider == "anthropic":
        response_text = _call_anthropic(prompt)
    elif provider == "openai":
        response_text = _call_openai(prompt)
    elif provider == "openrouter":
        response_text = _call_openrouter(prompt)
    else:
        # Default to Gemini if provider is unknown
        logger.warning(f"Unknown LLM provider: {provider}. Falling back to Gemini.")
        response_text = _call_gemini(prompt)

    # Log the response
    logger.info(f"RESPONSE: {response_text}")

    # Update cache if enabled
    if use_cache:
        _update_cache(prompt, response_text)

    return response_text


def _check_cache(prompt: str) -> str:
    """Check if a response is cached for the given prompt."""
    try:
        if os.path.exists(cache_file):
            with open(cache_file, "r") as f:
                cache = json.load(f)
                if prompt in cache:
                    logger.info(f"CACHE HIT: Using cached response")
                    return cache[prompt]
    except Exception as e:
        logger.warning(f"Failed to load cache: {e}")
    
    return None


def _update_cache(prompt: str, response: str) -> None:
    """Update the cache with a new prompt-response pair."""
    try:
        # Load existing cache if available
        cache = {}
        if os.path.exists(cache_file):
            try:
                with open(cache_file, "r") as f:
                    cache = json.load(f)
            except:
                pass

        # Add to cache and save
        cache[prompt] = response
        with open(cache_file, "w") as f:
            json.dump(cache, f)
    except Exception as e:
        logger.error(f"Failed to save cache: {e}")


def _call_gemini(prompt: str) -> str:
    """Call the Google Gemini API."""
    try:
        # Use AI Studio key
        api_key = os.getenv("GEMINI_API_KEY", "")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in environment")
            
        client = genai.Client(api_key=api_key)
        model = os.getenv("GEMINI_MODEL", "gemini-1.5-pro")
        
        response = client.models.generate_content(model=model, contents=[prompt])
        return response.text
    except Exception as e:
        error_msg = f"Gemini API call failed: {e}"
        logger.error(error_msg)
        raise Exception(error_msg)


def _call_anthropic(prompt: str) -> str:
    """Call the Anthropic Claude API."""
    try:
        from anthropic import Anthropic
        
        api_key = os.getenv("ANTHROPIC_API_KEY", "")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in environment")
            
        client = Anthropic(api_key=api_key)
        model = os.getenv("ANTHROPIC_MODEL", "claude-3-opus-20240229")
        
        response = client.messages.create(
            model=model,
            max_tokens=21000,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        return response.content[0].text
    except Exception as e:
        error_msg = f"Anthropic API call failed: {e}"
        logger.error(error_msg)
        raise Exception(error_msg)


def _call_openai(prompt: str) -> str:
    """Call the OpenAI API."""
    try:
        from openai import OpenAI
        
        api_key = os.getenv("OPENAI_API_KEY", "")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in environment")
            
        client = OpenAI(api_key=api_key)
        model = os.getenv("OPENAI_MODEL", "gpt-4o")
        
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2
        )
        return response.choices[0].message.content
    except Exception as e:
        error_msg = f"OpenAI API call failed: {e}"
        logger.error(error_msg)
        raise Exception(error_msg)


def _call_openrouter(prompt: str) -> str:
    """Call the OpenRouter API, which provides access to various LLMs."""
    try:
        api_key = os.getenv("OPENROUTER_API_KEY", "")
        if not api_key:
            raise ValueError("OPENROUTER_API_KEY not found in environment")
            
        model = os.getenv("OPENROUTER_MODEL", "anthropic/claude-3-opus:beta")
        
        headers = {
            "Authorization": f"Bearer {api_key}",
        }

        data = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}]
        }

        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=data
        )

        if response.status_code != 200:
            error_msg = f"OpenRouter API call failed with status {response.status_code}: {response.text}"
            logger.error(error_msg)
            raise Exception(error_msg)
            
        response_text = response.json()["choices"][0]["message"]["content"]
        return response_text
    except Exception as e:
        error_msg = f"OpenRouter API call failed: {e}"
        logger.error(error_msg)
        raise Exception(error_msg)


if __name__ == "__main__":
    # Test each provider
    if os.getenv("TEST_ALL_PROVIDERS", "false").lower() == "true":
        test_prompt = "Hello, how are you? Respond in exactly one sentence."
        for provider in ["openrouter", "gemini", "anthropic", "openai"]:
            try:
                os.environ["LLM_PROVIDER"] = provider
                print(f"\nTesting {provider.upper()}...")
                response = call_llm(test_prompt, use_cache=False)
                print(f"Response: {response}")
            except Exception as e:
                print(f"Error with {provider}: {e}")
    else:
        # Simple test with default provider
        test_prompt = "Hello, how are you?"
        print("Making call...")
        response = call_llm(test_prompt, use_cache=False)
        print(f"Response: {response}")
