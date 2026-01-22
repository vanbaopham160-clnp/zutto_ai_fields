import frappe
from frappe import _
from frappe.model.document import Document

class ZuttoAISettings(Document):
    """Zutto AI Settings - Global configuration for AI field generation"""

    def get_provider_config(self, provider: str) -> dict:
        """
        Get configuration for a specific provider.

        Args:
            provider: Provider name (openai, gemini, ollama)

        Returns:
            Dictionary with provider configuration
        """
        provider = provider.lower()
        config = {}

        if provider == "openai":
            config = {
                "api_key": self.get_password("openai_api_key"),  # Must use get_password() for Password fields
                "base_url": self.openai_base_url or "https://api.openai.com/v1",
                "model": self.default_model or "gpt-4o-mini"
            }
        elif provider == "gemini":
            config = {
                "api_key": self.get_password("gemini_api_key"),  # Must use get_password() for Password fields
                "model": self.default_model or "gemini-1.5-flash"
            }

        return config

    def validate(self):
        """Validate settings before save"""
        if self.enabled:
            if not self.default_provider:
                frappe.throw("Default Provider is required when AI is enabled")

            if not self.default_model:
                frappe.throw("Default Model is required when AI is enabled")

    @frappe.whitelist()
    def test_connection(self):
        """Test connection to the configured default provider"""
        from zutto_ai_fields.services.llm_service import generate_content

        if not self.enabled:
            return {
                "success": False,
                "error": "AI generation is disabled",
                "error_type": "disabled"
            }

        provider = self.default_provider
        config = self.get_provider_config(provider)

        if not config.get("api_key"):
            return {
                "success": False,
                "error": f"{provider.title()} API key not configured",
                "error_type": "invalid_key"
            }

        try:
            response = generate_content(
                provider=provider,
                config=config,
                prompt="Say 'Hello, World!'",
                system_prompt="You are a helpful assistant.",
                max_tokens=50,
                timeout=10
            )

            if response.success:
                return {
                    "success": True,
                    "message": f"Connection successful! Response: {response.content[:100]}...",
                    "provider": provider,
                    "model": config.get("model")
                }
            else:
                return {
                    "success": False,
                    "error": response.error,
                    "error_type": response.error_type
                }
        except Exception as e:
            return {
                "success": False,
                "error": f"Connection test failed: {str(e)}",
                "error_type": "unknown"
            }