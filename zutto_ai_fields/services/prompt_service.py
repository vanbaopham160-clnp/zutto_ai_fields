import re
import frappe
from frappe import _

def build_prompt(template: str, doc: dict) -> str:
    """
    Build prompt by replacing placeholders with document values.

    Placeholders format: {{field_name}} or {{doc.field_name}}

    Args:
        template: Prompt template with placeholders
        doc: Document dictionary with field values

    Returns:
        Processed prompt with placeholders replaced
    """
    if not template:
        return ""

    def replace_placeholder(match):
        placeholder = match.group(1)

        # Handle {{doc.field_name}} format
        if placeholder.startswith("doc."):
            field_name = placeholder[4:]
        else:
            field_name = placeholder

        # Get value from doc
        value = doc.get(field_name, "")

        # Convert to string and handle None / collections
        if value is None:
            value = ""
        elif isinstance(value, (list, dict)):
            import json
            value = json.dumps(value, default=str)
        elif not isinstance(value, str):
            value = str(value)

        return value

    # Replace all placeholders
    pattern = r"\{\{([^}]+)\}\}"
    processed_prompt = re.sub(pattern, replace_placeholder, template)

    return processed_prompt

def validate_placeholders(template: str, doc: dict) -> tuple[bool, list[str]]:
    """
    Validate that all placeholders in template exist in doc.

    Args:
        template: Prompt template with placeholders
        doc: Document dictionary

    Returns:
        Tuple of (is_valid, missing_fields)
    """
    if not template:
        return True, []

    # Extract all placeholders
    pattern = r"\{\{([^}]+)\}\}"
    placeholders = re.findall(pattern, template)

    missing_fields = []

    for placeholder in placeholders:
        # Handle {{doc.field_name}} format
        if placeholder.startswith("doc."):
            field_name = placeholder[4:]
        else:
            field_name = placeholder

        # Check if field exists in doc
        if field_name not in doc:
            missing_fields.append(field_name)

    return len(missing_fields) == 0, missing_fields

def get_placeholder_suggestions(template: str) -> list[str]:
    """
    Get list of placeholder names from template.

    Args:
        template: Prompt template

    Returns:
        List of field names
    """
    if not template:
        return []

    pattern = r"\{\{([^}]+)\}\}"
    placeholders = re.findall(pattern, template)

    # Clean up placeholders
    suggestions = []
    for placeholder in placeholders:
        if placeholder.startswith("doc."):
            suggestions.append(placeholder[4:])
        else:
            suggestions.append(placeholder)

    return list(set(suggestions))

def extract_placeholders(template: str) -> list[str]:
    """Extract placeholder names preserving order without duplicates."""
    if not template:
        return []
    pattern = r"\{\{([^}]+)\}\}"
    placeholders = re.findall(pattern, template)
    seen = set()
    result = []
    for ph in placeholders:
        field = ph[4:] if ph.startswith("doc.") else ph
        if field not in seen:
            seen.add(field)
            result.append(field)
    return result
