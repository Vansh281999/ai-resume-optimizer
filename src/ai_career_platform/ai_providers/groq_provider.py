import os
import time
from typing import List, Dict
from ai_career_platform.config import settings
from .base import BaseLLMProvider, AIMessage


class GroqProvider(BaseLLMProvider):
    def __init__(self, model: str = "gpt-4o-mini", api_key: str = "", timeout: int = 60, retries: int = 2):
        self.model = model
        self.api_key = api_key or getattr(settings, "GROQ_API_KEY", "") or os.getenv("GROQ_API_KEY", "")
        self.default_timeout = timeout
        self.default_retries = retries

    def generate(self, messages, timeout: int = 60, retries: int = 2) -> str:
        import httpx

        formatted = []
        for m in messages:
            if isinstance(m, AIMessage):
                formatted.append({"role": m.role, "content": m.content})
            elif isinstance(m, dict):
                formatted.append({"role": m.get("role"), "content": m.get("content")})

        for attempt in range(retries + 1):
            try:
                response = httpx.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    json={"model": self.model, "messages": formatted},
                    headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
                    timeout=timeout,
                )
                response.raise_for_status()
                data = response.json()
                return data.get("choices", [{}])[0].get("message", {}).get("content", "")
            except Exception:
                if attempt == retries:
                    raise
                time.sleep(0.5 * (attempt + 1))
        return ""
