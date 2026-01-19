"""Tests for text preprocessing module."""

from report2attack.preprocessing.text import (
    TextChunker,
    TextPreprocessor,
    chunk_text,
    preprocess_text,
)


class TestTextPreprocessor:
    """Tests for TextPreprocessor class."""

    def test_clean_html_entities(self) -> None:
        """Test HTML entity decoding."""
        preprocessor = TextPreprocessor()
        text = "AT&amp;T uses &lt;script&gt; tags"
        cleaned = preprocessor.clean(text)
        assert "AT&T" in cleaned
        assert "&amp;" not in cleaned
        assert "<script>" not in cleaned

    def test_normalize_whitespace(self) -> None:
        """Test whitespace normalization."""
        preprocessor = TextPreprocessor()
        text = "Multiple    spaces\n\n\n\nand lines"
        cleaned = preprocessor.clean(text)
        assert "  " not in cleaned
        assert "\n\n\n" not in cleaned

    def test_validate_empty(self) -> None:
        """Test validation of empty text."""
        preprocessor = TextPreprocessor()
        is_valid, msg = preprocessor.validate("")
        assert not is_valid
        assert msg == "Empty content"

    def test_validate_too_short(self) -> None:
        """Test validation of short text."""
        preprocessor = TextPreprocessor()
        is_valid, msg = preprocessor.validate("Short", min_length=100)
        assert not is_valid
        assert "too short" in msg.lower()

    def test_validate_good_text(self) -> None:
        """Test validation of good text."""
        preprocessor = TextPreprocessor()
        text = "This is a reasonably long piece of text that should pass validation checks." * 2
        is_valid, msg = preprocessor.validate(text)
        assert is_valid
        assert msg is None


class TestTextChunker:
    """Tests for TextChunker class."""

    def test_short_text_no_chunking(self) -> None:
        """Test that short text is not chunked."""
        chunker = TextChunker(chunk_size=500)
        text = "This is a short text."
        chunks = chunker.chunk(text)
        assert len(chunks) == 1
        assert chunks[0].text == text

    def test_chunk_token_counting(self) -> None:
        """Test token counting."""
        chunker = TextChunker()
        text = "Hello world"
        count = chunker.count_tokens(text)
        assert isinstance(count, int)
        assert count > 0

    def test_chunk_metadata(self) -> None:
        """Test chunk metadata."""
        chunker = TextChunker(chunk_size=50)
        text = "This is a test. " * 20
        chunks = chunker.chunk(text, source_document="test.pdf")

        assert len(chunks) > 1
        for i, chunk in enumerate(chunks):
            assert chunk.chunk_index == i
            assert chunk.source_document == "test.pdf"
            assert chunk.token_count > 0


    def test_long_text_chunking(self) -> None:
        """Test chunking of very long text."""
        chunker = TextChunker(chunk_size=100, chunk_overlap=20)
        # Create a long text with clear sentence boundaries
        text = ". ".join([f"Sentence number {i}" for i in range(200)])
        chunks = chunker.chunk(text)

        assert len(chunks) > 1
        # Verify overlap exists between consecutive chunks
        for i in range(len(chunks) - 1):
            current_end = chunks[i].text[-50:]
            next_start = chunks[i + 1].text[:50]
            # There should be some overlap
            assert len(set(current_end.split()) & set(next_start.split())) > 0

    def test_chunk_indices(self) -> None:
        """Test that chunk indices are sequential."""
        chunker = TextChunker(chunk_size=50)
        text = "Test sentence. " * 50
        chunks = chunker.chunk(text)

        for i, chunk in enumerate(chunks):
            assert chunk.chunk_index == i

    def test_empty_text_chunking(self) -> None:
        """Test chunking empty text."""
        chunker = TextChunker()
        chunks = chunker.chunk("")
        assert len(chunks) == 1
        assert chunks[0].text == ""


class TestTextValidation:
    """Tests for text validation."""

    def test_validate_high_non_ascii(self) -> None:
        """Test validation with high percentage of non-ASCII characters."""
        preprocessor = TextPreprocessor()
        # Text with lots of unicode
        text = "数字123测试文本" * 20
        is_valid, msg = preprocessor.validate(text)
        assert is_valid  # Should be valid but with warning
        assert msg is not None
        assert "non-ASCII" in msg

    def test_validate_unicode_text(self) -> None:
        """Test validation of unicode text."""
        preprocessor = TextPreprocessor()
        text = "Test with émojis 🎉 and spëcial chärs" * 10
        is_valid, msg = preprocessor.validate(text)
        assert is_valid


class TestConvenienceFunctions:
    """Tests for module-level convenience functions."""

    def test_preprocess_text(self) -> None:
        """Test preprocess_text function."""
        text = "  HTML&nbsp;entities  "
        cleaned = preprocess_text(text)
        assert cleaned.strip() == cleaned
        assert "nbsp" not in cleaned

    def test_chunk_text(self) -> None:
        """Test chunk_text function."""
        text = "Sentence one. " * 100
        chunks = chunk_text(text, chunk_size=50)
        assert len(chunks) > 1
        assert all(isinstance(c.text, str) for c in chunks)

    def test_chunk_text_with_source(self) -> None:
        """Test chunk_text with source document."""
        text = "Test content. " * 50
        chunks = chunk_text(text, source_document="test.pdf")
        assert all(c.source_document == "test.pdf" for c in chunks)
