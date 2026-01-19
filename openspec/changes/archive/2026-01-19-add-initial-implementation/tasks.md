# Implementation Tasks

## 1. Project Setup
- [x] 1.1 Initialize Python project with uv
- [x] 1.2 Create pyproject.toml with dependencies (langchain, chromadb, trafilatura, pytest)
- [x] 1.3 Setup project structure (src/report2attack/, tests/)
- [x] 1.4 Configure linting (ruff) and formatting (black)
- [x] 1.5 Create .gitignore for Python projects

## 2. Input Parsing Module
- [x] 2.1 Implement web parser using trafilatura (src/parsers/web.py)
- [x] 2.2 Implement PDF parser with PyPDF and PDFPlumber fallback (src/parsers/pdf.py)
- [x] 2.3 Add input type detection logic (src/parsers/__init__.py)
- [x] 2.4 Write unit tests for web parsing with mocked HTTP responses
- [x] 2.5 Write unit tests for PDF parsing with test fixtures

## 3. Text Extraction Module
- [x] 3.1 Implement text preprocessing (cleaning, normalization) (src/preprocessing/text.py)
- [x] 3.2 Implement document chunking with token counting (src/preprocessing/text.py)
- [x] 3.3 Add text quality validation checks (src/preprocessing/text.py)
- [x] 3.4 Write unit tests for preprocessing and chunking

## 4. RAG Pipeline Module
- [x] 4.1 Implement MITRE ATT&CK data downloader (src/rag/vector_store.py)
- [x] 4.2 Implement ChromaDB vector store initialization (src/rag/vector_store.py)
- [x] 4.3 Create embedding provider abstraction (src/rag/embeddings.py)
- [x] 4.4 Implement OpenAI embedding provider (src/rag/embeddings.py)
- [x] 4.5 Implement sentence-transformers local provider (src/rag/embeddings.py)
- [x] 4.6 Implement semantic retrieval with top-K query (src/rag/retrieval.py)
- [x] 4.7 Add retrieval context formatting for LLM (src/rag/retrieval.py)
- [x] 4.8 Write integration tests for vector store with sample data

## 5. ATT&CK Mapping Module
- [x] 5.1 Implement LLM provider abstraction (src/mapping/llm.py)
- [x] 5.2 Add OpenAI LLM provider (src/mapping/llm.py)
- [x] 5.3 Add Anthropic LLM provider (src/mapping/llm.py)
- [x] 5.4 Add Ollama local LLM provider (src/mapping/llm.py)
- [x] 5.5 Create Pydantic models for structured output (src/mapping/mapper.py)
- [x] 5.6 Implement prompt templates with few-shot examples (src/mapping/mapper.py)
- [x] 5.7 Implement technique extraction with validation (src/mapping/mapper.py)
- [x] 5.8 Add multi-chunk aggregation and deduplication (src/mapping/mapper.py)
- [x] 5.9 Write unit tests with mocked LLM responses

## 6. Output Formatting Module
- [x] 6.1 Implement JSON output formatter (src/output/json.py)
- [x] 6.2 Implement CSV output formatter (src/output/csv.py)
- [x] 6.3 Implement markdown report generator (src/output/markdown.py)
- [x] 6.4 Implement ATT&CK Navigator layer generator (src/output/navigator.py)
- [x] 6.5 Add output file naming logic (src/output/__init__.py)
- [x] 6.6 Write unit tests for all output formats

## 7. CLI Implementation
- [x] 7.1 Create CLI entry point with argument parsing (src/cli.py)
- [x] 7.2 Add configuration file support (YAML/JSON config)
- [x] 7.3 Implement logging configuration (console and file output)
- [x] 7.4 Add progress indicators for long-running operations
- [x] 7.5 Write CLI integration tests

## 8. Integration and End-to-End Testing
- [x] 8.1 Create end-to-end test with sample threat report URL
- [x] 8.2 Create end-to-end test with sample PDF document
- [x] 8.3 Test output format generation for all formats
- [x] 8.4 Validate ATT&CK Navigator layer import
- [x] 8.5 Test error handling paths (invalid inputs, API failures)

## 9. Documentation
- [x] 9.1 Write README.md with installation instructions
- [x] 9.2 Add usage examples and CLI documentation
- [x] 9.3 Document configuration options
- [x] 9.4 Add docstrings to all public functions (Google style)
- [x] 9.5 Create CONTRIBUTING.md with development setup

## 10. Deployment Preparation
- [x] 10.1 Add version metadata and __version__ variable
- [x] 10.2 Configure package metadata in pyproject.toml for PyPI
- [x] 10.3 Create requirements files for different use cases
- [x] 10.4 Test installation from source in clean environment
- [x] 10.5 Create GitHub Actions workflow for CI/CD
