# Project Context

## Purpose
report2Attack is a Python tool that reads threat intelligence reports from websites and PDFs, then automatically maps the described tactics and techniques to the MITRE ATT&CK framework. This enables security analysts to quickly understand and classify threat behaviors in a standardized format.

## Tech Stack
- **Language**: Python 3.11+
- **Package Management**: uv (for fast, reliable dependency management)
- **LLM Framework**: LangChain (for RAG pipelines and structured outputs)
- **Vector Store**: ChromaDB (for embedding MITRE ATT&CK techniques)
- **Embeddings**: OpenAI embeddings or sentence-transformers (for local option)
- **Web Parsing**: trafilatura (for extracting clean article content from websites)
- **PDF Parsing**: LangChain document loaders (PyPDFLoader, PDFPlumberLoader)

## Project Conventions

### Code Style
- Follow PEP 8 style guidelines
- Use type hints for all function signatures
- Maximum line length: 100 characters
- Use Black for code formatting
- Use Ruff for linting
- Docstrings: Google style format

### Architecture Patterns
- Modular design with clear separation of concerns:
  - Input handlers (trafilatura for web, LangChain loaders for PDF)
  - Text extraction and preprocessing
  - RAG pipeline:
    - Vector store with embedded MITRE ATT&CK techniques
    - Semantic retrieval of relevant techniques
    - LLM-based mapping with retrieved context
  - MITRE ATT&CK mapping validation
  - Output formatting (JSON, CSV, markdown, ATT&CK Navigator)
- Use dependency injection for testability
- Keep external API calls isolated in dedicated modules
- Cache embeddings and vector store for offline operation

### Testing Strategy
- Unit tests for core parsing and extraction logic
- Integration tests for LangChain RAG pipelines
- Use pytest as the testing framework
- Mock LLM and embedding calls in tests to avoid API costs
- Test vector store retrieval with sample data
- Aim for >80% code coverage on business logic

### Git Workflow
- Main branch: `main` (production-ready code)
- Feature branches: `feature/<description>`
- Conventional commits: `feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`
- PRs required for merging to main

## Domain Context
**MITRE ATT&CK Framework**: A globally accessible knowledge base of adversary tactics and techniques based on real-world observations. The framework is organized into:
- **Tactics**: The "why" of an attack (e.g., Initial Access, Persistence, Privilege Escalation)
- **Techniques**: The "how" of an attack (e.g., Phishing, Credential Dumping)
- **Sub-techniques**: More specific methods within a technique

The project should extract indicators of compromise (IoCs), TTPs (Tactics, Techniques, and Procedures), and map them to specific ATT&CK technique IDs (e.g., T1566.001 for Spearphishing Attachment).

## Important Constraints
- LLM API costs must be considered - use efficient prompting strategies
- Must handle various document formats and quality levels gracefully
- Output must be compatible with MITRE ATT&CK Navigator format
- Should support offline mode where possible (cached/local models)

## External Dependencies
- **MITRE ATT&CK STIX Data**: Download and embed entire framework for RAG retrieval
- **LLM API**: OpenAI, Anthropic, or local models via LangChain
- **Embedding API**: OpenAI embeddings or local sentence-transformers models
- **Vector Database**: ChromaDB (local) or Pinecone/Weaviate (cloud options)
- **Web sources**: Must handle various HTML structures, JavaScript-rendered content
- **PDF sources**: Must handle scanned documents (OCR might be needed)
