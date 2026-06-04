"""Gemini API wrapper — Multi-provider AI client (Groq + OpenRouter + Mistral)."""

import json
import base64
import httpx
from typing import Optional
from backend.config import get_settings
from backend.utils.logger import get_logger

logger = get_logger("ai_client")
settings = get_settings()


class AIClient:
    """
    Multi-provider AI client that routes requests to the best free provider:
    - Groq (llama-3.3-70b-versatile): Primary for text tasks — blazing fast
    - OpenRouter (Gemini 2.5 Flash): Vision/OCR tasks — free with vision
    - Mistral (mistral-small): Fallback for text tasks
    """

    GROQ_BASE_URL = "https://api.groq.com/openai/v1"
    OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
    MISTRAL_BASE_URL = "https://api.mistral.ai/v1"

    def __init__(self):
        # 10s connection timeout, 30s read timeout (max wait for a response)
        self.http_client = httpx.Client(timeout=httpx.Timeout(timeout=30.0, connect=10.0))

    def generate_text(
        self,
        prompt: str,
        system_prompt: str = "",
        temperature: float = 0.1,
        max_tokens: int = 4096,
        json_mode: bool = False,
        provider: str = "groq",
    ) -> str:
        """
        Generate text using the specified provider.
        Falls back through providers on failure: groq → mistral → openrouter.
        """
        providers_order = self._get_fallback_order(provider)

        for prov in providers_order:
            try:
                result = self._call_provider(
                    provider=prov,
                    prompt=prompt,
                    system_prompt=system_prompt,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    json_mode=json_mode,
                )
                if result:
                    logger.info(f"Text generation successful via {prov}")
                    return result
            except Exception as e:
                logger.warning(f"Provider {prov} failed: {e}")
                continue

        logger.error("All providers failed for text generation")
        return ""

    def generate_with_vision(
        self,
        prompt: str,
        image_base64: str,
        media_type: str = "image/jpeg",
        system_prompt: str = "",
        temperature: float = 0.1,
        max_tokens: int = 4096,
    ) -> str:
        """
        Process image with vision model via OpenRouter (Gemini 2.5 Flash).
        Falls back to Groq Llama 4 Maverick if available.
        """
        # Primary: OpenRouter with vision model
        try:
            result = self._call_openrouter_vision(
                prompt=prompt,
                image_base64=image_base64,
                media_type=media_type,
                system_prompt=system_prompt,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            if result:
                logger.info("Vision generation successful via OpenRouter")
                return result
        except Exception as e:
            logger.warning(f"OpenRouter vision failed: {e}")

        logger.error("Vision generation failed on all providers")
        return ""

    def generate_json(
        self,
        prompt: str,
        system_prompt: str = "",
        provider: str = "groq",
    ) -> dict:
        """Generate structured JSON output."""
        full_prompt = f"{prompt}\n\nRespond ONLY with valid JSON. No markdown, no explanation."

        response = self.generate_text(
            prompt=full_prompt,
            system_prompt=system_prompt,
            json_mode=True,
            provider=provider,
        )

        return self._parse_json_response(response)

    def _call_provider(
        self,
        provider: str,
        prompt: str,
        system_prompt: str = "",
        temperature: float = 0.1,
        max_tokens: int = 4096,
        json_mode: bool = False,
    ) -> str:
        """Route to the correct provider API."""
        if provider == "groq":
            return self._call_groq(prompt, system_prompt, temperature, max_tokens, json_mode)
        elif provider == "openrouter":
            return self._call_openrouter(prompt, system_prompt, temperature, max_tokens, json_mode)
        elif provider == "mistral":
            return self._call_mistral(prompt, system_prompt, temperature, max_tokens, json_mode)
        else:
            raise ValueError(f"Unknown provider: {provider}")

    def _call_groq(
        self, prompt: str, system_prompt: str, temperature: float,
        max_tokens: int, json_mode: bool
    ) -> str:
        """Call Groq API with Llama 3.3 70B."""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": settings.groq_model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if json_mode:
            payload["response_format"] = {"type": "json_object"}

        response = self.http_client.post(
            f"{self.GROQ_BASE_URL}/chat/completions",
            headers={
                "Authorization": f"Bearer {settings.groq_api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
        )
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]

    def _call_openrouter(
        self, prompt: str, system_prompt: str, temperature: float,
        max_tokens: int, json_mode: bool
    ) -> str:
        """Call OpenRouter API."""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": settings.openrouter_vision_model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        response = self.http_client.post(
            f"{self.OPENROUTER_BASE_URL}/chat/completions",
            headers={
                "Authorization": f"Bearer {settings.openrouter_api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://plum-opd-adjudicator.app",
                "X-Title": "Plum OPD Claim Adjudicator",
            },
            json=payload,
        )
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]

    def _call_openrouter_vision(
        self, prompt: str, image_base64: str, media_type: str,
        system_prompt: str, temperature: float, max_tokens: int
    ) -> str:
        """Call OpenRouter with vision model for image processing."""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        # Build multimodal message
        content = [
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:{media_type};base64,{image_base64}"
                },
            },
            {"type": "text", "text": prompt},
        ]
        messages.append({"role": "user", "content": content})

        payload = {
            "model": settings.openrouter_vision_model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        response = self.http_client.post(
            f"{self.OPENROUTER_BASE_URL}/chat/completions",
            headers={
                "Authorization": f"Bearer {settings.openrouter_api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://plum-opd-adjudicator.app",
                "X-Title": "Plum OPD Claim Adjudicator",
            },
            json=payload,
        )
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]

    def _call_mistral(
        self, prompt: str, system_prompt: str, temperature: float,
        max_tokens: int, json_mode: bool
    ) -> str:
        """Call Mistral API as fallback."""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": settings.mistral_model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if json_mode:
            payload["response_format"] = {"type": "json_object"}

        response = self.http_client.post(
            f"{self.MISTRAL_BASE_URL}/chat/completions",
            headers={
                "Authorization": f"Bearer {settings.mistral_api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
        )
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]

    def _get_fallback_order(self, primary: str) -> list[str]:
        """Get provider fallback order starting from the primary."""
        all_providers = ["groq", "mistral", "openrouter"]
        if primary in all_providers:
            all_providers.remove(primary)
            return [primary] + all_providers
        return all_providers

    def _parse_json_response(self, response: str) -> dict:
        """Parse JSON from AI response, handling markdown code blocks."""
        if not response:
            return {}

        text = response.strip()

        # Remove markdown code blocks if present
        if text.startswith("```"):
            lines = text.split("\n")
            lines = [l for l in lines if not l.strip().startswith("```")]
            text = "\n".join(lines)

        try:
            return json.loads(text)
        except json.JSONDecodeError:
            # Try to find JSON object in the response
            start = text.find("{")
            end = text.rfind("}") + 1
            if start != -1 and end > start:
                try:
                    return json.loads(text[start:end])
                except json.JSONDecodeError:
                    pass

            logger.error(f"Failed to parse JSON response: {text[:200]}")
            return {}

    def close(self):
        """Close the HTTP client."""
        self.http_client.close()


# Singleton instance
_client: Optional[AIClient] = None


def get_ai_client() -> AIClient:
    """Get or create the AI client singleton."""
    global _client
    if _client is None:
        _client = AIClient()
    return _client
