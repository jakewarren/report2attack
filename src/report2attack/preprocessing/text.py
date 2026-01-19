"""Text preprocessing and chunking utilities."""

import html
import re
from dataclasses import dataclass

import tiktoken


@dataclass
class TextChunk:
    """Represents a chunk of text with metadata."""

    text: str
    chunk_index: int
    start_char: int
    end_char: int
    token_count: int
    source_document: str | None = None
    page_number: int | None = None


class TextPreprocessor:
    """Handles text cleaning and normalization."""

    def __init__(self) -> None:
        """Initialize the text preprocessor."""
        self.boilerplate_patterns = [
            r"©\s*\d{4}.*?rights reserved",
            r"this document is.*?confidential",
            r"for internal use only",
        ]

    def clean(self, text: str) -> str:
        """
        Clean and normalize text.

        Args:
            text: Raw text to clean

        Returns:
            Cleaned text
        """
        # Decode HTML entities
        text = html.unescape(text)

        # Remove any remaining HTML tags
        text = re.sub(r"<[^>]+>", "", text)

        # Normalize whitespace
        text = re.sub(r"\s+", " ", text)
        text = re.sub(r"\n\s*\n\s*\n+", "\n\n", text)

        # Remove boilerplate (optional - configurable)
        # for pattern in self.boilerplate_patterns:
        #     text = re.sub(pattern, "", text, flags=re.IGNORECASE)

        # Strip leading/trailing whitespace
        text = text.strip()

        return text

    def validate(self, text: str, min_length: int = 100) -> tuple[bool, str | None]:
        """
        Validate text quality.

        Args:
            text: Text to validate
            min_length: Minimum character length

        Returns:
            Tuple of (is_valid, warning_message)
        """
        if not text:
            return False, "Empty content"

        if len(text) < min_length:
            return False, f"Content too short (< {min_length} characters)"

        # Check for high percentage of non-ASCII
        non_ascii_ratio = sum(1 for c in text if ord(c) > 127) / len(text)
        if non_ascii_ratio > 0.5:
            return True, "High percentage of non-ASCII characters - may indicate encoding issues"

        return True, None


class TextChunker:
    """Handles document chunking with token-based splitting."""

    def __init__(
        self,
        chunk_size: int = 500,
        chunk_overlap: int = 50,
        encoding_name: str = "cl100k_base",
    ) -> None:
        """
        Initialize the text chunker.

        Args:
            chunk_size: Maximum tokens per chunk
            chunk_overlap: Token overlap between chunks
            encoding_name: Tokenizer encoding to use
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.encoding = tiktoken.get_encoding(encoding_name)

    def count_tokens(self, text: str) -> int:
        """Count tokens in text."""
        return len(self.encoding.encode(text))

    def chunk(self, text: str, source_document: str | None = None) -> list[TextChunk]:
        """
        Split text into chunks with overlap.

        Args:
            text: Text to chunk
            source_document: Optional source document identifier

        Returns:
            List of TextChunk objects
        """
        total_tokens = self.count_tokens(text)

        # If text is short enough, return as single chunk
        if total_tokens <= self.chunk_size:
            return [
                TextChunk(
                    text=text,
                    chunk_index=0,
                    start_char=0,
                    end_char=len(text),
                    token_count=total_tokens,
                    source_document=source_document,
                )
            ]

        chunks: list[TextChunk] = []
        sentences = self._split_into_sentences(text)

        current_chunk_text = ""
        current_chunk_start = 0
        chunk_index = 0

        for sentence in sentences:
            # Check if adding this sentence would exceed chunk size
            test_chunk = current_chunk_text + " " + sentence if current_chunk_text else sentence
            test_tokens = self.count_tokens(test_chunk)

            if test_tokens > self.chunk_size and current_chunk_text:
                # Save current chunk
                chunks.append(
                    TextChunk(
                        text=current_chunk_text.strip(),
                        chunk_index=chunk_index,
                        start_char=current_chunk_start,
                        end_char=current_chunk_start + len(current_chunk_text),
                        token_count=self.count_tokens(current_chunk_text),
                        source_document=source_document,
                    )
                )

                # Start new chunk with overlap
                overlap_text = self._get_overlap_text(current_chunk_text)
                current_chunk_text = overlap_text + " " + sentence if overlap_text else sentence
                current_chunk_start += len(current_chunk_text) - len(overlap_text)
                chunk_index += 1
            else:
                current_chunk_text = test_chunk

        # Add final chunk
        if current_chunk_text:
            chunks.append(
                TextChunk(
                    text=current_chunk_text.strip(),
                    chunk_index=chunk_index,
                    start_char=current_chunk_start,
                    end_char=current_chunk_start + len(current_chunk_text),
                    token_count=self.count_tokens(current_chunk_text),
                    source_document=source_document,
                )
            )

        return chunks

    def _split_into_sentences(self, text: str) -> list[str]:
        """Split text into sentences at semantic boundaries."""
        # Simple sentence splitting - can be enhanced with spacy if needed
        sentences = re.split(r"(?<=[.!?])\s+", text)
        return [s.strip() for s in sentences if s.strip()]

    def _get_overlap_text(self, text: str) -> str:
        """Get overlap text from end of current chunk."""
        sentences = self._split_into_sentences(text)
        overlap_text = ""

        # Build overlap from end of chunk
        for sentence in reversed(sentences):
            test_overlap = sentence + " " + overlap_text if overlap_text else sentence
            if self.count_tokens(test_overlap) > self.chunk_overlap:
                break
            overlap_text = test_overlap

        return overlap_text.strip()


def preprocess_text(text: str) -> str:
    """
    Convenience function to preprocess text.

    Args:
        text: Raw text to preprocess

    Returns:
        Cleaned text
    """
    preprocessor = TextPreprocessor()
    return preprocessor.clean(text)


def chunk_text(
    text: str,
    chunk_size: int = 500,
    chunk_overlap: int = 50,
    source_document: str | None = None,
) -> list[TextChunk]:
    """
    Convenience function to chunk text.

    Args:
        text: Text to chunk
        chunk_size: Maximum tokens per chunk
        chunk_overlap: Token overlap between chunks
        source_document: Optional source document identifier

    Returns:
        List of TextChunk objects
    """
    chunker = TextChunker(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    return chunker.chunk(text, source_document=source_document)
