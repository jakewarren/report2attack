"""PDF document parser with multiple backend support."""

from datetime import datetime
from pathlib import Path

import pdfplumber
import pypdf


class PDFParser:
    """Parser for extracting text from PDF documents."""

    def parse(self, file_path: str) -> dict[str, str | None]:
        """
        Extract text content from a PDF file.

        Args:
            file_path: Path to the PDF file

        Returns:
            Dictionary containing:
                - text: Extracted PDF text
                - title: Document title (filename if not in metadata)
                - source: File path
                - metadata: Additional metadata (page count, etc.)

        Raises:
            ValueError: If file doesn't exist, is not a PDF, or cannot be parsed
        """
        path = Path(file_path)

        # Validate file exists and is PDF
        if not path.exists():
            raise ValueError(f"File not found: {file_path}")

        if not path.suffix.lower() == ".pdf":
            raise ValueError(f"File is not a PDF: {file_path}")

        # Try PyPDF first (faster for most PDFs)
        try:
            return self._parse_with_pypdf(path)
        except Exception as pypdf_error:
            # Fallback to PDFPlumber for complex layouts
            try:
                return self._parse_with_pdfplumber(path)
            except Exception as plumber_error:
                raise ValueError(
                    f"Failed to parse PDF with both backends.\n"
                    f"PyPDF error: {pypdf_error}\n"
                    f"PDFPlumber error: {plumber_error}"
                ) from plumber_error

    def _parse_with_pypdf(self, path: Path) -> dict[str, str | None]:
        """Parse PDF using PyPDF."""
        pages: list[str] = []

        with open(path, "rb") as file:
            reader = pypdf.PdfReader(file)

            # Extract metadata
            metadata = reader.metadata
            title = metadata.get("/Title") if metadata else None

            # Extract text from all pages
            for page_num, page in enumerate(reader.pages, 1):
                text = page.extract_text()
                if text.strip():
                    pages.append(f"[Page {page_num}]\n{text}")

        if not pages:
            raise ValueError("No text content extracted from PDF")

        full_text = "\n\n".join(pages)

        return {
            "text": full_text,
            "title": title if title else path.stem,
            "source": str(path.absolute()),
            "metadata": {
                "page_count": len(pages),
                "parser": "pypdf",
                "extracted_at": datetime.utcnow().isoformat(),
            },
        }

    def _parse_with_pdfplumber(self, path: Path) -> dict[str, str | None]:
        """Parse PDF using PDFPlumber (better for complex layouts)."""
        pages: list[str] = []

        with pdfplumber.open(path) as pdf:
            # Extract text from all pages
            for page_num, page in enumerate(pdf.pages, 1):
                text = page.extract_text()
                if text and text.strip():
                    pages.append(f"[Page {page_num}]\n{text}")

            # Try to get metadata
            title = pdf.metadata.get("Title") if pdf.metadata else None

        if not pages:
            raise ValueError("No text content extracted from PDF")

        full_text = "\n\n".join(pages)

        return {
            "text": full_text,
            "title": title if title else path.stem,
            "source": str(path.absolute()),
            "metadata": {
                "page_count": len(pages),
                "parser": "pdfplumber",
                "extracted_at": datetime.utcnow().isoformat(),
            },
        }


def parse_pdf(file_path: str) -> dict[str, str | None]:
    """
    Convenience function to parse a PDF file.

    Args:
        file_path: Path to the PDF file

    Returns:
        Dictionary with extracted content and metadata

    Raises:
        ValueError: If file cannot be parsed
    """
    parser = PDFParser()
    return parser.parse(file_path)
