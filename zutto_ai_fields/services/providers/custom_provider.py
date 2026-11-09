import requests
import frappe
from .base import BaseLLMProvider, LLMResponse

class CustomProvider(BaseLLMProvider):
    """Custom / Ollama OpenAI-compatible LLM provider"""

    def generate(
        self,
        prompt: str,
        system_prompt: str = "",
        max_tokens: int = 1000,
        timeout: int = 30
    ) -> LLMResponse:
        """Generate content using generic OpenAI-compatible or Ollama endpoint"""
        base_url = (self.config.get("base_url") or "http://localhost:11434/v1").rstrip("/")
        model = self.config.get("model") or "llama3"

        api_key = (self.api_key or "").strip()
        if api_key.lower().startswith("bearer "):
            api_key = api_key[7:].strip()

        try:
            # First attempt standard OpenAI-compatible /v1/chat/completions
            endpoint = f"{base_url}/chat/completions" if not base_url.endswith("/chat/completions") else base_url
            headers = {"Content-Type": "application/json"}
            if api_key:
                headers["Authorization"] = f"Bearer {api_key}"

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

            # If 404, check if it's native Ollama /api/generate
            if resp.status_code == 404 and "localhost:11434" in base_url:
                ollama_resp = requests.post(
                    "http://localhost:11434/api/generate",
                    json={"model": model, "prompt": f"{system_prompt}\n\n{prompt}" if system_prompt else prompt, "stream": False},
                    timeout=timeout
                )
                if ollama_resp.status_code == 200:
                    return LLMResponse(success=True, content=ollama_resp.json().get("response", ""))

            if resp.status_code == 200:
                data = resp.json()
                content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                return LLMResponse(success=True, content=content)
            else:
                return LLMResponse(success=False, error=f"Endpoint error ({resp.status_code}): {resp.text}", error_type="api_error")

        except requests.Timeout:
            return LLMResponse(success=False, error="Request timed out. Please try again.", error_type="timeout")
        except Exception as e:
            frappe.log_error(title="Custom Provider Exception", message=frappe.get_traceback())
            return LLMResponse(success=False, error=f"Custom Provider error: {str(e)}", error_type="api_error")
