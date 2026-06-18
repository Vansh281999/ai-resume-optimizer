import os
import time
from typing import List, Union, Dict
from ai_career_platform.config import settings
from .base import AIMessage

class GeminiProvider:
    def __init__(self, model: str = "gemini-2.0-flash", api_key: str = "", timeout: int = 60, retries: int = 2):
        self.model = model
        self.api_key = api_key or getattr(settings, "GEMINI_API_KEY", "") or os.getenv("GEMINI_API_KEY", "")
        self.default_timeout = timeout
        self.default_retries = retries

    def generate(self, messages, timeout: int = 60, retries: int = 2) -> str:
        import google.generativeai as genai
        system_parts = []
        for m in messages:
            if isinstance(m, AIMessage) and m.role == "system":
                system_parts.append(m.content)
            elif isinstance(m, dict) and m.get("role") == "system":
                system_parts.append(m.get("content", ""))
        system_prompt = "\n".join(system_parts) if system_parts else ""
        for attempt in range(retries + 1):
            try:
                genai.configure(api_key=self.api_key)
                model = genai.GenerativeModel(model_name=self.model)
                content = self._build_content(messages, system_prompt)
                response = model.generate_content(content)
                return response.text or ""
            except Exception:
                if attempt == retries:
                    raise
                time.sleep(0.5 * (attempt + 1))
        return ""

    def _build_content(self, messages, system_prompt: str) -> str:
        parts = [system_prompt] if system_prompt else []
        for m in messages:
            if isinstance(m, AIMessage) and m.role != "system":
                parts.append(m.content)
            elif isinstance(m, dict) and m.get("role") != "system":
                parts.append(m.get("content", ""))
        return "\n".join(p for p in parts if p)
