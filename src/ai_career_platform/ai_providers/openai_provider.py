import os
import time
from typing import List, Union, Dict

class OpenAIProvider:
    def __init__(self, model: str = "gpt-4o-mini", api_key: str = "", timeout: int = 60, retries: int = 2):
        self.model = model
        self.api_key = api_key or os.getenv("OPENAI_API_KEY", "")
        self.default_timeout = timeout
        self.default_retries = retries

    def generate(self, messages, timeout: int = 60, retries: int = 2) -> str:
        from .base import AIMessage
        import openai
        formatted = []
        for m in messages:
            if isinstance(m, AIMessage):
                formatted.append({"role": m.role, "content": m.content})
            elif isinstance(m, dict):
                formatted.append(m)
        for attempt in range(retries + 1):
            try:
                client = openai.OpenAI(api_key=self.api_key, timeout=timeout)
                response = client.chat.completions.create(
                    model=self.model,
                    messages=formatted,
                    timeout=timeout,
                )
                return response.choices[0].message.content or ""
            except Exception:
                if attempt == retries:
                    raise
                time.sleep(0.5 * (attempt + 1))
        return ""
