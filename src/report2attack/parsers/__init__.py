"""Input parsers for web and PDF documents."""

from enum import Enum
from pathlib import Path

from .pdf import parse_pdf
from .web import parse_web_url


class InputType(Enum):
    """Supported input types."""

    WEB = "web"
    PDF = "pdf"
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
