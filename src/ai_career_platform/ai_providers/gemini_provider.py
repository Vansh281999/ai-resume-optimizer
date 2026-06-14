from .base import BaseLLMProvider, AIMessage

class GeminiProvider(BaseLLMProvider):
    def __init__(self, model: str = "gemini-2.0-flash", api_key: str = ""):
        self.model = model
        self.api_key = api_key or os.getenv("GEMINI_API_KEY", "")

    def generate(self, messages, **kwargs):
        import google.generativeai as genai
        genai.configure(api_key=self.api_key)
        model = genai.GenerativeModel(model_name=self.model)
        history = []
        latest = ""
        for m in messages:
            if m.role == "system":
                latest = m.content + "\n" + latest
                continue
            history.append({"role": m.role, "parts": [m.content]})
        if history:
            chat = model.start_chat(history=history[:-1])
            prompt = (latest + history[-1]["parts"][0]) if latest else history[-1]["parts"][0]
            response = chat.send_message(prompt)
        else:
            response = model.generate_content(latest or "")
        return response.text or ""
