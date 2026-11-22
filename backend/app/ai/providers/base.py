from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class LLMResponse(BaseModel):
    content: str
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    provider: str
    model: str
    latency_ms: int = 0

class BaseLLMProvider(ABC):
    @abstractmethod
    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        messages: Optional[List[Dict[str, str]]] = None,
        temperature: float = 0.3,
        max_tokens: int = 2048,
        json_mode: bool = False,
    ) -> LLMResponse:
        """Execute text completion or chat response against LLM provider."""
        pass
