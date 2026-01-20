"""Web article parser using trafilatura."""

from datetime import datetime

import trafilatura

# Modern browser User-Agent to avoid bot detection (Chrome 144, January 2026)
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.7559.59 Safari/537.36"


class WebParser:
    """Parser for extracting clean text from web URLs."""

    def parse(self, url: str) -> dict[str, str | None]:
        """
        Extract clean text content from a web URL.

        Args:
            url: The URL to parse

        Returns:
            Dictionary containing:
                - text: Extracted article text
                - title: Article title
                - source: Original URL
                - metadata: Additional metadata (author, date, etc.)

        Raises:
            ValueError: If URL is invalid or unreachable
        """
        try:
            # Download content with custom User-Agent
            config = trafilatura.settings.use_config()
            config.set("DEFAULT", "USER_AGENTS", USER_AGENT)
            downloaded = trafilatura.fetch_url(url, config=config)
            if downloaded is None:
                raise ValueError(f"Failed to fetch content from URL: {url}")

            # Extract article text and metadata
            text = trafilatura.extract(
                downloaded,
                include_comments=False,
                include_tables=True,
                no_fallback=False,
            )

            if not text:
                raise ValueError(f"No text content extracted from URL: {url}")

            # Extract metadata
            metadata = trafilatura.extract_metadata(downloaded)

            result = {
                "text": text,
                "title": metadata.title if metadata and metadata.title else None,
                "source": url,
                "metadata": {
                    "author": metadata.author if metadata and metadata.author else None,
                    "date": metadata.date if metadata and metadata.date else None,
                    "sitename": metadata.sitename if metadata and metadata.sitename else None,
                    "extracted_at": datetime.utcnow().isoformat(),
                },
            }

            return result

        except Exception as e:
            raise ValueError(f"Error parsing URL {url}: {str(e)}") from e


def parse_web_url(url: str) -> dict[str, str | None]:
    """
    Convenience function to parse a web URL.

    Args:
        url: The URL to parse

    Returns:
        Dictionary with extracted content and metadata

    Raises:
        ValueError: If URL is invalid or unreachable
    """
    parser = WebParser()
    return parser.parse(url)
