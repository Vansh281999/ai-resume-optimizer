from .base import BaseLLMProvider, AIMessage

class OpenAIProvider(BaseLLMProvider):
    def __init__(self, model: str = "gpt-4o-mini", api_key: str = ""):
        self.model = model
        self.api_key = api_key or os.getenv("OPENAI_API_KEY", "")

    def generate(self, messages, **kwargs):
        import openai
        client = openai.OpenAI(api_key=self.api_key)
        response = client.chat.completions.create(model=self.model, messages=[m.model_dump() for m in messages], **kwargs)
        return response.choices[0].message.content or ""
