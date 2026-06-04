import os
import sys
from pathlib import Path

# Add root directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.config import get_settings
from backend.ai.gemini_client import get_ai_client

def test_keys():
    settings = get_settings()
    print("Testing API Keys...")
    print(f"Groq API Key length: {len(settings.groq_api_key) if settings.groq_api_key else 0}")
    print(f"OpenRouter API Key length: {len(settings.openrouter_api_key) if settings.openrouter_api_key else 0}")
    print(f"Mistral API Key length: {len(settings.mistral_api_key) if settings.mistral_api_key else 0}")
    
    client = get_ai_client()
    
    # Test Groq
    print("\nTesting Groq text generation...")
    try:
        res = client._call_groq("Hello, say 'Groq OK'", "", 0.1, 100, False)
        print(f"Groq response: {res.strip()}")
    except Exception as e:
        print(f"Groq failed: {e}")

    # Test Mistral
    print("\nTesting Mistral text generation...")
    try:
        res = client._call_mistral("Hello, say 'Mistral OK'", "", 0.1, 100, False)
        print(f"Mistral response: {res.strip()}")
    except Exception as e:
        print(f"Mistral failed: {e}")

    # Test OpenRouter
    print("\nTesting OpenRouter text generation with different models...")
    for model in ["google/gemini-2.5-flash", "google/gemini-2.5-flash:free", "google/gemini-2.5-flash-preview-05-20"]:
        print(f"Trying model: {model}")
        try:
            # Temporarily override model in settings
            settings.openrouter_vision_model = model
            res = client._call_openrouter("Hello, say 'OpenRouter OK'", "", 0.1, 100, False)
            print(f"  Success! Response: {res.strip()}")
            break
        except Exception as e:
            print(f"  Failed: {e}")

if __name__ == "__main__":
    test_keys()
