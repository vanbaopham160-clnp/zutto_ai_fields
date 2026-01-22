import frappe
from frappe import _

from .providers import (
    LLMResponse,
    OpenAIProvider,
    GeminiProvider
)

def generate_content(
    provider: str,
    config: dict,
    prompt: str,
    system_prompt: str = "",
    max_tokens: int = 1000,
    timeout: int = 30
) -> LLMResponse:
    """
    Generate content using the specified LLM provider.

    Args:
        provider: Provider name (openai, gemini, ollama)
        config: Provider configuration dictionary
        prompt: User prompt
        system_prompt: System prompt/instructions
        max_tokens: Maximum tokens to generate
        timeout: Request timeout in seconds

    Returns:
        LLMResponse object with success status and content/error
    """
    provider = provider.lower()

    # Get API key from config and remove it to avoid duplicate argument
    api_key = config.get("api_key")
    config_without_key = {k: v for k, v in config.items() if k != "api_key"}

    # Initialize provider
    try:
        if provider == "openai":
            llm_provider = OpenAIProvider(api_key=api_key, **config_without_key)
        elif provider == "gemini":
            llm_provider = GeminiProvider(api_key=api_key, **config_without_key)
        else:
            return LLMResponse(
                success=False,
                error=f"Unsupported provider: {provider}",
                error_type="invalid_key"
            )

        # Generate content
        return llm_provider.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            max_tokens=max_tokens,
            timeout=timeout
        )

    except Exception as e:
        frappe.log_error(
            title=f"LLM Service Exception: {provider}",
            message=frappe.get_traceback()
        )
        return LLMResponse(
            success=False,
            error=f"Provider error: {str(e)}",
            error_type="api_error"
        )

def get_available_providers(settings) -> list[dict]:
    """
    Get list of available providers with their status.

    Args:
        settings: Zutto AI Settings document

    Returns:
        List of provider info dicts
    """
    providers = []

    # OpenAI
    if settings.openai_api_key:
        providers.append({
            "name": "openai",
            "label": "OpenAI",
            "configured": True,
            "models": ["gpt-4o-mini", "gpt-4o", "gpt-3.5-turbo"]
        })
    else:
        providers.append({
            "name": "openai",
            "label": "OpenAI",
            "configured": False,
            "models": ["gpt-4o-mini", "gpt-4o", "gpt-3.5-turbo"]
        })

    # Gemini
    if settings.gemini_api_key:
        providers.append({
            "name": "gemini",
            "label": "Google Gemini",
            "configured": True,
            "models": ["gemini-1.5-flash", "gemini-1.5-pro"]
        })
    else:
        providers.append({
            "name": "gemini",
            "label": "Google Gemini",
            "configured": False,
            "models": ["gemini-1.5-flash", "gemini-1.5-pro"]
        })

    return providers