import requests
import frappe
from .base import BaseLLMProvider, LLMResponse

class GLMProvider(BaseLLMProvider):
    """GLM (Zhipu AI) LLM provider implementation (OpenAI compatible)"""

    def generate(
        self,
        prompt: str,
        system_prompt: str = "",
        max_tokens: int = 1000,
        timeout: int = 30
    ) -> LLMResponse:
        """Generate content using Zhipu GLM API"""
        if not self.api_key:
            return LLMResponse(
                success=False,
                error="GLM API key not configured",
                error_type="invalid_key"
            )

        base_url = (self.config.get("base_url") or "https://open.bigmodel.cn/api/paas/v4").rstrip("/")
        model = self.config.get("model") or "glm-4.5-flash"

        try:
            endpoint = f"{base_url}/chat/completions"
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            payload = {
                "model": model,
                "messages": messages,
                "max_tokens": max_tokens
            }

            resp = requests.post(endpoint, headers=headers, json=payload, timeout=timeout)

            if resp.status_code == 200:
                data = resp.json()
                content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                return LLMResponse(success=True, content=content)
            elif resp.status_code == 401:
                return LLMResponse(success=False, error="Invalid GLM API key", error_type="invalid_key")
            elif resp.status_code == 429:
                return LLMResponse(success=False, error="Rate limit exceeded. Please try again later.", error_type="rate_limit")
            else:
                return LLMResponse(success=False, error=f"GLM API error ({resp.status_code}): {resp.text}", error_type="api_error")

        except requests.Timeout:
            return LLMResponse(success=False, error="Request timed out. Please try again.", error_type="timeout")
        except Exception as e:
            frappe.log_error(title="GLM Provider Exception", message=frappe.get_traceback())
            return LLMResponse(success=False, error=f"GLM API error: {str(e)}", error_type="api_error")
