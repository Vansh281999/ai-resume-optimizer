import os
import time
from typing import List, Dict
import requests
from ai_career_platform.config import settings
from .base import AIMessage


class GeminiProvider:
    def __init__(self, model: str = "gemini-2.0-flash", api_key: str = "", timeout: int = 60, retries: int = 2):
        self.model = model
        self.api_key = api_key or getattr(settings, "GEMINI_API_KEY", "") or os.getenv("GEMINI_API_KEY", "")
        self.timeout = timeout
        self.retries = retries

    def generate(self, messages, timeout: int = 60, retries: int = 2) -> str:
        system_parts = []
        for m in messages:
            if isinstance(m, AIMessage) and m.role == "system":
                system_parts.append(m.content)
            elif isinstance(m, dict) and m.get("role") == "system":
                system_parts.append(m.get("content", ""))
        system_prompt = "\n".join(system_parts) if system_parts else ""
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
        content = self._build_content(messages, system_prompt)
        payload = {
            "contents": [{"parts": [{"text": content}]}]
        }
        last_error = None
        for attempt in range(retries + 1):
            try:
                response = requests.post(url, json=payload, timeout=timeout)
                try:
                    response.raise_for_status()
                except requests.HTTPError as exc:
                    status_code = getattr(exc.response, "status_code", None)
                    if status_code == 429:
                        raise RuntimeError("Gemini rate limit exceeded. Please try again later.") from exc
                    raise RuntimeError(f"Gemini request failed with status {status_code or 'unknown'}.") from exc
                data = response.json()
                return data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
            except Exception as e:
                last_error = e
                if attempt == retries:
                    raise last_error
                time.sleep(0.5 * (attempt + 1))
        raise last_error or RuntimeError("Gemini generation failed")

    def _build_content(self, messages, system_prompt: str) -> str:
        parts = [system_prompt] if system_prompt else []
        for m in messages:
            if isinstance(m, AIMessage) and m.role != "system":
                parts.append(m.content)
            elif isinstance(m, dict) and m.get("role") != "system":
                parts.append(m.get("content", ""))
        return "\n".join(p for p in parts if p)
