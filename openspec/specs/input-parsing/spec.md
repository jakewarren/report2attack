# input-parsing Specification

## Purpose
TBD - created by archiving change add-initial-implementation. Update Purpose after archive.
## Requirements
### Requirement: Web Article Parsing
The system SHALL extract clean text content from web URLs using trafilatura.

#### Scenario: Parse public threat report
- **WHEN** user provides a URL to a threat intelligence article
- **THEN** system extracts article text, title, and publication date
- **AND** removes navigation, ads, and boilerplate content

#### Scenario: Handle HTTPS redirects
- **WHEN** a URL redirects to another location
- **THEN** system follows redirects and extracts content from final destination

#### Scenario: Invalid URL
- **WHEN** user provides an invalid or unreachable URL
- **THEN** system returns an error message with details

### Requirement: PDF Document Parsing
The system SHALL extract text content from PDF files using multiple parsing backends.

#### Scenario: Parse text-based PDF
- **WHEN** user provides a path to a text-based PDF report
- **THEN** system extracts all text content with page numbers preserved

#### Scenario: Parse complex PDF layout
- **WHEN** PDF has tables, multi-column layouts, or embedded images
- **THEN** system attempts extraction with PDFPlumber fallback

#### Scenario: Unreadable PDF
- **WHEN** PDF is encrypted, corrupted, or scanned without OCR
- **THEN** system returns an error message indicating the parsing failure

### Requirement: Input Type Detection
The system SHALL automatically detect input type based on provided argument, including PDF URLs.

#### Scenario: Detect PDF URL input
- **WHEN** input starts with `http://` or `https://` and ends with `.pdf`
- **THEN** system routes to PDF download handler

#### Scenario: Detect web URL for HTML content
- **WHEN** input starts with `http://` or `https://` and does not end with `.pdf`
- **THEN** system routes to web parser (unchanged behavior)

### Requirement: Text Extraction Output
The system SHALL return extracted text in a normalized format.

#### Scenario: Successful extraction
- **WHEN** parsing completes successfully
- **THEN** system returns a dictionary with keys: text, title, source, metadata

#### Scenario: Metadata preservation
- **WHEN** source document has metadata (author, date, URL)
- **THEN** system preserves metadata in output structure

### Requirement: PDF URL Detection and Download
The system SHALL detect when a URL points to a PDF document and download it for parsing.

#### Scenario: Detect PDF URL by extension
- **WHEN** user provides a URL ending in `.pdf` (e.g., `https://example.com/report.pdf`)
- **THEN** system detects it as a PDF URL input type
- **AND** routes to PDF download handler instead of web parser

#### Scenario: Detect PDF URL by Content-Type
- **WHEN** URL does not end in `.pdf` but server returns `Content-Type: application/pdf`
- **THEN** system detects it as a PDF document
- **AND** downloads and parses as PDF

#### Scenario: Download PDF to temporary location
- **WHEN** system detects a PDF URL
- **THEN** system downloads the PDF to a temporary file using `requests` library
- **AND** passes the temporary file path to existing PDF parser
- **AND** deletes the temporary file after parsing (even on error)

#### Scenario: Stream large PDF files
- **WHEN** downloading a PDF larger than 10MB
- **THEN** system streams the content to disk instead of loading into memory
- **AND** provides efficient handling of large threat reports

#### Scenario: Handle network errors during download
- **WHEN** PDF URL is unreachable, times out, or returns HTTP error
- **THEN** system returns clear error message indicating network failure
- **AND** includes HTTP status code and error details

#### Scenario: Validate PDF size before download
- **WHEN** system detects a PDF URL
- **THEN** system performs HEAD request to check Content-Length
- **AND** rejects downloads exceeding 100MB with clear error message
- **AND** proceeds with download if size is within limit

#### Scenario: Handle redirects for PDF URLs
- **WHEN** PDF URL redirects to another location
- **THEN** system follows redirects (up to 5 redirects)
- **AND** downloads PDF from final destination
- **AND** validates final URL points to PDF content

