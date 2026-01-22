try:
    import google.generativeai as genai
except ImportError:
    genai = None

from .base import BaseLLMProvider, LLMResponse

class GeminiProvider(BaseLLMProvider):
    """Google Gemini LLM provider implementation"""

    def generate(
        self,
        prompt: str,
        system_prompt: str = "",
        max_tokens: int = 1000,
        timeout: int = 30
    ) -> LLMResponse:
        """Generate content using Google Gemini API"""

        if not genai:
            return LLMResponse(
                success=False,
                error="Google Generative AI library not installed. Please install google-generativeai package.",
                error_type="api_error"
            )

        if not self.api_key:
            return LLMResponse(
                success=False,
                error="Gemini API key not configured",
                error_type="invalid_key"
            )

        try:
            genai.configure(api_key=self.api_key)

            model_name = self.config.get("model", "gemini-1.5-flash")
            model = genai.GenerativeModel(model_name)

            # Build prompt with system instruction
            full_prompt = prompt
            if system_prompt:
                full_prompt = f"System: {system_prompt}\n\nUser: {prompt}"

            response = model.generate_content(
                full_prompt,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=max_tokens
                )
            )

            return LLMResponse(
                success=True,
                content=response.text
            )

        except Exception as e:
            error_msg = str(e)
            if "API key" in error_msg or "400" in error_msg:
                return LLMResponse(
                    success=False,
                    error="Invalid Gemini API key",
                    error_type="invalid_key"
                )
            elif "429" in error_msg or "quota" in error_msg.lower():
                return LLMResponse(
                    success=False,
                    error="Rate limit exceeded. Please try again later.",
                    error_type="rate_limit"
                )
            elif "timeout" in error_msg.lower() or "deadline" in error_msg.lower():
                return LLMResponse(
                    success=False,
                    error="Request timed out. Please try again.",
                    error_type="timeout"
                )
            else:
                return LLMResponse(
                    success=False,
                    error=f"Gemini API error: {error_msg}",
                    error_type="api_error"
                )