"""Tests for input parsers."""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from report2attack.parsers import (
    InputType,
    detect_input_type,
    parse_input,
)
from report2attack.parsers.pdf import PDFParser
from report2attack.parsers.web import WebParser


class TestWebParser:
    """Tests for WebParser class."""

    @patch("report2attack.parsers.web.trafilatura.fetch_url")
    @patch("report2attack.parsers.web.trafilatura.extract")
    @patch("report2attack.parsers.web.trafilatura.extract_metadata")
    def test_parse_valid_url(
        self, mock_extract_metadata, mock_extract, mock_fetch
    ) -> None:
        """Test parsing a valid URL."""
        # Setup mocks
        mock_fetch.return_value = "<html><body>Test content</body></html>"
        mock_extract.return_value = "Test article content"

        mock_metadata = Mock()
        mock_metadata.title = "Test Article"
        mock_metadata.author = "Test Author"
        mock_metadata.date = "2024-01-01"
        mock_metadata.sitename = "Test Site"
        mock_extract_metadata.return_value = mock_metadata

        # Execute
        parser = WebParser()
        result = parser.parse("https://example.com/article")

        # Assert
        assert result["text"] == "Test article content"
        assert result["title"] == "Test Article"
        assert result["source"] == "https://example.com/article"
        assert result["metadata"]["author"] == "Test Author"

    @patch("report2attack.parsers.web.trafilatura.fetch_url")
    def test_parse_url_fetch_fails(self, mock_fetch) -> None:
        """Test handling failed URL fetch."""
        mock_fetch.return_value = None

        parser = WebParser()
        with pytest.raises(ValueError, match="Failed to fetch content"):
            parser.parse("https://example.com/article")

    @patch("report2attack.parsers.web.trafilatura.fetch_url")
    @patch("report2attack.parsers.web.trafilatura.extract")
    def test_parse_url_no_text_extracted(self, mock_extract, mock_fetch) -> None:
        """Test handling when no text is extracted."""
        mock_fetch.return_value = "<html><body></body></html>"
        mock_extract.return_value = None

        parser = WebParser()
        with pytest.raises(ValueError, match="No text content extracted"):
            parser.parse("https://example.com/article")

    @patch("report2attack.parsers.web.trafilatura.fetch_url")
    @patch("report2attack.parsers.web.trafilatura.extract")
    @patch("report2attack.parsers.web.trafilatura.extract_metadata")
    def test_parse_url_no_metadata(
        self, mock_extract_metadata, mock_extract, mock_fetch
    ) -> None:
        """Test parsing URL with no metadata."""
        mock_fetch.return_value = "<html><body>Content</body></html>"
        mock_extract.return_value = "Test content"
        mock_extract_metadata.return_value = None

        parser = WebParser()
        result = parser.parse("https://example.com/article")

        assert result["text"] == "Test content"
        assert result["title"] is None


class TestPDFParser:
    """Tests for PDFParser class."""

    def test_parse_nonexistent_file(self) -> None:
        """Test parsing non-existent file."""
        parser = PDFParser()
        with pytest.raises(ValueError, match="File not found"):
            parser.parse("/nonexistent/file.pdf")

    def test_parse_non_pdf_file(self, tmp_path: Path) -> None:
        """Test parsing non-PDF file."""
        # Create a text file
        text_file = tmp_path / "test.txt"
        text_file.write_text("Not a PDF")

        parser = PDFParser()
        with pytest.raises(ValueError, match="File is not a PDF"):
            parser.parse(str(text_file))

    @patch("report2attack.parsers.pdf.pypdf.PdfReader")
    def test_parse_with_pypdf_success(self, mock_reader_class, tmp_path: Path) -> None:
        """Test successful parsing with PyPDF."""
        # Create a dummy PDF file
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"%PDF-1.4\ntest")

        # Mock PyPDF reader
        mock_reader = Mock()
        mock_page = Mock()
        mock_page.extract_text.return_value = "Test content from page 1"
        mock_reader.pages = [mock_page]
        mock_reader.metadata = {"/Title": "Test PDF"}
        mock_reader_class.return_value = mock_reader

        parser = PDFParser()
        result = parser.parse(str(pdf_file))

        assert "Test content from page 1" in result["text"]
        assert result["title"] == "Test PDF"
        assert result["metadata"]["parser"] == "pypdf"

    @patch("report2attack.parsers.pdf.pypdf.PdfReader")
    @patch("report2attack.parsers.pdf.pdfplumber.open")
    def test_parse_pypdf_fails_pdfplumber_succeeds(
        self, mock_plumber_open, mock_reader_class, tmp_path: Path
    ) -> None:
        """Test fallback to PDFPlumber when PyPDF fails."""
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"%PDF-1.4\ntest")

        # Make PyPDF fail
        mock_reader_class.side_effect = Exception("PyPDF error")

        # Make PDFPlumber succeed
        mock_pdf = Mock()
        mock_page = Mock()
        mock_page.extract_text.return_value = "Content from PDFPlumber"
        mock_pdf.pages = [mock_page]
        mock_pdf.metadata = {"Title": "Test"}
        mock_plumber_open.return_value.__enter__.return_value = mock_pdf

        parser = PDFParser()
        result = parser.parse(str(pdf_file))

        assert "Content from PDFPlumber" in result["text"]
        assert result["metadata"]["parser"] == "pdfplumber"

    @patch("report2attack.parsers.pdf.pypdf.PdfReader")
    @patch("report2attack.parsers.pdf.pdfplumber.open")
    def test_parse_both_backends_fail(
        self, mock_plumber_open, mock_reader_class, tmp_path: Path
    ) -> None:
        """Test when both PDF backends fail."""
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"%PDF-1.4\ntest")

        mock_reader_class.side_effect = Exception("PyPDF error")
        mock_plumber_open.side_effect = Exception("PDFPlumber error")

        parser = PDFParser()
        with pytest.raises(ValueError, match="Failed to parse PDF with both backends"):
            parser.parse(str(pdf_file))


class TestInputDetection:
    """Tests for input type detection."""

    def test_detect_http_url(self) -> None:
        """Test detection of HTTP URL."""
        assert detect_input_type("http://example.com") == InputType.WEB

    def test_detect_https_url(self) -> None:
        """Test detection of HTTPS URL."""
        assert detect_input_type("https://example.com/article") == InputType.WEB

    def test_detect_pdf_url(self) -> None:
        """Test detection of PDF URL."""
        assert detect_input_type("https://example.com/report.pdf") == InputType.PDF_URL
        assert detect_input_type("http://example.com/file.PDF") == InputType.PDF_URL

    def test_detect_pdf_url_with_query_params(self) -> None:
        """Test detection of PDF URL with query parameters."""
        # URLs with .pdf before query params should be detected as PDF_URL
        assert detect_input_type("https://example.com/report.pdf?download=1") == InputType.PDF_URL

    def test_detect_pdf_file(self, tmp_path: Path) -> None:
        """Test detection of PDF file."""
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"%PDF-1.4")

        assert detect_input_type(str(pdf_file)) == InputType.PDF

    def test_detect_nonexistent_pdf(self) -> None:
        """Test detection of non-existent PDF."""
        result = detect_input_type("/nonexistent/file.pdf")
        assert result == InputType.UNKNOWN

    def test_detect_ambiguous_input(self) -> None:
        """Test detection of ambiguous input."""
        assert detect_input_type("random_text") == InputType.UNKNOWN
        assert detect_input_type("file.txt") == InputType.UNKNOWN


class TestParseInput:
    """Tests for unified parse_input function."""

    @patch("report2attack.parsers.parse_web_url")
    def test_parse_input_web_url(self, mock_parse_web) -> None:
        """Test parsing web URL through parse_input."""
        mock_parse_web.return_value = {"text": "test", "title": "Test"}

        result = parse_input("https://example.com")

        mock_parse_web.assert_called_once_with("https://example.com")
        assert result["text"] == "test"

    @patch("report2attack.parsers.parse_pdf")
    def test_parse_input_pdf_file(self, mock_parse_pdf, tmp_path: Path) -> None:
        """Test parsing PDF through parse_input."""
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"%PDF-1.4")

        mock_parse_pdf.return_value = {"text": "pdf content", "title": "PDF"}

        result = parse_input(str(pdf_file))

        mock_parse_pdf.assert_called_once_with(str(pdf_file))
        assert result["text"] == "pdf content"

    def test_parse_input_unknown_type(self) -> None:
        """Test parsing unknown input type."""
        with pytest.raises(ValueError, match="Cannot determine input type"):
            parse_input("unknown_input")

    @patch("report2attack.parsers.TemporaryPDFDownload")
    @patch("report2attack.parsers.parse_pdf")
    def test_parse_input_pdf_url(self, mock_parse_pdf, mock_temp_download) -> None:
        """Test parsing PDF URL through parse_input."""
        # Mock TemporaryPDFDownload context manager
        mock_temp_download.return_value.__enter__.return_value = "/tmp/downloaded.pdf"
        mock_temp_download.return_value.__exit__.return_value = None

        # Mock parse_pdf to return result
        mock_parse_pdf.return_value = {
            "text": "Downloaded PDF content",
            "title": "Test PDF",
            "source": "/tmp/downloaded.pdf",
            "metadata": {},
        }

        result = parse_input("https://example.com/report.pdf")

        # Verify download was initiated
        mock_temp_download.assert_called_once_with("https://example.com/report.pdf")

        # Verify PDF was parsed
        mock_parse_pdf.assert_called_once_with("/tmp/downloaded.pdf")

        # Verify source URL is preserved (not temp file path)
        assert result["source"] == "https://example.com/report.pdf"
        assert result["text"] == "Downloaded PDF content"
