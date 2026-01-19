# Change: Initial Implementation of report2attack

## Why

Security analysts frequently encounter threat intelligence reports from various sources (blogs, PDFs, research papers) that describe adversary tactics and techniques. Manually mapping these narratives to the MITRE ATT&CK framework is time-consuming and error-prone. An automated tool that can ingest reports and produce standardized ATT&CK mappings would significantly accelerate threat analysis workflows and improve consistency across security teams.

## What Changes

- **NEW**: Complete Python CLI tool for automated threat intelligence to MITRE ATT&CK mapping
- **NEW**: Input parsing for web URLs and PDF documents
- **NEW**: RAG (Retrieval-Augmented Generation) pipeline with embedded MITRE ATT&CK framework
- **NEW**: LLM-based technique mapping with semantic retrieval
- **NEW**: Multiple output formats (JSON, CSV, markdown, ATT&CK Navigator)
- **NEW**: Project structure with dependency management via uv
- **NEW**: Testing infrastructure with pytest

## Impact

- **Affected specs**: Creates 5 new capabilities:
  - `input-parsing` - Web and PDF document ingestion
  - `text-extraction` - Content extraction and preprocessing
  - `rag-pipeline` - Vector store and semantic retrieval
  - `attack-mapping` - LLM-based MITRE ATT&CK technique identification
  - `output-formatting` - Multi-format report generation

- **Affected code**:
  - New project structure (greenfield)
  - Core modules: `src/report2attack/`
  - Configuration: `pyproject.toml`
  - Tests: `tests/`
  - CLI entry point

- **External dependencies**:
  - LangChain for RAG orchestration
  - ChromaDB for vector storage
  - OpenAI/Anthropic for LLM and embeddings
  - trafilatura for web parsing
  - pytest for testing

## Risks

- LLM API costs could be high for large documents
- Mapping accuracy depends on LLM quality and prompt engineering
- MITRE ATT&CK framework updates require vector store refresh
- PDF parsing quality varies with document structure
