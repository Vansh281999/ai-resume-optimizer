import os
import time
from typing import List, Dict
from ai_career_platform.config import settings
from .base import BaseLLMProvider, AIMessage

class OpenRouterProvider(BaseLLMProvider):
    def __init__(self, model: str = "anthropic/claude-3.5-haiku", api_key: str = "", timeout: int = 60, retries: int = 2):
        self.model = model
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY", "") or getattr(settings, "OPENROUTER_API_KEY", "")
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
                    "https://openrouter.ai/api/v1/chat/completions",
                    json={"model": self.model, "messages": formatted},
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                        "HTTP-Referer": "https://ai-resume-optimizer-dium.onrender.com",
                        "X-Title": "AI Career Platform",
                    },
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