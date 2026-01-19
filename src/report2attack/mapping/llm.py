"""LLM provider abstractions."""

import os
from abc import ABC, abstractmethod
from typing import Any

from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI


class LLMProvider(ABC):
    """Base class for LLM providers."""

    @abstractmethod
    def get_model(self) -> Any:
        """Get LangChain model instance."""
        pass

    @abstractmethod
    def get_name(self) -> str:
        """Get provider name."""
        pass


class OpenAIProvider(LLMProvider):
    """OpenAI LLM provider."""

    def __init__(
        self,
        api_key: str | None = None,
        model_name: str = "gpt-5-nano",
        temperature: float = 0.0,
        reasoning_effort: str | None = "medium",
    ) -> None:
        """
        Initialize OpenAI provider.

        Args:
            api_key: OpenAI API key (uses OPENAI_API_KEY env var if not provided)
            model_name: Model name (e.g., 'gpt-5-nano', 'gpt-4', 'gpt-3.5-turbo')
            temperature: Sampling temperature
            reasoning_effort: Reasoning effort for reasoning models ('low', 'medium', 'high'), defaults to 'medium'
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model_name = model_name
        self.temperature = temperature
        self.reasoning_effort = reasoning_effort

    def get_model(self) -> ChatOpenAI:
        """Get OpenAI model instance."""
        kwargs = {
            "api_key": self.api_key,
            "model_name": self.model_name,
            "temperature": self.temperature,
        }

        if self.reasoning_effort is not None:
            kwargs["reasoning_effort"] = self.reasoning_effort

        return ChatOpenAI(**kwargs)

    def get_name(self) -> str:
        """Get provider name."""
        return f"openai-{self.model_name}"


class AnthropicProvider(LLMProvider):
    """Anthropic Claude LLM provider."""

    def __init__(
        self,
        api_key: str | None = None,
        model_name: str = "claude-sonnet-4-5-20250929",
        temperature: float = 0.0,
    ) -> None:
        """
        Initialize Anthropic provider.

        Args:
            api_key: Anthropic API key (uses ANTHROPIC_API_KEY env var if not provided)
            model_name: Model name (e.g., 'claude-sonnet-4-5-20250929', 'claude-3-opus', 'claude-3-sonnet')
            temperature: Sampling temperature
        """
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self.model_name = model_name
        self.temperature = temperature

    def get_model(self) -> ChatAnthropic:
        """Get Anthropic model instance."""
        return ChatAnthropic(
            api_key=self.api_key,
            model_name=self.model_name,
            temperature=self.temperature,
        )

    def get_name(self) -> str:
        """Get provider name."""
        return f"anthropic-{self.model_name}"


class OllamaProvider(LLMProvider):
    """Ollama local LLM provider."""

    def __init__(
        self,
        model_name: str = "llama2",
        base_url: str = "http://localhost:11434",
        temperature: float = 0.0,
    ) -> None:
        """
        Initialize Ollama provider.

        Args:
            model_name: Model name (e.g., 'llama2', 'mistral')
            base_url: Ollama server URL
            temperature: Sampling temperature
        """
        self.model_name = model_name
        self.base_url = base_url
        self.temperature = temperature

    def get_model(self) -> Any:
        """Get Ollama model instance."""
        # Use langchain_community for Ollama
        try:
            from langchain_community.chat_models import ChatOllama

            return ChatOllama(
                model=self.model_name,
                base_url=self.base_url,
                temperature=self.temperature,
            )
        except ImportError as e:
            raise ImportError(
                "ChatOllama requires langchain-community. "
                "Install with: pip install langchain-community"
            ) from e

    def get_name(self) -> str:
        """Get provider name."""
        return f"ollama-{self.model_name}"


def get_llm_provider(provider: str = "openai", **kwargs: Any) -> LLMProvider:
    """
    Factory function to get LLM provider.

    Args:
        provider: Provider name ('openai', 'anthropic', or 'ollama')
        **kwargs: Provider-specific arguments

    Returns:
        LLMProvider instance

    Raises:
        ValueError: If provider is not supported
    """
    if provider == "openai":
        return OpenAIProvider(**kwargs)
    elif provider == "anthropic":
        return AnthropicProvider(**kwargs)
    elif provider == "ollama":
        return OllamaProvider(**kwargs)
    else:
        raise ValueError(
            f"Unsupported LLM provider: {provider}. Choose from: openai, anthropic, ollama"
        )
