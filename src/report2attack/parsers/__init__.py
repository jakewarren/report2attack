"""Input parsers for web and PDF documents."""

from enum import Enum
from pathlib import Path

import requests

from .pdf import parse_pdf
from .pdf_url import TemporaryPDFDownload, USER_AGENT
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

    Uses HTTP HEAD probing to detect PDF content type when URL doesn't end in .pdf.

    Args:
        input_str: Input string (URL or file path)

    Returns:
        InputType enum value
    """
    # Check if it's a URL
    if input_str.startswith(("http://", "https://")):
        # First check URL suffix (fast path)
        url_path = input_str.split('?')[0].split('#')[0]
        if url_path.lower().endswith(".pdf"):
            return InputType.PDF_URL

        # Perform HTTP HEAD probe to check Content-Type
        # This handles cases where PDFs don't have .pdf extension
        try:
            session = requests.Session()
            session.max_redirects = 5  # Enforce 5-redirect limit per spec

            headers = {"User-Agent": USER_AGENT}

            # Try HEAD request first (lightweight)
            try:
                response = session.head(
                    input_str,
                    headers=headers,
                    timeout=5,  # Quick probe
                    allow_redirects=True
                )
                content_type = response.headers.get("Content-Type", "")
            except (requests.RequestException, requests.exceptions.InvalidHeader):
                # HEAD failed, try GET with minimal range
                try:
                    headers["Range"] = "bytes=0-0"  # Request just 1 byte
                    response = session.get(
                        input_str,
                        headers=headers,
                        timeout=5,
                        allow_redirects=True,
                        stream=True  # Don't download body
                    )
                    response.close()  # Close immediately
                    content_type = response.headers.get("Content-Type", "")
                except requests.RequestException:
                    # Network error - fall back to web parsing
                    return InputType.WEB

            # Check if Content-Type indicates PDF
            if content_type and "application/pdf" in content_type.lower():
                return InputType.PDF_URL

        except Exception:
            # Any unexpected error - fall back to web parsing
            pass

        # Default to web parsing for HTTP(S) URLs
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
