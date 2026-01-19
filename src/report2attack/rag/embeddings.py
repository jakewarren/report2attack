"""Embedding provider abstractions for ChromaDB."""

from abc import ABC, abstractmethod

from chromadb.utils import embedding_functions


class EmbeddingProvider(ABC):
    """Base class for embedding providers."""

    @abstractmethod
    def get_embedding_function(self) -> embedding_functions.EmbeddingFunction:
        """Get ChromaDB embedding function."""
        pass


class OpenAIEmbeddings(EmbeddingProvider):
    """OpenAI embeddings provider."""

    def __init__(
        self,
        api_key: str | None = None,
        model_name: str = "text-embedding-3-small",
    ) -> None:
        """
        Initialize OpenAI embeddings.

        Args:
            api_key: OpenAI API key (uses OPENAI_API_KEY env var if not provided)
            model_name: Name of the embedding model
        """
        self.api_key = api_key
        self.model_name = model_name

    def get_embedding_function(self) -> embedding_functions.EmbeddingFunction:
        """Get OpenAI embedding function."""
        return embedding_functions.OpenAIEmbeddingFunction(
            api_key=self.api_key, model_name=self.model_name
        )


class SentenceTransformerEmbeddings(EmbeddingProvider):
    """Local sentence-transformers embeddings provider."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2") -> None:
        """
        Initialize sentence-transformers embeddings.

        Args:
            model_name: Name of the sentence-transformers model
        """
        self.model_name = model_name

    def get_embedding_function(self) -> embedding_functions.EmbeddingFunction:
        """Get sentence-transformer embedding function."""
        return embedding_functions.SentenceTransformerEmbeddingFunction(model_name=self.model_name)


def get_embedding_provider(provider: str = "openai", **kwargs: str | None) -> EmbeddingProvider:
    """
    Factory function to get embedding provider.

    Args:
        provider: Provider name ('openai' or 'sentence-transformers')
        **kwargs: Provider-specific arguments

    Returns:
        EmbeddingProvider instance

    Raises:
        ValueError: If provider is not supported
    """
    if provider == "openai":
        return OpenAIEmbeddings(**kwargs)  # type: ignore
    elif provider in ("sentence-transformers", "local"):
        return SentenceTransformerEmbeddings(**kwargs)  # type: ignore
    else:
        raise ValueError(
            f"Unsupported embedding provider: {provider}. "
            f"Choose from: openai, sentence-transformers"
        )
