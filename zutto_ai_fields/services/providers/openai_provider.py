try:
    import openai
except ImportError:
    openai = None

import frappe
from .base import BaseLLMProvider, LLMResponse

class OpenAIProvider(BaseLLMProvider):
    """OpenAI LLM provider implementation"""

    def generate(
        self,
        prompt: str,
        system_prompt: str = "",
        max_tokens: int = 1000,
        timeout: int = 30
    ) -> LLMResponse:
        """Generate content using OpenAI API"""
        if not openai:
            return LLMResponse(
                success=False,
                error="OpenAI library not installed. Please install openai package.",
                error_type="api_error"
            )

        if not self.api_key:
            return LLMResponse(
                success=False,
                error="OpenAI API key not configured",
                error_type="invalid_key"
            )

        try:
            client = openai.OpenAI(
                api_key=self.api_key,
                base_url=self.config.get("base_url"),
                timeout=timeout
            )

            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            model = self.config.get("model", "gpt-4o-mini")

            response = client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=max_tokens
            )

            return LLMResponse(
                success=True,
                content=response.choices[0].message.content
            )

        except openai.AuthenticationError:
            return LLMResponse(
                success=False,
                error="Invalid OpenAI API key",
                error_type="invalid_key"
            )
        except openai.RateLimitError:
            return LLMResponse(
                success=False,
                error="Rate limit exceeded. Please try again later.",
                error_type="rate_limit"
            )
        except openai.APITimeoutError:
            return LLMResponse(
                success=False,
                error="Request timed out. Please try again.",
                error_type="timeout"
            )
        except Exception as e:
            frappe.log_error(
                title="OpenAI Provider Exception",
                message=frappe.get_traceback()
            )
            return LLMResponse(
                success=False,
                error=f"OpenAI API error: {str(e)}",
                error_type="api_error"
            )