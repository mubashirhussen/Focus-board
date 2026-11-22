import time
from typing import List, Dict, Any, Optional
import httpx
from app.ai.providers.base import BaseLLMProvider, LLMResponse

class OpenAIProvider(BaseLLMProvider):
    def __init__(self, api_key: str, model_name: str = "gpt-4o-mini", timeout: int = 30):
        self.api_key = api_key
        self.model_name = model_name
        self.timeout = timeout
        self.base_url = "https://api.openai.com/v1/chat/completions"

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        messages: Optional[List[Dict[str, str]]] = None,
        temperature: float = 0.3,
        max_tokens: int = 2048,
        json_mode: bool = False,
    ) -> LLMResponse:
        start_time = time.time()
        formatted_messages = []

        if system_prompt:
            formatted_messages.append({"role": "system", "content": system_prompt})

        if messages:
            for m in messages:
                formatted_messages.append({"role": m.get("role", "user"), "content": m.get("content", "")})

        formatted_messages.append({"role": "user", "content": prompt})

        payload: Dict[str, Any] = {
            "model": self.model_name,
            "messages": formatted_messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        if json_mode:
            payload["response_format"] = {"type": "json_object"}

        try:
            with httpx.Client(timeout=self.timeout) as client:
                res = client.post(
                    self.base_url,
                    json=payload,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    }
                )
                res.raise_for_status()
                data = res.json()

            text_out = data["choices"][0]["message"]["content"]
            usage = data.get("usage", {})
            in_tokens = usage.get("prompt_tokens", len(prompt) // 4)
            out_tokens = usage.get("completion_tokens", len(text_out) // 4)
            latency_ms = int((time.time() - start_time) * 1000)

            return LLMResponse(
                content=text_out,
                input_tokens=in_tokens,
                output_tokens=out_tokens,
                total_tokens=in_tokens + out_tokens,
                provider="openai",
                model=self.model_name,
                latency_ms=latency_ms,
            )
        except Exception as e:
            raise RuntimeError(f"OpenAI API request failed: {str(e)}")
