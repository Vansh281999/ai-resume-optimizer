from .base import BaseLLMProvider, AIMessage

class AnthropicProvider(BaseLLMProvider):
    def __init__(self, model: str = "claude-3-5-haiku-20241022", api_key: str = ""):
        self.model = model
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY", "")

    def generate(self, messages, **kwargs):
        import anthropic
        client = anthropic.Anthropic(api_key=self.api_key)
        system = next((m.content for m in messages if m.role == "system"), "")
        chat = [{"role": m.role, "content": m.content} for m in messages if m.role != "system"]
        response = client.messages.create(model=self.model, system=system, messages=chat, **kwargs)
        return response.content[0].text if response.content else ""
