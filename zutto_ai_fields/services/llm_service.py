import frappe
from frappe import _

from .providers import (
    LLMResponse,
    AnthropicProvider,
    OpenAIProvider,
    GeminiProvider,
    GLMProvider,
    CustomProvider
)

def get_provider_instance(provider_type: str, api_key: str = "", base_url: str = "", model: str = ""):
    """Instantiate the appropriate LLM provider strategy"""
    ptype = (provider_type or "").lower()

    config = {}
    if base_url:
        config["base_url"] = base_url
    if model:
        config["model"] = model

    if "anthropic" in ptype or "claude" in ptype:
        return AnthropicProvider(api_key=api_key, **config)
    elif "qwen" in ptype:
        if "base_url" not in config:
            config["base_url"] = "https://token-plan.maas.qwencloudapi.com/compatible-mode/v1"
        if "model" not in config:
            config["model"] = "qwen3.7-max"
        return OpenAIProvider(api_key=api_key, **config)
    elif "mimo" in ptype:
        if "base_url" not in config:
            config["base_url"] = "https://token-plan-cn.xiaomimimo.com/v1"
        if "model" not in config:
            config["model"] = "mimo-v2.5-pro"
        return OpenAIProvider(api_key=api_key, **config)
    elif "openai" in ptype or "chatgpt" in ptype:
        return OpenAIProvider(api_key=api_key, **config)
    elif "gemini" in ptype or "google" in ptype:
        return GeminiProvider(api_key=api_key, **config)
    elif "glm" in ptype or "zhipu" in ptype:
        return GLMProvider(api_key=api_key, **config)
    elif "custom" in ptype or "ollama" in ptype:
        return CustomProvider(api_key=api_key, **config)
    else:
        # Default to OpenAI-compatible provider
        return OpenAIProvider(api_key=api_key, **config)

def resolve_provider_and_model(config: dict) -> tuple:
    """
    Resolve which Zutto AI Provider and model should be used.

    Returns:
        (provider_doc, resolved_model_string)
    """
    if config.get("override_provider") and config.get("provider"):
        provider_name = config["provider"]
        if not frappe.db.exists("Zutto AI Provider", provider_name):
            frappe.throw(_(f"Configured AI Provider '{provider_name}' does not exist."))
        provider_doc = frappe.get_doc("Zutto AI Provider", provider_name)
        if not provider_doc.active:
            frappe.throw(_(f"Selected AI Provider '{provider_name}' is inactive."))
        model = config.get("model") or provider_doc.default_chat_model
        return provider_doc, model

    # Otherwise, resolve default active provider
    defaults = frappe.get_all(
        "Zutto AI Provider",
        filters={"default_provider": 1, "active": 1},
        pluck="name",
        limit=1
    )
    if not defaults:
        # Fallback to any active provider if none is explicitly marked default
        active_any = frappe.get_all(
            "Zutto AI Provider",
            filters={"active": 1},
            pluck="name",
            limit=1
        )
        if not active_any:
            frappe.throw(_("No active AI Provider configured. Please configure an active provider in Zutto AI Provider."))
        defaults = active_any

    provider_doc = frappe.get_doc("Zutto AI Provider", defaults[0])
    model = config.get("model") or provider_doc.default_chat_model
    return provider_doc, model

def execute_generation(
    provider_doc,
    model: str,
    prompt: str,
    system_prompt: str = "",
    max_tokens: int = None,
    timeout: int = None
) -> LLMResponse:
    """Execute generation using a resolved Zutto AI Provider record"""
    api_key = provider_doc.get_api_key()
    base_url = provider_doc.base_url_override or ""
    provider_type = provider_doc.provider

    tokens = max_tokens or provider_doc.max_tokens or 1000
    req_timeout = timeout or provider_doc.request_timeout or 30

    instance = get_provider_instance(
        provider_type=provider_type,
        api_key=api_key,
        base_url=base_url,
        model=model
    )

    return instance.generate(
        prompt=prompt,
        system_prompt=system_prompt,
        max_tokens=tokens,
        timeout=req_timeout
    )
