import frappe
from frappe import _

from .services.llm_service import generate_content as llm_generate
from .services.prompt_service import build_prompt, validate_placeholders
from .services.providers import LLMResponse

@frappe.whitelist(allow_guest=False)
def get_ai_field_configs(doctype: str) -> list[dict]:
    """
    Get all enabled AI field configurations for a DocType.
    Called on form load to determine which fields get AI buttons.
    """
    try:
        configs = frappe.get_all(
            "AI Field Config",
            filters={
                "target_doctype": doctype,
                "enabled": 1
            },
            fields=["name", "target_field", "prompt_template", "system_prompt"]
        )
        return configs
    except Exception:
        return []

@frappe.whitelist()
def generate_content(config_name: str, doc: str | dict) -> dict:
    """
    Generate AI content for a field.

    Args:
        config_name: AI Field Config name (e.g., "Item-description")
        doc: Current document values (for placeholder replacement)

    Returns:
        {
            "success": True,
            "content": "Generated content here...",
            "provider": "openai",
            "model": "gpt-4o-mini"
        }
        OR
        {
            "success": False,
            "error": "Error message for user",
            "error_type": "api_error|rate_limit|timeout|invalid_key"
        }
    """
    import json

    try:
        # Parse doc if it's a JSON string
        if isinstance(doc, str):
            doc = json.loads(doc)

        # Check write permission
        if not frappe.has_permission("AI Field Config", ptype="read"):
            return {
                "success": False,
                "error": _("You do not have permission to use AI generation"),
                "error_type": "permission"
            }

        # Get AI Field Config
        config = frappe.get_value(
            "AI Field Config",
            config_name,
            ["target_doctype", "target_field", "prompt_template", "system_prompt",
             "override_provider", "provider", "model"],
            as_dict=True
        )

        if not config:
            return {
                "success": False,
                "error": _("AI Field Config not found"),
                "error_type": "not_found"
            }

        # Get global settings
        settings = frappe.get_single("Zutto AI Settings")

        if not settings.enabled:
            return {
                "success": False,
                "error": _("AI generation is disabled"),
                "error_type": "disabled"
            }

        # Determine provider and config
        if config.override_provider and config.provider:
            provider = config.provider.lower()
            model = config.model or settings.default_model
        else:
            provider = (settings.default_provider or "").lower()
            model = settings.default_model

        # Get provider configuration
        provider_config = settings.get_provider_config(provider)

        if not provider_config.get("api_key"):
            return {
                "success": False,
                "error": _(f"{provider.title()} API key not configured"),
                "error_type": "invalid_key"
            }

        # Override model if specified in config
        if model:
            provider_config["model"] = model

        # Build prompt with placeholders
        prompt = build_prompt(config.prompt_template, doc)

        # Generate content
        response = llm_generate(
            provider=provider,
            config=provider_config,
            prompt=prompt,
            system_prompt=config.system_prompt or "",
            max_tokens=settings.max_tokens or 1000,
            timeout=settings.request_timeout or 30
        )

        if response.success:
            return {
                "success": True,
                "content": response.content,
                "provider": provider,
                "model": provider_config.get("model")
            }
        else:
            frappe.log_error(
                title=f"AI Generation Failed: {config_name}",
                message=f"Provider: {provider}, Model: {provider_config.get('model')}, Error: {response.error}, Error Type: {response.error_type}"
            )
            return {
                "success": False,
                "error": response.error,
                "error_type": response.error_type
            }

    except Exception as e:
        frappe.log_error(
            title=f"AI Generation Exception: {config_name}",
            message=frappe.get_traceback()
        )
        return {
            "success": False,
            "error": _("An unexpected error occurred. Please try again."),
            "error_type": "unknown"
        }

@frappe.whitelist()
def test_connection(provider: str) -> dict:
    """
    Test connection to a specific LLM provider.

    Args:
        provider: Provider name (openai, gemini, ollama)

    Returns:
        {"success": True, "message": "Connection successful"}
        OR
        {"success": False, "error": "Error message"}
    """
    try:
        settings = frappe.get_single("Zutto AI Settings")
        config = settings.get_provider_config(provider)

        if not config.get("api_key"):
            return {
                "success": False,
                "error": f"{provider.title()} API key not configured"
            }

        # Try a simple generation
        response = llm_generate(
            provider=provider,
            config=config,
            prompt="Say 'Hello, World!'",
            max_tokens=50,
            timeout=10
        )

        if response.success:
            return {
                "success": True,
                "message": f"Connection successful! Response: {response.content[:50]}..."
            }
        else:
            return {
                "success": False,
                "error": response.error
            }

    except Exception as e:
        return {
            "success": False,
            "error": f"Connection test failed: {str(e)}"
        }

@frappe.whitelist()
def test_ai_field_config(config_name: str) -> dict:
    """
    Test AI generation for a specific AI Field Config.

    Args:
        config_name: Name of the AI Field Config document

    Returns:
        {"success": True, "message": "...", "provider": "...", "model": "..."}
        OR
        {"success": False, "error": "..."}
    """
    try:
        config = frappe.get_doc("AI Field Config", config_name)

        if not config.enabled:
            return {"success": False, "error": "Config is disabled"}

        if not config.prompt_template:
            return {"success": False, "error": "Prompt template is required"}

        # Get placeholders from prompt
        from zutto_ai_fields.services.prompt_service import get_placeholder_suggestions
        placeholders = get_placeholder_suggestions(config.prompt_template)

        # Create sample doc with placeholder values
        sample_doc = {}
        for placeholder in placeholders:
            sample_doc[placeholder] = f"[Sample {placeholder}]"

        # Try to get real data from target doctype
        if config.target_doctype:
            try:
                sample_records = frappe.get_all(
                    config.target_doctype,
                    limit=1,
                    pluck="name"
                )
                if sample_records:
                    sample_doc = frappe.get_value(
                        config.target_doctype,
                        sample_records[0],
                        "*",
                        as_dict=True
                    )
            except Exception:
                pass  # Use placeholder values if can't get real data

        # Generate content
        response = generate_content(
            config_name=config_name,
            doc=sample_doc
        )

        if response.get("success"):
            return {
                "success": True,
                "message": f"Test successful!\n\nGenerated content:\n{response.get('content', '')[:500]}...",
                "provider": response.get("provider"),
                "model": response.get("model")
            }
        else:
            return {
                "success": False,
                "error": response.get("error", "Unknown error")
            }

    except Exception as e:
        frappe.log_error(
            title=f"Test AI Config Exception: {config_name}",
            message=frappe.get_traceback()
        )
        return {
            "success": False,
            "error": f"Test generation failed: {str(e)}"
        }