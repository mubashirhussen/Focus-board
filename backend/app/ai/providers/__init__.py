import logging
from typing import Optional
from app.core.config import settings
from app.ai.providers.base import BaseLLMProvider, LLMResponse
from app.ai.providers.mock_provider import MockProvider
from app.ai.providers.gemini_provider import GeminiProvider
from app.ai.providers.openai_provider import OpenAIProvider
from app.ai.providers.anthropic_provider import AnthropicProvider

logger = logging.getLogger("focusboard.ai.providers")

def get_llm_provider(
    provider_name: Optional[str] = None,
    api_key: Optional[str] = None,
    model_name: Optional[str] = None,
) -> BaseLLMProvider:
    """
    Factory creating configured LLM provider instance.
    Defaults to settings.AI_PROVIDER with seamless fallback to MockProvider
    if required credentials are not supplied.
    """
    selected_provider = (provider_name or settings.AI_PROVIDER or "mock").lower()

    if selected_provider == "gemini":
        key = api_key or settings.GEMINI_API_KEY or settings.AI_API_KEY
        if key:
            model = model_name or settings.GEMINI_MODEL or settings.AI_MODEL
            return GeminiProvider(api_key=key, model_name=model, timeout=settings.AI_TIMEOUT_SECONDS)
        logger.warning("Gemini API key missing. Falling back to MockProvider.")

    elif selected_provider == "openai":
        key = api_key or settings.OPENAI_API_KEY or settings.AI_API_KEY
        if key:
            model = model_name or settings.OPENAI_MODEL or "gpt-4o-mini"
            return OpenAIProvider(api_key=key, model_name=model, timeout=settings.AI_TIMEOUT_SECONDS)
        logger.warning("OpenAI API key missing. Falling back to MockProvider.")

    elif selected_provider == "anthropic":
        key = api_key or settings.ANTHROPIC_API_KEY or settings.AI_API_KEY
        if key:
            model = model_name or settings.ANTHROPIC_MODEL or "claude-3-5-sonnet-20241022"
            return AnthropicProvider(api_key=key, model_name=model, timeout=settings.AI_TIMEOUT_SECONDS)
        logger.warning("Anthropic API key missing. Falling back to MockProvider.")

    # Default to MockProvider
    return MockProvider(model_name=model_name or "focusboard-mock-v1")

__all__ = [
    "BaseLLMProvider",
    "LLMResponse",
    "MockProvider",
    "GeminiProvider",
    "OpenAIProvider",
    "AnthropicProvider",
    "get_llm_provider",
]
