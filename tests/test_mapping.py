"""Tests for ATT&CK mapping module."""

from unittest.mock import Mock, patch

import pytest
from pydantic import ValidationError

from report2attack.mapping.llm import (
    AnthropicProvider,
    OllamaProvider,
    OpenAIProvider,
    get_llm_provider,
)
from report2attack.mapping.mapper import (
    ATTACKMapper,
    DocumentMappings,
    TechniqueMapping,
)


class TestLLMProviders:
    """Tests for LLM provider implementations."""

    def test_openai_provider_init(self) -> None:
        """Test OpenAI provider initialization."""
        provider = OpenAIProvider(api_key="test_key", model_name="gpt-5-nano")
        assert provider.api_key == "test_key"
        assert provider.model_name == "gpt-5-nano"
        assert provider.temperature == 0.0

    def test_openai_provider_default_model(self) -> None:
        """Test OpenAI provider with default model."""
        provider = OpenAIProvider()
        assert provider.model_name == "gpt-5-nano"

    def test_openai_provider_get_name(self) -> None:
        """Test OpenAI provider name."""
        provider = OpenAIProvider(model_name="gpt-4")
        assert provider.get_name() == "openai-gpt-4"

    def test_anthropic_provider_init(self) -> None:
        """Test Anthropic provider initialization."""
        provider = AnthropicProvider(api_key="test_key")
        assert provider.api_key == "test_key"
        assert provider.model_name == "claude-sonnet-4-5-20250929"

    def test_anthropic_provider_custom_model(self) -> None:
        """Test Anthropic provider with custom model."""
        provider = AnthropicProvider(model_name="claude-3-opus-20240229")
        assert provider.model_name == "claude-3-opus-20240229"

    def test_anthropic_provider_get_name(self) -> None:
        """Test Anthropic provider name."""
        provider = AnthropicProvider()
        assert "anthropic" in provider.get_name()
        assert "claude" in provider.get_name()

    def test_ollama_provider_init(self) -> None:
        """Test Ollama provider initialization."""
        provider = OllamaProvider(model_name="llama2")
        assert provider.model_name == "llama2"
        assert provider.base_url == "http://localhost:11434"

    def test_ollama_provider_custom_url(self) -> None:
        """Test Ollama provider with custom URL."""
        provider = OllamaProvider(base_url="http://custom:8080")
        assert provider.base_url == "http://custom:8080"

    def test_get_llm_provider_openai(self) -> None:
        """Test factory function for OpenAI."""
        provider = get_llm_provider("openai", api_key="test")
        assert isinstance(provider, OpenAIProvider)

    def test_get_llm_provider_anthropic(self) -> None:
        """Test factory function for Anthropic."""
        provider = get_llm_provider("anthropic", api_key="test")
        assert isinstance(provider, AnthropicProvider)

    def test_get_llm_provider_ollama(self) -> None:
        """Test factory function for Ollama."""
        provider = get_llm_provider("ollama")
        assert isinstance(provider, OllamaProvider)

    def test_get_llm_provider_invalid(self) -> None:
        """Test factory function with invalid provider."""
        with pytest.raises(ValueError, match="Unsupported LLM provider"):
            get_llm_provider("invalid_provider")


class TestTechniqueMappingModel:
    """Tests for Pydantic TechniqueMapping model."""

    def test_valid_technique_mapping(self) -> None:
        """Test creating a valid technique mapping."""
        mapping = TechniqueMapping(
            technique_id="T1566.001",
            technique_name="Spearphishing Attachment",
            confidence=0.9,
            evidence="Attackers sent malicious emails",
            tactics=["initial-access"],
        )
        assert mapping.technique_id == "T1566.001"
        assert mapping.confidence == 0.9

    def test_invalid_confidence_too_high(self) -> None:
        """Test that confidence > 1.0 is rejected."""
        with pytest.raises(ValidationError):
            TechniqueMapping(
                technique_id="T1566.001",
                technique_name="Test",
                confidence=1.5,
                evidence="Test",
                tactics=[],
            )

    def test_invalid_confidence_too_low(self) -> None:
        """Test that confidence < 0.0 is rejected."""
        with pytest.raises(ValidationError):
            TechniqueMapping(
                technique_id="T1566.001",
                technique_name="Test",
                confidence=-0.1,
                evidence="Test",
                tactics=[],
            )

    def test_document_mappings_model(self) -> None:
        """Test DocumentMappings model."""
        mappings = DocumentMappings(
            techniques=[
                TechniqueMapping(
                    technique_id="T1566.001",
                    technique_name="Test",
                    confidence=0.8,
                    evidence="Evidence",
                    tactics=["initial-access"],
                )
            ]
        )
        assert len(mappings.techniques) == 1


class TestATTACKMapper:
    """Tests for ATT&CK mapper."""

    def test_initialization(self) -> None:
        """Test mapper initialization."""
        mock_provider = Mock()
        mock_llm = Mock()
        mock_provider.get_model.return_value = mock_llm
        mock_provider.get_name.return_value = "test-provider"

        mapper = ATTACKMapper(mock_provider, min_confidence=0.5)
        assert mapper.llm == mock_llm
        assert mapper.llm_name == "test-provider"
        assert mapper.min_confidence == 0.5

    @patch("report2attack.mapping.mapper.ChatPromptTemplate")
    def test_map_chunk_success(self, mock_prompt_template) -> None:
        """Test successful chunk mapping."""
        # Create mock LLM that returns structured output
        mock_llm = Mock()
        mock_response = Mock()
        mock_response.content = """{"techniques": [
            {
                "technique_id": "T1566.001",
                "technique_name": "Spearphishing Attachment",
                "confidence": 0.9,
                "evidence": "The attackers sent emails with malicious attachments",
                "tactics": ["initial-access"]
            }
        ]}"""
        mock_llm.invoke.return_value = mock_response

        mock_provider = Mock()
        mock_provider.get_model.return_value = mock_llm
        mock_provider.get_name.return_value = "test-provider"

        mapper = ATTACKMapper(mock_provider, min_confidence=0.5)

        # Mock parser
        with patch.object(mapper, "parser") as mock_parser:
            mock_parsed = DocumentMappings(
                techniques=[
                    TechniqueMapping(
                        technique_id="T1566.001",
                        technique_name="Spearphishing Attachment",
                        confidence=0.9,
                        evidence="Test evidence",
                        tactics=["initial-access"],
                    )
                ]
            )
            mock_parser.parse.return_value = mock_parsed

            retrieved_techniques = [
                {
                    "technique_id": "T1566.001",
                    "name": "Spearphishing",
                    "tactics": ["initial-access"],
                    "description": "Test description",
                }
            ]

            result = mapper.map_chunk("Test text about phishing", retrieved_techniques)

            assert len(result) == 1
            assert result[0].technique_id == "T1566.001"
            assert result[0].confidence >= 0.5

    def test_map_chunk_filters_low_confidence(self) -> None:
        """Test that low-confidence mappings are filtered."""
        mock_llm = Mock()
        mock_provider = Mock()
        mock_provider.get_model.return_value = mock_llm
        mock_provider.get_name.return_value = "test"

        mapper = ATTACKMapper(mock_provider, min_confidence=0.7)

        with patch.object(mapper, "parser") as mock_parser:
            mock_parsed = DocumentMappings(
                techniques=[
                    TechniqueMapping(
                        technique_id="T1566.001",
                        technique_name="Test",
                        confidence=0.5,  # Below threshold
                        evidence="Test",
                        tactics=[],
                    )
                ]
            )
            mock_parser.parse.return_value = mock_parsed

            result = mapper.map_chunk("Text", [])
            assert len(result) == 0  # Filtered out

    def test_map_chunk_handles_error(self) -> None:
        """Test error handling in chunk mapping."""
        mock_llm = Mock()
        mock_llm.invoke.side_effect = Exception("LLM error")

        mock_provider = Mock()
        mock_provider.get_model.return_value = mock_llm
        mock_provider.get_name.return_value = "test"

        mapper = ATTACKMapper(mock_provider)
        result = mapper.map_chunk("Text", [])

        # Should return empty list on error
        assert result == []

    def test_map_document(self) -> None:
        """Test mapping entire document with multiple chunks."""
        mock_provider = Mock()
        mock_llm = Mock()
        mock_provider.get_model.return_value = mock_llm
        mock_provider.get_name.return_value = "test"

        mapper = ATTACKMapper(mock_provider)

        # Mock map_chunk to return different techniques
        with patch.object(mapper, "map_chunk") as mock_map_chunk:
            mock_map_chunk.side_effect = [
                [
                    TechniqueMapping(
                        technique_id="T1566.001",
                        technique_name="Test",
                        confidence=0.9,
                        evidence="Evidence 1",
                        tactics=[],
                    )
                ],
                [
                    TechniqueMapping(
                        technique_id="T1566.001",
                        technique_name="Test",
                        confidence=0.8,
                        evidence="Evidence 2",
                        tactics=[],
                    )
                ],
            ]

            chunks = [{"text": "chunk1"}, {"text": "chunk2"}]
            chunk_techniques = [[], []]

            result = mapper.map_document(chunks, chunk_techniques)

            # Should deduplicate and keep highest confidence
            assert len(result) == 1
            assert result[0].confidence == 0.9

    def test_format_techniques_context(self) -> None:
        """Test formatting techniques as context."""
        mock_provider = Mock()
        mock_provider.get_model.return_value = Mock()
        mock_provider.get_name.return_value = "test"

        mapper = ATTACKMapper(mock_provider)

        techniques = [
            {
                "technique_id": "T1566.001",
                "name": "Spearphishing",
                "tactics": ["initial-access"],
                "description": "Test description",
            }
        ]

        context = mapper._format_techniques_context(techniques)
        assert "T1566.001" in context
        assert "Spearphishing" in context

    def test_format_techniques_context_empty(self) -> None:
        """Test formatting empty techniques list."""
        mock_provider = Mock()
        mock_provider.get_model.return_value = Mock()
        mock_provider.get_name.return_value = "test"

        mapper = ATTACKMapper(mock_provider)
        context = mapper._format_techniques_context([])

        assert "No techniques" in context

    def test_deduplicate_mappings(self) -> None:
        """Test deduplication logic."""
        mock_provider = Mock()
        mock_provider.get_model.return_value = Mock()
        mock_provider.get_name.return_value = "test"

        mapper = ATTACKMapper(mock_provider)

        mappings = [
            TechniqueMapping(
                technique_id="T1566.001",
                technique_name="Test",
                confidence=0.8,
                evidence="Evidence 1",
                tactics=[],
            ),
            TechniqueMapping(
                technique_id="T1566.001",
                technique_name="Test",
                confidence=0.9,
                evidence="Evidence 2",
                tactics=[],
            ),
            TechniqueMapping(
                technique_id="T1078",
                technique_name="Test2",
                confidence=0.7,
                evidence="Evidence 3",
                tactics=[],
            ),
        ]

        result = mapper._deduplicate_mappings(mappings)

        assert len(result) == 2  # Two unique techniques
        # Find T1566.001 and verify it kept the higher confidence
        t1566 = next(t for t in result if t.technique_id == "T1566.001")
        assert t1566.confidence == 0.9
