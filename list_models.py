from google import generativeai as genai
import os

# Get API key from environment
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    print("Error: GEMINI_API_KEY not found in environment")
    exit(1)

# Configure SDK
genai.configure(api_key=api_key)

# List text generation models
print("Available Gemini models:")
for m in genai.list_models():
    if "generateContent" in m.supported_generation_methods:
        print(f"- {m.name}")
