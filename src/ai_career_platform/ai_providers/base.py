from typing import Protocol, List, Optional
from pydantic import BaseModel

class AIMessage(BaseModel):
    role: str
    content: str

class BaseLLMProvider(Protocol):
    def generate(self, messages: List[AIMessage], timeout: int = 60, retries: int = 2) -> str:
        ...
