import os
import time
from typing import List, Union, Dict
from ai_career_platform.config import settings

class AnthropicProvider:
    def __init__(self, model: str = "claude-3-5-haiku-20241022", api_key: str = "", timeout: int = 60, retries: int = 2):
        self.model = model
        self.api_key = api_key or getattr(settings, "ANTHROPIC_API_KEY", "") or os.getenv("ANTHROPIC_API_KEY", "")
        self.default_timeout = timeout
        self.default_retries = retries

    def generate(self, messages, timeout: int = 60, retries: int = 2) -> str:
        from .base import AIMessage
        import anthropic
        formatted_system = ""
        formatted = []
        for m in messages:
            if isinstance(m, AIMessage):
                if m.role == "system":
                    formatted_system = m.content
                else:
                    formatted.append({"role": m.role, "content": m.content})
            elif isinstance(m, dict):
                if m.get("role") == "system":
                    formatted_system = m.get("content", "")
                else:
                    formatted.append({"role": m.get("role"), "content": m.get("content")})
        for attempt in range(retries + 1):
            try:
                client = anthropic.Anthropic(api_key=self.api_key, timeout=timeout)
                response = client.messages.create(
                    model=self.model,
                    system=formatted_system,
                    messages=formatted,
                    max_tokens=1000,
                    timeout=timeout,
                )
                return response.content[0].text if response.content else ""
            except Exception:
                if attempt == retries:
                    raise
                time.sleep(0.5 * (attempt + 1))
        return ""
