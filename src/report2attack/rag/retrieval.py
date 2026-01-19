"""Semantic retrieval for MITRE ATT&CK techniques."""

from typing import Any

from .embeddings import get_embedding_provider
from .vector_store import ATTACKDataLoader, ATTACKVectorStore


class ATTACKRetriever:
    """Retrieves relevant ATT&CK techniques using semantic search."""

    def __init__(
        self,
        vector_store: ATTACKVectorStore,
        top_k: int = 10,
        similarity_threshold: float = 0.3,
        subtechnique_threshold: float = 0.5,
    ) -> None:
        """
        Initialize the retriever.

        Args:
            vector_store: Initialized vector store
            top_k: Number of techniques to retrieve
            similarity_threshold: Minimum similarity score for parent techniques
            subtechnique_threshold: Stricter threshold for sub-techniques (e.g., T1234.001)
        """
        self.vector_store = vector_store
        self.top_k = top_k
        self.similarity_threshold = similarity_threshold
        self.subtechnique_threshold = subtechnique_threshold

    def retrieve(
        self, query_text: str, tactic_filter: list[str] | None = None
    ) -> list[dict[str, Any]]:
        """
        Retrieve relevant ATT&CK techniques for query text.

        Args:
            query_text: Text to find relevant techniques for
            tactic_filter: Optional list of tactics to filter by

        Returns:
            List of technique dictionaries with similarity scores
        """
        results = self.vector_store.query(
            query_text=query_text, n_results=self.top_k, tactic_filter=tactic_filter
        )

        # Format results
        techniques = []
        if results.get("ids") and len(results["ids"]) > 0:
            ids = results["ids"][0]
            metadatas = results["metadatas"][0]
            distances = results["distances"][0]
            documents = results["documents"][0]

            for i, technique_id in enumerate(ids):
                # ChromaDB returns distances; convert to similarity
                similarity = 1.0 / (1.0 + distances[i])

                # Apply stricter threshold for sub-techniques (e.g., T1234.001)
                is_subtechnique = "." in technique_id
                threshold = (
                    self.subtechnique_threshold if is_subtechnique else self.similarity_threshold
                )

                if similarity < threshold:
                    continue

                technique = {
                    "technique_id": technique_id,
                    "name": metadatas[i].get("name", ""),
                    "tactics": metadatas[i].get("tactics", "").split(","),
                    "description": documents[i],
                    "similarity_score": similarity,
                }

                techniques.append(technique)

        return techniques

    def batch_retrieve(
        self, query_texts: list[str], tactic_filter: list[str] | None = None
    ) -> list[list[dict[str, Any]]]:
        """
        Batch retrieve relevant ATT&CK techniques for multiple queries.

        Args:
            query_texts: List of text queries to find relevant techniques for
            tactic_filter: Optional list of tactics to filter by

        Returns:
            List of technique lists, one per query
        """
        # Process all queries at once for better embedding efficiency
        all_results = []

        # Batch queries in groups for memory efficiency
        batch_size = 10
        for i in range(0, len(query_texts), batch_size):
            batch = query_texts[i : i + batch_size]

            for query_text in batch:
                results = self.retrieve(query_text, tactic_filter)
                all_results.append(results)

        return all_results

    def format_context(self, techniques: list[dict[str, Any]], max_tokens: int = 2000) -> str:
        """
        Format retrieved techniques as LLM context.

        Args:
            techniques: List of retrieved techniques
            max_tokens: Approximate maximum tokens for context

        Returns:
            Formatted context string
        """
        if not techniques:
            return "No relevant ATT&CK techniques found."

        context_parts = ["# Retrieved MITRE ATT&CK Techniques\n"]

        current_length = len(context_parts[0])
        approx_max_chars = max_tokens * 4  # Rough estimate

        for tech in techniques:
            tech_text = (
                f"\n## {tech['technique_id']}: {tech['name']}\n"
                f"**Tactics:** {', '.join(tech['tactics'])}\n"
                f"**Description:** {tech['description'][:500]}...\n"
                f"**Similarity:** {tech['similarity_score']:.3f}\n"
            )

            if current_length + len(tech_text) > approx_max_chars:
                break

            context_parts.append(tech_text)
            current_length += len(tech_text)

        return "".join(context_parts)


def setup_retrieval_system(
    embedding_provider: str = "openai",
    persist_directory: str | None = None,
    force_reload: bool = False,
) -> ATTACKRetriever:
    """
    Setup the complete retrieval system.

    Args:
        embedding_provider: Embedding provider to use ('openai' or 'sentence-transformers')
        persist_directory: Directory for vector store persistence
        force_reload: Force reload of ATT&CK data

    Returns:
        Initialized ATTACKRetriever

    Raises:
        RuntimeError: If setup fails
    """
    print("Setting up ATT&CK retrieval system...")

    # Initialize embedding provider
    embeddings = get_embedding_provider(embedding_provider)
    embedding_function = embeddings.get_embedding_function()

    # Initialize vector store
    vector_store = ATTACKVectorStore(persist_directory=persist_directory)
    vector_store.initialize(embedding_function)

    # Check if we need to populate
    if not vector_store.is_populated() or force_reload:
        print("Vector store empty or force reload requested. Loading ATT&CK data...")

        # Download and load ATT&CK data
        loader = ATTACKDataLoader()
        loader.download(force=force_reload)
        techniques = loader.extract_techniques()

        print(f"Extracted {len(techniques)} techniques from ATT&CK framework")

        # Populate vector store
        vector_store.populate(techniques)
    else:
        print("Vector store already populated")
        metadata = vector_store.get_metadata()
        print(f"Loaded {metadata.get('technique_count', 0)} techniques")

    # Create retriever
    retriever = ATTACKRetriever(vector_store)

    print("ATT&CK retrieval system ready")
    return retriever
