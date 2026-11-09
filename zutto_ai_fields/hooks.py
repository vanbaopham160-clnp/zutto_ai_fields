app_name = "zutto_ai_fields"
app_title = "Zutto AI Fields"
app_publisher = "Zutto Solutions"
app_description = "AI-powered field content generation for Frappe"
app_version = "0.0.1"
app_license = "MIT"

# Include JS/CSS in all web pages
app_include_js = ["/assets/zutto_ai_fields/js/ai_field_button.js", "/assets/zutto_ai_fields/js/form_hook.js"]
app_include_css = "/assets/zutto_ai_fields/css/ai_field.css"

# DocType-specific JavaScript
doctype_js = {
    "Zutto AI Provider": "public/js/zutto_ai_provider.js",
    "AI Field Config": "public/js/ai_field_config.js"
}

# DocType permissions
has_permission = {
    "Zutto AI Provider": "zutto_ai_fields.permissions.has_provider_permission",
    "AI Field Config": "zutto_ai_fields.permissions.has_config_permission"
}
