import os
import google.generativeai as genai
from backend.config import settings

# Configure with your existing API key
genai.configure(api_key=settings.GEMINI_API_KEY)

print("🔍 Searching for available models that support text generation...\n")

for m in genai.list_models():
    if 'generateContent' in m.supported_generation_methods:
        print(f"✅ Available: {m.name}")