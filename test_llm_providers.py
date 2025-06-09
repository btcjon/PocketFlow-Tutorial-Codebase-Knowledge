#!/usr/bin/env python3
"""
Test script to check if all LLM providers are properly configured.
Run this script to verify API keys and connectivity for each provider.
"""

import os
import sys
from utils.call_llm import call_llm

def test_provider(provider, model=None):
    """Test a specific LLM provider"""
    print(f"\n{'='*50}")
    print(f"Testing {provider.upper()} provider")
    print(f"{'='*50}")
    
    # Set environment variables
    os.environ["LLM_PROVIDER"] = provider
    if model:
        model_var = f"{provider.upper()}_MODEL"
        print(f"Setting {model_var}={model}")
        os.environ[model_var] = model
        
    # Check if API key is set
    api_key_var = f"{provider.upper()}_API_KEY"
    api_key = os.environ.get(api_key_var)
    if not api_key:
        print(f"⚠️ Warning: {api_key_var} not found in environment")
        return False
    
    # Test with a simple prompt
    try:
        test_prompt = "Respond with a single word: Hello!"
        print("Sending test prompt...")
        response = call_llm(test_prompt, use_cache=False)
        print(f"Response received: {response}")
        print(f"✅ {provider.upper()} is configured and working correctly")
        return True
    except Exception as e:
        print(f"❌ Error testing {provider}: {e}")
        return False

def main():
    """Test all LLM providers"""
    print("LLM Provider Test Utility")
    print("-----------------------")
    
    # Load environment variables from .env file if present
    try:
        import dotenv
        dotenv.load_dotenv()
        print("Loaded environment variables from .env file")
    except ImportError:
        print("dotenv package not installed, skipping .env file loading")
    
    # Track results
    results = {}
    
    # Test each provider with appropriate models
    providers = {
        "gemini": "gemini-1.5-pro",
        "openrouter": "anthropic/claude-3-opus:beta", 
        "anthropic": "claude-3-opus-20240229",
        "openai": "gpt-4o"
    }
    
    # Allow testing a specific provider from command line
    if len(sys.argv) > 1 and sys.argv[1] in providers:
        provider = sys.argv[1]
        results[provider] = test_provider(provider, providers[provider])
    else:
        # Test all providers
        for provider, model in providers.items():
            results[provider] = test_provider(provider, model)
    
    # Summary
    print("\n\n" + "="*50)
    print("LLM Provider Test Results Summary")
    print("="*50)
    
    working_providers = [p for p, status in results.items() if status]
    failed_providers = [p for p, status in results.items() if not status]
    
    if working_providers:
        print(f"\n✅ Working providers: {', '.join(working_providers)}")
    if failed_providers:
        print(f"\n❌ Failed providers: {', '.join(failed_providers)}")
        
    if not working_providers:
        print("\n⚠️ No working LLM providers found! Please check your API keys.")
        return 1
        
    print(f"\nRecommended llm-provider argument: --llm-provider={working_providers[0]}")
    return 0

if __name__ == "__main__":
    sys.exit(main()) 