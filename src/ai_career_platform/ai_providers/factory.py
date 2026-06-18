import logging
from typing import Optional, List, Dict
from ai_career_platform.config import settings
from .base import BaseLLMProvider, AIMessage
from .openai_provider import OpenAIProvider
from .anthropic_provider import AnthropicProvider
from .gemini_provider import GeminiProvider
from .ollama_provider import OllamaProvider
from .openrouter_provider import OpenRouterProvider
from .groq_provider import GroqProvider

logger = logging.getLogger(__name__)

def _get_api_key(name: str) -> str:
    return getattr(settings, name, "") or ""

def get_llm_provider(provider: str, model: Optional[str] = None, **kwargs):
    provider = (provider or "openrouter").strip().lower()
    if provider == "openai":
        return OpenAIProvider(model=model or "gpt-4o-mini", **kwargs)
    if provider == "anthropic":
        return AnthropicProvider(model=model or "claude-3-5-haiku-20241022", **kwargs)
    if provider in {"gemini", "google"}:
        return GeminiProvider(model=model or "gemini-2.0-flash", **kwargs)
    if provider == "ollama":
        return OllamaProvider(model=model or "llama3", **kwargs)
    if provider == "openrouter":
        return OpenRouterProvider(model=model or "anthropic/claude-3.5-haiku", **kwargs)
    if provider == "groq":
        return GroqProvider(model=model or "gpt-4o-mini", **kwargs)
    raise ValueError(f"Unsupported provider: {provider}")

class MultiProvider(BaseLLMProvider):
    def __init__(self, providers: Optional[List[str]] = None, **kwargs):
        self.provider_order = (providers or ["openrouter", "gemini", "ollama"]).copy()
        self.kwargs = kwargs

    def _get_provider_with_key(self, provider: str):
        api_key = _get_api_key(f"{provider.upper().replace('/', '_')}_API_KEY")
        if provider == "openai" and api_key:
            return OpenAIProvider(model=self.kwargs.get("model", "gpt-4o-mini"))
        if provider == "anthropic" and api_key:
            return AnthropicProvider(model=self.kwargs.get("model", "claude-3-5-haiku-20241022"))
        if provider in {"gemini", "google"} and api_key:
            return GeminiProvider(model=self.kwargs.get("model", "gemini-2.0-flash"))
        if provider == "openrouter" and api_key:
            return OpenRouterProvider(model=self.kwargs.get("model", "google/gemini-2.0-flash"))
        if provider == "ollama":
            return OllamaProvider(model=self.kwargs.get("model", "llama3"))
        return None

    def generate(self, messages: List[AIMessage], timeout: int = 60, retries: int = 2) -> str:
        errors = []
        for provider_name in self.provider_order:
            provider = self._get_provider_with_key(provider_name)
            if provider is None:
                continue
            try:
                logger.info(f"Trying {provider_name} for LLM generation")
                return provider.generate(messages, timeout=timeout, retries=retries)
            except Exception as e:
                logger.warning(f"{provider_name} failed: {e}")
                errors.append(f"{provider_name}: {str(e)}")
                continue
        raise RuntimeError(f"All providers failed. Errors: {errors}")

def get_multi_provider(**kwargs) -> MultiProvider:
    return MultiProvider(**kwargs)