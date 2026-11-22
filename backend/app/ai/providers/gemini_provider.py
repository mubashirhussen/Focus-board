import time
import json
from typing import List, Dict, Any, Optional
import httpx
from app.ai.providers.base import BaseLLMProvider, LLMResponse

class GeminiProvider(BaseLLMProvider):
    def __init__(self, api_key: str, model_name: str = "gemini-1.5-flash", timeout: int = 30):
        self.api_key = api_key
        self.model_name = model_name
        self.timeout = timeout
        self.base_url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_name}:generateContent"

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
        contents = []

        if messages:
            for m in messages:
                role = "user" if m.get("role") in ("user", "system") else "model"
                contents.append({"role": role, "parts": [{"text": m.get("content", "")}]})

        contents.append({"role": "user", "parts": [{"text": prompt}]})

        payload: Dict[str, Any] = {
            "contents": contents,
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
            }
        }

        if system_prompt:
            payload["systemInstruction"] = {"parts": [{"text": system_prompt}]}

        if json_mode:
            payload["generationConfig"]["responseMimeType"] = "application/json"

        try:
            with httpx.Client(timeout=self.timeout) as client:
                res = client.post(
                    f"{self.base_url}?key={self.api_key}",
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )
                res.raise_for_status()
                data = res.json()

            candidates = data.get("candidates", [])
            text_out = ""
            if candidates:
                parts = candidates[0].get("content", {}).get("parts", [])
                if parts:
                    text_out = parts[0].get("text", "")

            usage = data.get("usageMetadata", {})
            in_tokens = usage.get("promptTokenCount", len(prompt) // 4)
            out_tokens = usage.get("candidatesTokenCount", len(text_out) // 4)
            latency_ms = int((time.time() - start_time) * 1000)

            return LLMResponse(
                content=text_out,
                input_tokens=in_tokens,
                output_tokens=out_tokens,
                total_tokens=in_tokens + out_tokens,
                provider="gemini",
                model=self.model_name,
                latency_ms=latency_ms,
            )
        except Exception as e:
            raise RuntimeError(f"Gemini API request failed: {str(e)}")
