import time
from typing import List, Dict, Any, Optional
import httpx
from app.ai.providers.base import BaseLLMProvider, LLMResponse

class AnthropicProvider(BaseLLMProvider):
    def __init__(self, api_key: str, model_name: str = "claude-3-5-sonnet-20241022", timeout: int = 30):
        self.api_key = api_key
        self.model_name = model_name
        self.timeout = timeout
        self.base_url = "https://api.anthropic.com/v1/messages"

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

        if messages:
            for m in messages:
                if m.get("role") in ("user", "assistant"):
                    formatted_messages.append({"role": m["role"], "content": m.get("content", "")})

        formatted_messages.append({"role": "user", "content": prompt})

        payload: Dict[str, Any] = {
            "model": self.model_name,
            "messages": formatted_messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }

        if system_prompt:
            payload["system"] = system_prompt

        try:
            with httpx.Client(timeout=self.timeout) as client:
                res = client.post(
                    self.base_url,
                    json=payload,
                    headers={
                        "x-api-key": self.api_key,
                        "anthropic-version": "2023-06-01",
                        "Content-Type": "application/json"
                    }
                )
                res.raise_for_status()
                data = res.json()

            text_out = "".join(b.get("text", "") for b in data.get("content", []))
            usage = data.get("usage", {})
            in_tokens = usage.get("input_tokens", len(prompt) // 4)
            out_tokens = usage.get("output_tokens", len(text_out) // 4)
            latency_ms = int((time.time() - start_time) * 1000)

            return LLMResponse(
                content=text_out,
                input_tokens=in_tokens,
                output_tokens=out_tokens,
                total_tokens=in_tokens + out_tokens,
                provider="anthropic",
                model=self.model_name,
                latency_ms=latency_ms,
            )
        except Exception as e:
            raise RuntimeError(f"Anthropic API request failed: {str(e)}")
