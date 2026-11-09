from abc import ABC, abstractmethod
from dataclasses import dataclass

@dataclass
class LLMResponse:
    """Response from LLM provider"""
    success: bool
    content: str = ""
    error: str = ""
    error_type: str = ""  # api_error, rate_limit, timeout, invalid_key, unknown

class BaseLLMProvider(ABC):
    """Abstract base class for LLM providers"""

    def __init__(self, api_key: str = None, **kwargs):
        self.api_key = api_key
        if "config" in kwargs and isinstance(kwargs["config"], dict):
            self.config = {**kwargs["config"], **{k: v for k, v in kwargs.items() if k != "config"}}
        else:
            self.config = kwargs

    @abstractmethod
    def generate(
        self,
        prompt: str,
        system_prompt: str = "",
        max_tokens: int = 1000,
        timeout: int = 30
    ) -> LLMResponse:
        """Generate content from prompt"""
        pass