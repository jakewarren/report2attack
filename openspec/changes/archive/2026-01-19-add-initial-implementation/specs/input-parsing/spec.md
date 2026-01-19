# Capability: Input Parsing

## ADDED Requirements

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
The system SHALL automatically detect input type based on provided argument.

#### Scenario: Detect URL input
- **WHEN** input starts with http:// or https://
- **THEN** system routes to web parser

#### Scenario: Detect file path input
- **WHEN** input is a file path ending in .pdf
- **THEN** system routes to PDF parser

#### Scenario: Ambiguous input
- **WHEN** input type cannot be determined
- **THEN** system returns an error with usage examples

### Requirement: Text Extraction Output
The system SHALL return extracted text in a normalized format.

#### Scenario: Successful extraction
- **WHEN** parsing completes successfully
- **THEN** system returns a dictionary with keys: text, title, source, metadata

#### Scenario: Metadata preservation
- **WHEN** source document has metadata (author, date, URL)
- **THEN** system preserves metadata in output structure
