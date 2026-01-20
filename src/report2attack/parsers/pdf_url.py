"""PDF URL download and parsing utilities."""

import ipaddress
import tempfile
from pathlib import Path
from urllib.parse import urlparse

import requests

# Modern browser User-Agent to avoid bot detection (Chrome 144, January 2026)
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.7559.59 Safari/537.36"


def _validate_url_safety(url: str) -> None:
    """
    Validate URL to prevent SSRF attacks.

    Args:
        url: URL to validate

    Raises:
        ValueError: If URL is unsafe (localhost, private IP, non-HTTP(S))
    """
    parsed = urlparse(url)

    # Only allow HTTP and HTTPS schemes
    if parsed.scheme not in ("http", "https"):
        raise ValueError(f"Invalid URL scheme '{parsed.scheme}': only http:// and https:// are allowed")

    hostname = parsed.hostname
    if not hostname:
        raise ValueError("Invalid URL: no hostname found")

    # Block localhost
    if hostname.lower() in ("localhost", "127.0.0.1", "::1", "0.0.0.0"):
        raise ValueError("Access to localhost URLs is not allowed")

    # Try to parse as IP address and check if it's private
    try:
        # This is a basic check - doesn't actually resolve DNS
        # Parse as IP address to detect private ranges
        ip = ipaddress.ip_address(hostname)
    except ValueError:
        # Not an IP address, it's a hostname - this is fine
        # We'll let DNS resolution happen naturally during the request
        pass
    else:
        # Successfully parsed as IP - check if it's private/loopback
        if ip.is_private or ip.is_loopback or ip.is_link_local:
            raise ValueError(f"Access to private IP addresses is not allowed: {hostname}")


class TemporaryPDFDownload:
    """Context manager for downloading and managing temporary PDF files."""

    def __init__(self, url: str, timeout: int = 30, max_size_mb: int = 100):
        """
        Initialize PDF download context manager.

        Args:
            url: URL of the PDF to download
            timeout: Request timeout in seconds
            max_size_mb: Maximum file size in megabytes
        """
        self.url = url
        self.timeout = timeout
        self.max_size_mb = max_size_mb
        self.temp_file: tempfile.NamedTemporaryFile | None = None
        self.file_path: str | None = None

    def __enter__(self) -> str:
        """
        Download PDF and return temporary file path.

        Returns:
            Path to downloaded temporary PDF file

        Raises:
            ValueError: If download fails or file is too large
        """
        # Validate URL safety first (prevent SSRF attacks)
        _validate_url_safety(self.url)

        # Create temporary file with .pdf suffix
        self.temp_file = tempfile.NamedTemporaryFile(
            mode="wb", suffix=".pdf", delete=False
        )
        self.file_path = self.temp_file.name

        # Set headers with modern browser User-Agent
        headers = {"User-Agent": USER_AGENT}

        # Create session with 5-redirect limit per spec
        session = requests.Session()
        session.max_redirects = 5

        try:
            # Perform HEAD request to validate before downloading
            try:
                head_response = session.head(
                    self.url, headers=headers, timeout=self.timeout, allow_redirects=True
                )
                head_response.raise_for_status()
            except requests.RequestException as e:
                raise ValueError(f"Failed to access PDF URL: {e}") from e

            # Check Content-Length if available
            content_length = head_response.headers.get("Content-Length")
            if content_length:
                try:
                    size_mb = int(content_length) / (1024 * 1024)
                except ValueError:
                    # Malformed Content-Length header - continue without size check
                    # Will be validated during download streaming
                    pass
                else:
                    if size_mb > self.max_size_mb:
                        raise ValueError(
                            f"PDF file too large: {size_mb:.1f}MB exceeds {self.max_size_mb}MB limit"
                        )

            # Check Content-Type (warn if not PDF but continue)
            content_type = head_response.headers.get("Content-Type", "")
            if content_type and "application/pdf" not in content_type.lower():
                # Don't fail here - some servers return wrong Content-Type
                pass

            # Download with streaming to avoid loading entire file into memory
            try:
                response = session.get(
                    self.url, headers=headers, timeout=self.timeout, stream=True, allow_redirects=True
                )
                response.raise_for_status()
            except requests.Timeout as e:
                raise ValueError(
                    f"Download timeout after {self.timeout}s: {self.url}"
                ) from e
            except requests.RequestException as e:
                raise ValueError(f"Failed to download PDF: {e}") from e

            # Stream content to temp file
            downloaded_size = 0
            max_size_bytes = self.max_size_mb * 1024 * 1024

            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    downloaded_size += len(chunk)
                    if downloaded_size > max_size_bytes:
                        raise ValueError(
                            f"PDF download exceeded {self.max_size_mb}MB size limit"
                        )
                    self.temp_file.write(chunk)

            self.temp_file.close()

            # Validate PDF magic bytes
            with open(self.file_path, "rb") as f:
                header = f.read(5)
                if not header.startswith(b"%PDF-"):
                    raise ValueError(
                        f"Downloaded file is not a valid PDF (URL may not point to PDF): {self.url}"
                    )

            return self.file_path

        except Exception:
            # Clean up on error
            if self.temp_file:
                self.temp_file.close()
            if self.file_path and Path(self.file_path).exists():
                Path(self.file_path).unlink()
            raise

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Clean up temporary file on exit."""
        if self.temp_file:
            self.temp_file.close()
        if self.file_path and Path(self.file_path).exists():
            try:
                Path(self.file_path).unlink()
            except Exception:
                # Best effort cleanup - don't raise in __exit__
                pass
