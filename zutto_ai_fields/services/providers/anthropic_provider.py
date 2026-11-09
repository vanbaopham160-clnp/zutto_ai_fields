import json
import requests
import frappe
from .base import BaseLLMProvider, LLMResponse

try:
    import anthropic
except ImportError:
    anthropic = None

class AnthropicProvider(BaseLLMProvider):
    """Anthropic (Claude) LLM provider implementation"""

    def generate(
        self,
        prompt: str,
        system_prompt: str = "",
        max_tokens: int = 1000,
        timeout: int = 30
    ) -> LLMResponse:
        """Generate content using Anthropic Claude API"""
        if not self.api_key:
            return LLMResponse(
                success=False,
                error="Anthropic API key not configured",
                error_type="invalid_key"
            )

        model = self.config.get("model") or "claude-sonnet-5-5"
        base_url = (self.config.get("base_url") or "").rstrip("/")

        # If official anthropic library is available and no custom base_url is set
        if anthropic and not base_url:
            try:
                client = anthropic.Anthropic(
                    api_key=self.api_key,
                    timeout=timeout
                )

                kwargs = {
                    "model": model,
                    "max_tokens": max_tokens,
                    "messages": [{"role": "user", "content": prompt}]
                }
                if system_prompt:
                    kwargs["system"] = system_prompt

                response = client.messages.create(**kwargs)
                text_content = ""
                for block in response.content:
                    if getattr(block, "type", "") == "text":
                        text_content += block.text

                return LLMResponse(
                    success=True,
                    content=text_content
                )

            except anthropic.AuthenticationError:
                return LLMResponse(
                    success=False,
                    error="Invalid Anthropic API key",
                    error_type="invalid_key"
                )
            except anthropic.RateLimitError:
                return LLMResponse(
                    success=False,
                    error="Rate limit exceeded. Please try again later.",
                    error_type="rate_limit"
                )
            except anthropic.APITimeoutError:
                return LLMResponse(
                    success=False,
                    error="Request timed out. Please try again.",
                    error_type="timeout"
                )
            except Exception as e:
                frappe.log_error(title="Anthropic SDK Exception", message=frappe.get_traceback())
                # Fallback to direct HTTP request below

        # Direct HTTP API fallback (also handles base_url_override)
        try:
            endpoint = f"{base_url or 'https://api.anthropic.com'}/v1/messages"
            headers = {
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json"
            }
            payload = {
                "model": model,
                "max_tokens": max_tokens,
                "messages": [{"role": "user", "content": prompt}]
            }
            if system_prompt:
                payload["system"] = system_prompt

            resp = requests.post(endpoint, headers=headers, json=payload, timeout=timeout)

            if resp.status_code == 200:
                data = resp.json()
                text = "".join(b.get("text", "") for b in data.get("content", []) if b.get("type") == "text")
                return LLMResponse(success=True, content=text)
            elif resp.status_code == 401:
                return LLMResponse(success=False, error="Invalid Anthropic API key", error_type="invalid_key")
            elif resp.status_code == 429:
                return LLMResponse(success=False, error="Rate limit exceeded. Please try again later.", error_type="rate_limit")
            else:
                return LLMResponse(success=False, error=f"Anthropic API error ({resp.status_code}): {resp.text}", error_type="api_error")

        except requests.Timeout:
            return LLMResponse(success=False, error="Request timed out. Please try again.", error_type="timeout")
        except Exception as e:
            frappe.log_error(title="Anthropic HTTP Exception", message=frappe.get_traceback())
            return LLMResponse(success=False, error=f"Anthropic API error: {str(e)}", error_type="api_error")
