"""Tests for RAG pipeline components."""

import json
from unittest.mock import Mock, patch

import pytest

from report2attack.rag.embeddings import (
    OpenAIEmbeddings,
    SentenceTransformerEmbeddings,
    get_embedding_provider,
)
from report2attack.rag.retrieval import ATTACKRetriever, setup_retrieval_system
from report2attack.rag.vector_store import ATTACKDataLoader, ATTACKVectorStore


class TestATTACKDataLoader:
    """Tests for MITRE ATT&CK data loader."""

    @patch("report2attack.rag.vector_store.requests.get")
    def test_download_success(self, mock_get, tmp_path) -> None:
        """Test successful download of ATT&CK data."""
        # Mock response
        mock_response = Mock()
        mock_response.json.return_value = {"objects": []}
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        loader = ATTACKDataLoader(data_dir=str(tmp_path))
        result = loader.download()

        assert result.exists()
        mock_get.assert_called_once()

    @patch("report2attack.rag.vector_store.requests.get")
    def test_download_fails(self, mock_get, tmp_path) -> None:
        """Test handling of download failure."""
        mock_get.side_effect = Exception("Network error")

        loader = ATTACKDataLoader(data_dir=str(tmp_path))
        with pytest.raises(RuntimeError, match="Failed to download"):
            loader.download()

    def test_load_nonexistent_file(self, tmp_path) -> None:
        """Test loading when file doesn't exist."""
        loader = ATTACKDataLoader(data_dir=str(tmp_path))
        with pytest.raises(FileNotFoundError, match="ATT&CK data not found"):
            loader.load()

    def test_load_success(self, tmp_path) -> None:
        """Test successful loading of ATT&CK data."""
        loader = ATTACKDataLoader(data_dir=str(tmp_path))

        # Create a mock data file
        data = {"objects": [{"type": "attack-pattern", "name": "Test"}]}
        with open(loader.data_file, "w") as f:
            json.dump(data, f)

        result = loader.load()
        assert "objects" in result
        assert len(result["objects"]) == 1

    def test_extract_techniques(self, tmp_path) -> None:
        """Test extraction of techniques from STIX data."""
        loader = ATTACKDataLoader(data_dir=str(tmp_path))

        # Create mock STIX data
        data = {
            "objects": [
                {
                    "type": "attack-pattern",
                    "id": "attack-pattern--12345",
                    "name": "Spearphishing",
                    "description": "Test description",
                    "external_references": [
                        {
                            "source_name": "mitre-attack",
                            "external_id": "T1566.001"
                        }
                    ],
                    "kill_chain_phases": [
                        {
                            "kill_chain_name": "mitre-attack",
                            "phase_name": "initial-access"
                        }
                    ],
                    "x_mitre_deprecated": False
                }
            ]
        }

        with open(loader.data_file, "w") as f:
            json.dump(data, f)

        techniques = loader.extract_techniques()
        assert len(techniques) == 1
        assert techniques[0]["technique_id"] == "T1566.001"
        assert techniques[0]["name"] == "Spearphishing"
        assert "initial-access" in techniques[0]["tactics"]

    def test_extract_techniques_filters_deprecated(self, tmp_path) -> None:
        """Test that deprecated techniques are filtered out."""
        loader = ATTACKDataLoader(data_dir=str(tmp_path))

        data = {
            "objects": [
                {
                    "type": "attack-pattern",
                    "id": "attack-pattern--12345",
                    "name": "Deprecated Technique",
                    "description": "Old technique",
                    "external_references": [
                        {"source_name": "mitre-attack", "external_id": "T9999"}
                    ],
                    "kill_chain_phases": [],
                    "x_mitre_deprecated": True
                }
            ]
        }

        with open(loader.data_file, "w") as f:
            json.dump(data, f)

        techniques = loader.extract_techniques()
        assert len(techniques) == 0


class TestEmbeddingProviders:
    """Tests for embedding providers."""

    def test_openai_provider(self) -> None:
        """Test OpenAI embedding provider initialization."""
        provider = OpenAIEmbeddings(api_key="test_key")
        assert provider.api_key == "test_key"
        assert provider.model_name == "text-embedding-3-small"

    def test_openai_provider_custom_model(self) -> None:
        """Test OpenAI provider with custom model."""
        provider = OpenAIEmbeddings(model_name="custom-model")
        assert provider.model_name == "custom-model"

    def test_sentence_transformer_provider(self) -> None:
        """Test sentence-transformers provider."""
        provider = SentenceTransformerEmbeddings()
        assert provider.model_name == "all-MiniLM-L6-v2"

    def test_get_embedding_provider_openai(self) -> None:
        """Test factory function for OpenAI."""
        provider = get_embedding_provider("openai", api_key="test")
        assert isinstance(provider, OpenAIEmbeddings)

    def test_get_embedding_provider_sentence_transformers(self) -> None:
        """Test factory function for sentence-transformers."""
        provider = get_embedding_provider("sentence-transformers")
        assert isinstance(provider, SentenceTransformerEmbeddings)

    def test_get_embedding_provider_invalid(self) -> None:
        """Test factory function with invalid provider."""
        with pytest.raises(ValueError, match="Unsupported embedding provider"):
            get_embedding_provider("invalid_provider")


class TestATTACKVectorStore:
    """Tests for vector store operations."""

    def test_initialization(self, tmp_path) -> None:
        """Test vector store initialization."""
        vector_store = ATTACKVectorStore(persist_directory=str(tmp_path))
        assert vector_store.persist_directory.exists()
        assert vector_store.collection_name == "attack_techniques"

    @patch("report2attack.rag.vector_store.chromadb.PersistentClient")
    def test_initialize_collection(self, mock_client, tmp_path) -> None:
        """Test collection initialization."""
        mock_collection = Mock()
        mock_client_instance = Mock()
        mock_client_instance.get_or_create_collection.return_value = mock_collection
        mock_client.return_value = mock_client_instance

        vector_store = ATTACKVectorStore(persist_directory=str(tmp_path))
        mock_embedding_fn = Mock()
        vector_store.initialize(mock_embedding_fn)

        assert vector_store.collection == mock_collection
        mock_client_instance.get_or_create_collection.assert_called_once()

    def test_is_populated_empty(self, tmp_path) -> None:
        """Test is_populated with empty collection."""
        vector_store = ATTACKVectorStore(persist_directory=str(tmp_path))
        assert not vector_store.is_populated()

    @patch("report2attack.rag.vector_store.chromadb.PersistentClient")
    def test_is_populated_with_data(self, mock_client, tmp_path) -> None:
        """Test is_populated with data."""
        mock_collection = Mock()
        mock_collection.count.return_value = 100
        mock_client_instance = Mock()
        mock_client_instance.get_or_create_collection.return_value = mock_collection
        mock_client.return_value = mock_client_instance

        vector_store = ATTACKVectorStore(persist_directory=str(tmp_path))
        vector_store.initialize(Mock())

        assert vector_store.is_populated()

    @patch("report2attack.rag.vector_store.chromadb.PersistentClient")
    def test_populate(self, mock_client, tmp_path) -> None:
        """Test populating vector store with techniques."""
        mock_collection = Mock()
        mock_client_instance = Mock()
        mock_client_instance.get_or_create_collection.return_value = mock_collection
        mock_client.return_value = mock_client_instance

        vector_store = ATTACKVectorStore(persist_directory=str(tmp_path))
        vector_store.initialize(Mock())

        techniques = [
            {
                "technique_id": "T1566.001",
                "name": "Spearphishing",
                "description": "Test description",
                "tactics": ["initial-access"],
                "stix_id": "attack-pattern--123"
            }
        ]

        vector_store.populate(techniques)
        mock_collection.add.assert_called()

    @patch("report2attack.rag.vector_store.chromadb.PersistentClient")
    def test_query(self, mock_client, tmp_path) -> None:
        """Test querying vector store."""
        mock_collection = Mock()
        mock_collection.query.return_value = {
            "ids": [["T1566.001"]],
            "metadatas": [[{"name": "Spearphishing", "tactics": "initial-access"}]],
            "distances": [[0.1]],
            "documents": [["Spearphishing description"]]
        }
        mock_client_instance = Mock()
        mock_client_instance.get_or_create_collection.return_value = mock_collection
        mock_client.return_value = mock_client_instance

        vector_store = ATTACKVectorStore(persist_directory=str(tmp_path))
        vector_store.initialize(Mock())

        result = vector_store.query("test query", n_results=5)
        assert "ids" in result
        mock_collection.query.assert_called_once()


class TestATTACKRetriever:
    """Tests for technique retrieval."""

    def test_initialization(self) -> None:
        """Test retriever initialization."""
        mock_vector_store = Mock()
        retriever = ATTACKRetriever(mock_vector_store, top_k=10, similarity_threshold=0.3)

        assert retriever.vector_store == mock_vector_store
        assert retriever.top_k == 10
        assert retriever.similarity_threshold == 0.3

    def test_retrieve(self) -> None:
        """Test retrieving techniques."""
        mock_vector_store = Mock()
        mock_vector_store.query.return_value = {
            "ids": [["T1566.001", "T1078"]],
            "metadatas": [
                [
                    {"name": "Spearphishing", "tactics": "initial-access"},
                    {"name": "Valid Accounts", "tactics": "persistence"}
                ]
            ],
            "distances": [[0.1, 0.2]],
            "documents": [["Spearphishing description", "Valid Accounts description"]]
        }

        retriever = ATTACKRetriever(mock_vector_store)
        results = retriever.retrieve("phishing attack")

        assert len(results) == 2
        assert results[0]["technique_id"] == "T1566.001"
        assert "similarity_score" in results[0]

    def test_retrieve_with_threshold(self) -> None:
        """Test retrieval with similarity threshold."""
        mock_vector_store = Mock()
        mock_vector_store.query.return_value = {
            "ids": [["T1566.001"]],
            "metadatas": [[{"name": "Spearphishing", "tactics": "initial-access"}]],
            "distances": [[2.0]],  # High distance = low similarity
            "documents": [["Spearphishing description"]]
        }

        retriever = ATTACKRetriever(mock_vector_store, similarity_threshold=0.5)
        results = retriever.retrieve("test")

        # Should be filtered out due to low similarity
        assert len(results) == 0

    def test_format_context(self) -> None:
        """Test formatting techniques as LLM context."""
        mock_vector_store = Mock()
        retriever = ATTACKRetriever(mock_vector_store)

        techniques = [
            {
                "technique_id": "T1566.001",
                "name": "Spearphishing",
                "tactics": ["initial-access"],
                "description": "Test description",
                "similarity_score": 0.9
            }
        ]

        context = retriever.format_context(techniques)
        assert "T1566.001" in context
        assert "Spearphishing" in context
        assert "initial-access" in context

    def test_format_context_empty(self) -> None:
        """Test formatting empty techniques list."""
        mock_vector_store = Mock()
        retriever = ATTACKRetriever(mock_vector_store)

        context = retriever.format_context([])
        assert "No relevant" in context


class TestSetupRetrievalSystem:
    """Tests for retrieval system setup."""

    @patch("report2attack.rag.retrieval.ATTACKDataLoader")
    @patch("report2attack.rag.retrieval.ATTACKVectorStore")
    @patch("report2attack.rag.retrieval.get_embedding_provider")
    def test_setup_with_existing_data(
        self, mock_get_provider, mock_vector_store_class, mock_loader_class
    ) -> None:
        """Test setup when vector store already has data."""
        # Mock embedding provider
        mock_provider = Mock()
        mock_embedding_fn = Mock()
        mock_provider.get_embedding_function.return_value = mock_embedding_fn
        mock_get_provider.return_value = mock_provider

        # Mock vector store
        mock_vector_store = Mock()
        mock_vector_store.is_populated.return_value = True
        mock_vector_store.get_metadata.return_value = {"technique_count": 100}
        mock_vector_store_class.return_value = mock_vector_store

        # Execute
        retriever = setup_retrieval_system()

        # Should not download/populate if already populated
        mock_loader_class.assert_not_called()
        assert isinstance(retriever, ATTACKRetriever)

    @patch("report2attack.rag.retrieval.ATTACKDataLoader")
    @patch("report2attack.rag.retrieval.ATTACKVectorStore")
    @patch("report2attack.rag.retrieval.get_embedding_provider")
    def test_setup_with_empty_store(
        self, mock_get_provider, mock_vector_store_class, mock_loader_class
    ) -> None:
        """Test setup when vector store is empty."""
        # Mock embedding provider
        mock_provider = Mock()
        mock_embedding_fn = Mock()
        mock_provider.get_embedding_function.return_value = mock_embedding_fn
        mock_get_provider.return_value = mock_provider

        # Mock vector store (empty)
        mock_vector_store = Mock()
        mock_vector_store.is_populated.return_value = False
        mock_vector_store_class.return_value = mock_vector_store

        # Mock loader
        mock_loader = Mock()
        mock_loader.extract_techniques.return_value = [
            {"technique_id": "T1566.001", "name": "Test"}
        ]
        mock_loader_class.return_value = mock_loader

        # Execute
        retriever = setup_retrieval_system()

        # Should download and populate
        mock_loader.download.assert_called_once()
        mock_vector_store.populate.assert_called_once()
        assert isinstance(retriever, ATTACKRetriever)
