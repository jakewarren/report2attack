"""Input parsers for web and PDF documents."""

from enum import Enum
from pathlib import Path

from .pdf import parse_pdf
from .pdf_url import TemporaryPDFDownload
from .web import parse_web_url


class InputType(Enum):
    """Supported input types."""

    WEB = "web"
    PDF = "pdf"
    PDF_URL = "pdf_url"
    UNKNOWN = "unknown"


def detect_input_type(input_str: str) -> InputType:
    """
    Detect input type from string.

    Args:
        input_str: Input string (URL or file path)

    Returns:
        InputType enum value
    """
    # Check if it's a URL
    if input_str.startswith(("http://", "https://")):
        # Check if URL points to a PDF (before query params or fragments)
        # Extract path component before '?' or '#'
        url_path = input_str.split('?')[0].split('#')[0]
        if url_path.lower().endswith(".pdf"):
            return InputType.PDF_URL
        return InputType.WEB

    # Check if it's a PDF file
    if input_str.endswith(".pdf") and Path(input_str).exists():
        return InputType.PDF

    # Check if it's a file path that exists
    path = Path(input_str)
    if path.exists() and path.suffix.lower() == ".pdf":
        return InputType.PDF

    return InputType.UNKNOWN


def parse_input(input_str: str) -> dict[str, str | None]:
    """
    Parse input automatically based on type detection.

    Args:
        input_str: Input string (URL or file path)

    Returns:
        Dictionary with extracted content and metadata

    Raises:
        ValueError: If input type cannot be determined or parsing fails
    """
    input_type = detect_input_type(input_str)

    if input_type == InputType.WEB:
        return parse_web_url(input_str)
    elif input_type == InputType.PDF:
        return parse_pdf(input_str)
    elif input_type == InputType.PDF_URL:
        # Download PDF from URL and parse
        with TemporaryPDFDownload(input_str) as temp_pdf_path:
            result = parse_pdf(temp_pdf_path)
            # Update source to be the original URL, not temp file path
            result["source"] = input_str
            return result
    else:
        raise ValueError(
            f"Cannot determine input type for: {input_str}\n"
            f"Expected a URL (http:// or https://) or a PDF file path"
        )


__all__ = [
    "parse_input",
    "parse_web_url",
    "parse_pdf",
    "detect_input_type",
    "InputType",
]
