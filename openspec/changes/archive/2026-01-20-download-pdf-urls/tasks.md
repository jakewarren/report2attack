# Implementation Tasks

## 1. Add requests dependency
- [x] Check if `requests` is already in `pyproject.toml` dependencies
- [x] If not present, add `requests>=2.31.0` to dependencies
- [x] Run `uv sync` to update lock file

**Validation**: `uv pip list | grep requests` shows the package is installed

---

## 2. Create PDF URL download module
- [x] Create `src/report2attack/parsers/pdf_url.py`
- [x] Implement `download_pdf_from_url(url: str) -> str` function that:
  - Performs HEAD request to check Content-Type and Content-Length
  - Validates file size (reject >100MB)
  - Downloads PDF using streaming to temporary file
  - Returns temporary file path
- [x] Add timeout configuration (30 seconds default)
- [x] Handle HTTP errors, timeouts, and redirects with clear error messages

**Validation**: Manual test with sample PDF URL shows successful download

---

## 3. Create context manager for temporary file cleanup
- [x] Implement `TemporaryPDFDownload` context manager in `pdf_url.py`
- [x] Ensure temporary file is deleted in `__exit__` even on exceptions
- [x] Use `tempfile.NamedTemporaryFile` with `.pdf` suffix

**Validation**: Unit test confirms cleanup happens on both success and error paths

---

## 4. Update input type detection logic
- [x] Modify `detect_input_type()` in `src/report2attack/parsers/__init__.py`
- [x] Add check: if URL ends with `.pdf`, return new `InputType.PDF_URL`
- [x] Preserve existing WEB detection for non-PDF URLs
- [x] Update `InputType` enum to include `PDF_URL` value

**Validation**: Unit tests for various URL patterns (`.pdf` suffix, query params, etc.)

---

## 5. Update parse_input to handle PDF URLs
- [x] Modify `parse_input()` in `src/report2attack/parsers/__init__.py`
- [x] Add branch for `InputType.PDF_URL`:
  - Download PDF using `download_pdf_from_url()`
  - Parse with existing `parse_pdf()`
  - Clean up temporary file
- [x] Preserve source URL in metadata (not temp file path)

**Validation**: Integration test with real PDF URL shows correct parsing and cleanup

---

## 6. Add Content-Type validation (optional enhancement)
- [x] In `download_pdf_from_url()`, check `Content-Type` header from HEAD request
- [x] Log warning if Content-Type is not `application/pdf` but proceed with download
- [x] Add explicit check after download: verify file starts with `%PDF-` magic bytes

**Validation**: Test with URL that returns wrong Content-Type but is actually PDF

---

## 7. Write unit tests for PDF URL download
- [x] Create `tests/test_pdf_url.py`
- [x] Mock `requests.get()` and `requests.head()` for network calls
- [x] Test scenarios:
  - Successful PDF download and parsing
  - HTTP errors (404, 500)
  - Timeout errors
  - File size exceeded (>100MB)
  - Content-Type validation
  - Temporary file cleanup

**Validation**: `pytest tests/test_pdf_url.py -v` passes all tests

---

## 8. Update integration tests
- [x] Add test case in `tests/test_parsers.py` for PDF URL input
- [x] Mock network call or use a stable public PDF URL
- [x] Verify end-to-end flow: detection → download → parse → cleanup

**Validation**: `pytest tests/test_parsers.py -v` includes PDF URL test

---

## 9. Update error messages and documentation
- [x] Update CLI help text in `src/report2attack/cli.py` to mention PDF URLs
- [x] Add example: `report2attack https://example.com/report.pdf`
- [x] Update README.md with PDF URL examples in usage section
- [x] Ensure error messages clearly distinguish network errors from parsing errors

**Validation**: `report2attack --help` shows PDF URL support

---

## 10. Manual end-to-end testing
- [x] Test with real PDF URLs from various sources
- [x] Test with edge cases: redirects, large files, slow servers
- [x] Verify temporary files are cleaned up in `/tmp` directory
- [x] Confirm error messages are helpful for common failures

**Validation**: Successfully parse real threat intelligence PDF from URL

---

## Dependencies and Parallelization
- Tasks 1-3 can be done in parallel
- Task 4 depends on Task 3 (needs enum update)
- Task 5 depends on Tasks 2, 3, and 4
- Tasks 6-8 can be done in parallel after Task 5
- Tasks 9-10 should be done last
