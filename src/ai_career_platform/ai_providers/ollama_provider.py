from .base import BaseLLMProvider, AIMessage

class OllamaProvider(BaseLLMProvider):
    def __init__(self, model: str = "llama3", base_url: str = "http://localhost:11434"):
        self.model = model
        self.base_url = base_url.rstrip("/")

    def generate(self, messages, **kwargs):
        import httpx
        timeout = kwargs.pop("timeout", 120)
        payload = {"model": self.model, "messages": [{"role": m.role, "content": m.content} for m in messages], "stream": False}
        payload.update(kwargs)
        with httpx.Client(timeout=timeout) as client:
            response = client.post(f"{self.base_url}/api/chat", json=payload)
            response.raise_for_status()
            data = response.json()
        return data.get("message", {}).get("content", "")
