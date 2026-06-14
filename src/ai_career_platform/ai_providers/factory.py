import os
from typing import Optional
from .base import BaseLLMProvider, AIMessage
from .openai_provider import OpenAIProvider
from .anthropic_provider import AnthropicProvider
from .gemini_provider import GeminiProvider
from .ollama_provider import OllamaProvider

def get_llm_provider(provider: str, model: Optional[str] = None, **kwargs):
    provider = (provider or "openai").strip().lower()
    if provider == "openai":
        return OpenAIProvider(model=model or "gpt-4o-mini", **kwargs)
    if provider == "anthropic":
        return AnthropicProvider(model=model or "claude-3-5-haiku-20241022", **kwargs)
    if provider in {"gemini", "google"}:
        return GeminiProvider(model=model or "gemini-2.0-flash", **kwargs)
    if provider == "ollama":
        return OllamaProvider(model=model or "llama3", **kwargs)
    raise ValueError(f"Unsupported provider: {provider}")
