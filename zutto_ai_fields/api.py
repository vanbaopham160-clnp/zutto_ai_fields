import json
import frappe
from frappe import _

from .services.llm_service import resolve_provider_and_model, execute_generation
from .services.prompt_service import build_prompt, validate_placeholders, get_placeholder_suggestions

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
            fields=["name", "target_field", "prompt_template", "system_prompt", "override_provider", "provider", "model"]
        )
        return configs
    except Exception:
        return []

@frappe.whitelist()
def generate_content(config_name: str, doc: str | dict) -> dict:
    """
    Generate AI content for a field.

    Args:
        config_name: AI Field Config name
        doc: Current document values (for placeholder replacement)

    Returns:
        {
            "success": True,
            "content": "...",
            "provider": "Claude",
            "model": "claude-sonnet-5-5"
        }
    """
    try:
        # Parse doc if it's a JSON string
        if isinstance(doc, str):
            doc = json.loads(doc)

        # Check read permission
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

        # Resolve provider and model
        try:
            provider_doc, model = resolve_provider_and_model(config)
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "error_type": "config_error"
            }

        # Build prompt with placeholders
        prompt = build_prompt(config.prompt_template, doc)

        # Generate content
        response = execute_generation(
            provider_doc=provider_doc,
            model=model,
            prompt=prompt,
            system_prompt=config.system_prompt or "",
            max_tokens=provider_doc.max_tokens or 1000,
            timeout=provider_doc.request_timeout or 30
        )

        if response.success:
            return {
                "success": True,
                "content": response.content,
                "provider": provider_doc.name,
                "model": model
            }
        else:
            frappe.log_error(
                title=f"AI Generation Failed: {config_name}",
                message=f"Provider: {provider_doc.name}, Model: {model}, Error: {response.error}, Error Type: {response.error_type}"
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
def test_provider_connection(provider_name: str) -> dict:
    """
    Test connection to a specific Zutto AI Provider.

    Args:
        provider_name: Name of the Zutto AI Provider document
    """
    if not frappe.has_permission("Zutto AI Provider", ptype="write"):
        return {"success": False, "error": _("Insufficient permissions")}

    try:
        if not frappe.db.exists("Zutto AI Provider", provider_name):
            return {"success": False, "error": _(f"Provider '{provider_name}' not found")}

        provider_doc = frappe.get_doc("Zutto AI Provider", provider_name)
        response = execute_generation(
            provider_doc=provider_doc,
            model=provider_doc.default_chat_model,
            prompt="Respond with 'Connection successful!' in 5 words or less.",
            system_prompt="",
            max_tokens=30,
            timeout=provider_doc.request_timeout or 15
        )

        if response.success:
            return {
                "success": True,
                "message": f"Connection successful! Response: {response.content.strip()}"
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
def test_connection(provider: str) -> dict:
    """Backward compatibility alias for test_provider_connection"""
    return test_provider_connection(provider)

@frappe.whitelist()
def test_ai_field_config(config_name: str) -> dict:
    """
    Test AI generation for a specific AI Field Config.
    """
    try:
        config = frappe.get_doc("AI Field Config", config_name)

        if not config.enabled:
            return {"success": False, "error": "Config is disabled"}

        if not config.prompt_template:
            return {"success": False, "error": "Prompt template is required"}

        placeholders = get_placeholder_suggestions(config.prompt_template)
        sample_doc = {}
        for placeholder in placeholders:
            sample_doc[placeholder] = f"[Sample {placeholder}]"

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
                pass

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
