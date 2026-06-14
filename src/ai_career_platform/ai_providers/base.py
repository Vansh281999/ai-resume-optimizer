from typing import Protocol
from pydantic import BaseModel

class AIMessage(BaseModel):
    role: str
    content: str

class BaseLLMProvider(Protocol):
    def generate(self, messages, **kwargs):
        ...
