# Proposal: download-pdf-urls

## Problem Statement
When users provide a URL pointing to a PDF file (e.g., `https://example.com/report.pdf`), the system currently attempts to parse it as a web page using trafilatura, which fails. The input type detection logic only recognizes URLs as "web" type, without checking if the URL points to a PDF document.

## Current Behavior
1. User provides: `https://example.com/threat-report.pdf`
2. `detect_input_type()` sees `https://` prefix → returns `InputType.WEB`
3. `parse_web_url()` attempts to extract HTML content
4. Parser fails because the content is binary PDF data, not HTML

## Proposed Solution
Add PDF URL download capability to automatically detect when a URL points to a PDF file, download it to a temporary location, parse it using the existing PDF parser, and clean up the temporary file afterward.

### Key Changes
1. **URL-based PDF detection**: Check if URL path ends with `.pdf` or if Content-Type header indicates PDF
2. **Temporary file download**: Use `requests` library to download PDF to temp directory
3. **Reuse existing parser**: Pass downloaded file path to existing `parse_pdf()` function
4. **Automatic cleanup**: Remove temporary file after parsing (even on error)

### Design Constraints
- Minimal dependencies: Use `requests` (already common) and `tempfile` (stdlib)
- Security: Validate Content-Type, enforce reasonable size limits
- Performance: Stream large files to disk rather than loading into memory
- Error handling: Clear messages for network errors, invalid PDFs, timeout issues

## Affected Specifications
- **input-parsing**: Add new requirement for PDF URL download and detection

## Out of Scope
- OCR for scanned PDFs (future enhancement)
- Authentication/credentials for protected PDFs
- Progressive download for very large files (>100MB)
- Caching of downloaded PDFs across invocations

## Dependencies
- Requires `requests` library (check if already in dependencies)
- Uses Python stdlib `tempfile` module

## Risks and Mitigations
| Risk | Mitigation |
|------|------------|
| Large file downloads | Implement size limit check via HEAD request |
| Network timeouts | Use reasonable timeout (30s) with clear error messages |
| Disk space exhaustion | Use temp directory with automatic cleanup |
| Malicious PDF files | Rely on existing PDF parser error handling |

## Success Criteria
- User can provide PDF URLs like `https://example.com/report.pdf`
- System automatically detects PDF URLs and downloads them
- Downloaded PDFs are parsed using existing PDF parser
- Temporary files are cleaned up even on errors
- Clear error messages for network failures or invalid PDFs
