"""Tests for PDF URL download functionality."""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from report2attack.parsers.pdf_url import TemporaryPDFDownload, _validate_url_safety


class TestURLValidation:
    """Tests for URL safety validation."""

    def test_valid_http_url(self) -> None:
        """Test that valid HTTP URLs are accepted."""
        _validate_url_safety("http://example.com/file.pdf")

    def test_valid_https_url(self) -> None:
        """Test that valid HTTPS URLs are accepted."""
        _validate_url_safety("https://example.com/file.pdf")

    def test_invalid_scheme_file(self) -> None:
        """Test that file:// URLs are rejected."""
        with pytest.raises(ValueError, match="Invalid URL scheme"):
            _validate_url_safety("file:///etc/passwd")

    def test_invalid_scheme_ftp(self) -> None:
        """Test that ftp:// URLs are rejected."""
        with pytest.raises(ValueError, match="Invalid URL scheme"):
            _validate_url_safety("ftp://example.com/file.pdf")

    def test_localhost_rejection(self) -> None:
        """Test that localhost URLs are rejected."""
        with pytest.raises(ValueError, match="localhost"):
            _validate_url_safety("http://localhost/file.pdf")

    def test_127_0_0_1_rejection(self) -> None:
        """Test that 127.0.0.1 is rejected."""
        with pytest.raises(ValueError, match="localhost"):
            _validate_url_safety("http://127.0.0.1/file.pdf")

    def test_private_ip_rejection(self) -> None:
        """Test that private IPs are rejected."""
        with pytest.raises(ValueError, match="private IP"):
            _validate_url_safety("http://192.168.1.1/file.pdf")

        with pytest.raises(ValueError, match="private IP"):
            _validate_url_safety("http://10.0.0.1/file.pdf")

        with pytest.raises(ValueError, match="private IP"):
            _validate_url_safety("http://172.16.0.1/file.pdf")

    def test_ipv6_loopback_rejection(self) -> None:
        """Test that IPv6 loopback is rejected."""
        with pytest.raises(ValueError, match="localhost"):
            _validate_url_safety("http://[::1]/file.pdf")


class TestTemporaryPDFDownload:
    """Tests for TemporaryPDFDownload context manager."""

    @pytest.fixture
    def mock_pdf_content(self) -> bytes:
        """Sample PDF content with valid header."""
        return b"%PDF-1.4\nSample PDF content for testing"

    @pytest.fixture
    def mock_head_response(self) -> Mock:
        """Mock HEAD request response."""
        response = Mock()
        response.headers = {
            "Content-Type": "application/pdf",
            "Content-Length": "1024",
        }
        response.raise_for_status = Mock()
        return response

    @pytest.fixture
    def mock_get_response(self, mock_pdf_content: bytes) -> Mock:
        """Mock GET request response."""
        response = Mock()
        response.raise_for_status = Mock()
        response.iter_content = Mock(return_value=[mock_pdf_content])
        return response

    def test_successful_download(
        self, mock_head_response: Mock, mock_get_response: Mock, mock_pdf_content: bytes
    ) -> None:
        """Test successful PDF download and cleanup."""
        with patch("report2attack.parsers.pdf_url.requests.head") as mock_head:
            with patch("report2attack.parsers.pdf_url.requests.get") as mock_get:
                mock_head.return_value = mock_head_response
                mock_get.return_value = mock_get_response

                with TemporaryPDFDownload("https://example.com/test.pdf") as temp_path:
                    # File should exist and be readable
                    assert Path(temp_path).exists()
                    with open(temp_path, "rb") as f:
                        content = f.read()
                        assert content == mock_pdf_content

                # File should be cleaned up after context exit
                assert not Path(temp_path).exists()

    def test_file_too_large(self, mock_head_response: Mock) -> None:
        """Test rejection of files exceeding size limit."""
        # Set Content-Length to 150MB
        mock_head_response.headers["Content-Length"] = str(150 * 1024 * 1024)

        with patch("report2attack.parsers.pdf_url.requests.head") as mock_head:
            mock_head.return_value = mock_head_response

            with pytest.raises(ValueError, match="too large"):
                with TemporaryPDFDownload("https://example.com/large.pdf"):
                    pass

    def test_download_size_exceeded(
        self, mock_head_response: Mock, mock_get_response: Mock
    ) -> None:
        """Test rejection when download exceeds max size during streaming."""
        # HEAD says small file, but actual download is huge
        mock_head_response.headers["Content-Length"] = "1024"

        # Create large chunks that exceed limit
        large_chunk = b"x" * (50 * 1024 * 1024)  # 50MB chunks
        mock_get_response.iter_content = Mock(return_value=[large_chunk, large_chunk, large_chunk])

        with patch("report2attack.parsers.pdf_url.requests.head") as mock_head:
            with patch("report2attack.parsers.pdf_url.requests.get") as mock_get:
                mock_head.return_value = mock_head_response
                mock_get.return_value = mock_get_response

                with pytest.raises(ValueError, match="exceeded.*size limit"):
                    with TemporaryPDFDownload("https://example.com/test.pdf"):
                        pass

    def test_http_error(self, mock_head_response: Mock) -> None:
        """Test handling of HTTP errors."""
        with patch("report2attack.parsers.pdf_url.requests") as mock_requests:
            # Create RequestException
            request_exception = Exception("404 Not Found")
            mock_requests.RequestException = Exception
            mock_head_response.raise_for_status = Mock(side_effect=request_exception)
            mock_requests.head.return_value = mock_head_response

            with pytest.raises(ValueError, match="Failed to access PDF URL"):
                with TemporaryPDFDownload("https://example.com/missing.pdf"):
                    pass

    def test_timeout_error(self) -> None:
        """Test handling of timeout errors."""
        with patch("report2attack.parsers.pdf_url.requests") as mock_requests:
            # Create Timeout exception
            timeout_exception = Exception("Connection timeout")
            mock_requests.Timeout = Exception
            mock_requests.RequestException = Exception

            mock_head_resp = Mock(
                headers={"Content-Type": "application/pdf"},
                raise_for_status=Mock(),
            )
            mock_requests.head.return_value = mock_head_resp
            mock_requests.get.side_effect = timeout_exception

            with pytest.raises(ValueError, match="Download timeout"):
                with TemporaryPDFDownload("https://example.com/slow.pdf"):
                    pass

    def test_invalid_pdf_magic_bytes(
        self, mock_head_response: Mock, mock_get_response: Mock
    ) -> None:
        """Test rejection of non-PDF files."""
        # Return HTML content instead of PDF
        mock_get_response.iter_content = Mock(
            return_value=[b"<html><body>Not a PDF</body></html>"]
        )

        with patch("report2attack.parsers.pdf_url.requests.head") as mock_head:
            with patch("report2attack.parsers.pdf_url.requests.get") as mock_get:
                mock_head.return_value = mock_head_response
                mock_get.return_value = mock_get_response

                with pytest.raises(ValueError, match="not a valid PDF"):
                    with TemporaryPDFDownload("https://example.com/fake.pdf"):
                        pass

    def test_wrong_content_type_but_valid_pdf(
        self, mock_head_response: Mock, mock_get_response: Mock, mock_pdf_content: bytes
    ) -> None:
        """Test that wrong Content-Type doesn't fail if file is actually PDF."""
        # Server returns wrong Content-Type
        mock_head_response.headers["Content-Type"] = "text/html"

        with patch("report2attack.parsers.pdf_url.requests.head") as mock_head:
            with patch("report2attack.parsers.pdf_url.requests.get") as mock_get:
                mock_head.return_value = mock_head_response
                mock_get.return_value = mock_get_response

                # Should succeed because we validate magic bytes
                with TemporaryPDFDownload("https://example.com/test.pdf") as temp_path:
                    assert Path(temp_path).exists()

    def test_cleanup_on_exception(
        self, mock_head_response: Mock, mock_get_response: Mock
    ) -> None:
        """Test that temp file is cleaned up even when exception occurs."""
        temp_path = None

        with patch("report2attack.parsers.pdf_url.requests.head") as mock_head:
            with patch("report2attack.parsers.pdf_url.requests.get") as mock_get:
                mock_head.return_value = mock_head_response
                # Make GET fail with invalid PDF content
                mock_get_response.iter_content = Mock(
                    return_value=[b"Not a PDF"]
                )
                mock_get.return_value = mock_get_response

                try:
                    with TemporaryPDFDownload("https://example.com/test.pdf") as path:
                        temp_path = path
                except ValueError:
                    pass  # Expected

                # File should be cleaned up despite exception
                if temp_path:
                    assert not Path(temp_path).exists()

    def test_redirects_followed(
        self, mock_head_response: Mock, mock_get_response: Mock
    ) -> None:
        """Test that redirects are followed correctly."""
        with patch("report2attack.parsers.pdf_url.requests.head") as mock_head:
            with patch("report2attack.parsers.pdf_url.requests.get") as mock_get:
                mock_head.return_value = mock_head_response
                mock_get.return_value = mock_get_response

                with TemporaryPDFDownload("https://example.com/redirect.pdf"):
                    pass

                # Verify allow_redirects was set
                assert mock_head.call_args.kwargs.get("allow_redirects") is True
                assert mock_get.call_args.kwargs.get("allow_redirects") is True

    def test_custom_timeout(self, mock_head_response: Mock, mock_get_response: Mock) -> None:
        """Test custom timeout configuration."""
        with patch("report2attack.parsers.pdf_url.requests.head") as mock_head:
            with patch("report2attack.parsers.pdf_url.requests.get") as mock_get:
                mock_head.return_value = mock_head_response
                mock_get.return_value = mock_get_response

                with TemporaryPDFDownload("https://example.com/test.pdf", timeout=60):
                    pass

                # Verify timeout was passed correctly
                assert mock_head.call_args.kwargs.get("timeout") == 60
                assert mock_get.call_args.kwargs.get("timeout") == 60

    def test_streaming_enabled(
        self, mock_head_response: Mock, mock_get_response: Mock
    ) -> None:
        """Test that streaming is enabled for downloads."""
        with patch("report2attack.parsers.pdf_url.requests.head") as mock_head:
            with patch("report2attack.parsers.pdf_url.requests.get") as mock_get:
                mock_head.return_value = mock_head_response
                mock_get.return_value = mock_get_response

                with TemporaryPDFDownload("https://example.com/test.pdf"):
                    pass

                # Verify streaming was enabled
                assert mock_get.call_args.kwargs.get("stream") is True
