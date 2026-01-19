# Design: report2attack Architecture

## Context

Building a tool that automatically maps threat intelligence narratives to MITRE ATT&CK requires:
- Robust parsing of diverse input formats (web, PDF)
- Semantic understanding of adversary behaviors described in natural language
- Accurate retrieval of relevant ATT&CK techniques from 600+ possibilities
- Flexible output formats for different analyst workflows

**Constraints:**
- LLM API calls are expensive - minimize token usage
- Must work with varying document quality (formatting, OCR errors)
- Should support offline operation where possible (cached embeddings)
- Output must be compatible with existing ATT&CK tooling (Navigator)

**Stakeholders:**
- Security analysts conducting threat research
- SOC teams triaging incident reports
- Threat intelligence teams standardizing reporting

## Goals / Non-Goals

### Goals
- Parse web articles and PDF reports with high fidelity
- Map described techniques to ATT&CK IDs with >80% accuracy
- Support multiple LLM providers (OpenAI, Anthropic, local models)
- Generate outputs compatible with ATT&CK Navigator
- Enable offline operation with cached vector store
- Keep LLM token usage under 10K tokens per document

### Non-Goals
- Real-time monitoring or streaming ingestion
- Custom threat intelligence database management
- Automated detection rule generation
- Multi-language support (English only initially)
- OCR for scanned PDFs (assume text-based PDFs)

## Decisions

### 1. RAG Architecture for ATT&CK Mapping

**Decision:** Use RAG (Retrieval-Augmented Generation) with pre-embedded MITRE ATT&CK techniques rather than zero-shot classification or fine-tuning.

**Rationale:**
- 600+ ATT&CK techniques exceed context window limits for comprehensive zero-shot
- RAG retrieves top-K relevant techniques based on semantic similarity, reducing LLM input size
- No fine-tuning required - works with any LLM API
- Enables iterative refinement: retrieval → LLM mapping → validation

**Alternatives considered:**
- Zero-shot classification: Would require massive prompts with all techniques, high token cost
- Fine-tuned classifier: Expensive to train, maintain, and update with ATT&CK changes
- Rule-based keyword matching: Too brittle, misses semantic variations

### 2. Vector Store: ChromaDB (Local-First)

**Decision:** Use ChromaDB as the default vector store with local persistence.

**Rationale:**
- Embedded database, no separate server required
- Persistent storage enables offline operation
- Fast similarity search with HNSW indexing
- Python-native, easy to integrate

**Alternatives considered:**
- Pinecone/Weaviate: Cloud-hosted, requires internet and subscription
- FAISS: More complex setup, no built-in persistence layer
- Qdrant: Good alternative but more deployment overhead

### 3. LangChain for RAG Orchestration

**Decision:** Use LangChain to orchestrate the RAG pipeline (document loading, embedding, retrieval, LLM calls).

**Rationale:**
- Standardized interfaces for LLMs, embeddings, and vector stores
- Built-in document loaders for PDF and web
- Structured output parsing for ATT&CK technique extraction
- Active community and frequent updates

**Alternatives considered:**
- LlamaIndex: Similar features, but LangChain has better structured output support
- Custom implementation: More control but significant engineering effort
- Haystack: Good for search, less focused on LLM orchestration

### 4. Input Parsing: trafilatura for Web, LangChain for PDF

**Decision:** Use trafilatura for web article extraction and LangChain's PDF loaders (PyPDF + PDFPlumber fallback).

**Rationale:**
- trafilatura specializes in clean article extraction, handles JavaScript-rendered content
- PyPDFLoader works for most text-based PDFs
- PDFPlumber as fallback for complex layouts
- Consistent text output for both sources

**Alternatives considered:**
- BeautifulSoup: Requires manual parsing logic for each site
- Playwright: Heavy dependency for JavaScript rendering (may add later)
- pdfminer: Lower-level, more complex API

### 5. CLI-First Interface

**Decision:** Build as a CLI tool with library imports as secondary use case.

**Rationale:**
- Primary user workflow: `report2attack https://example.com/report.html`
- Simpler testing and debugging
- Easy integration into automation scripts
- Can add web UI or API later if needed

**Alternatives considered:**
- Web API first: Adds deployment complexity, not needed initially
- Library-only: Less discoverable, requires more user code

### 6. Output Formats

**Decision:** Support JSON, CSV, markdown, and ATT&CK Navigator layer files.

**Rationale:**
- JSON: Machine-readable, programmatic integration
- CSV: Excel/spreadsheet-friendly for analysts
- Markdown: Human-readable reports
- Navigator layer: Direct import into MITRE's visualization tool

### 7. Prompt Engineering Strategy

**Decision:** Use structured output with Pydantic models to extract technique IDs, confidence scores, and evidence.

**Rationale:**
- LangChain's structured output ensures parseable responses
- Pydantic validation catches malformed LLM outputs
- Forces LLM to cite evidence from retrieved techniques
- Enables confidence filtering in post-processing

### 8. Testing Strategy

**Decision:** Mock LLM/embedding calls in unit tests, use fixtures for integration tests.

**Rationale:**
- Avoid API costs during development
- Deterministic test results
- Fast CI/CD pipeline
- Use recorded real responses as test fixtures for realism

## Data Flow

```
Input (URL/PDF)
    ↓
[Input Parser] → Extract clean text
    ↓
[Text Preprocessor] → Chunk, clean, deduplicate
    ↓
[RAG Pipeline]
    ├─ Embed document chunks
    ├─ Query vector store (MITRE ATT&CK techniques)
    ├─ Retrieve top-K relevant techniques
    └─ LLM mapping with retrieved context
    ↓
[Validation] → Filter by confidence, deduplicate
    ↓
[Output Formatter] → JSON/CSV/Markdown/Navigator
    ↓
Output file(s)
```

## Module Structure

```
src/report2attack/
├── __init__.py
├── cli.py                  # CLI entry point
├── parsers/
│   ├── __init__.py
│   ├── web.py              # trafilatura wrapper
│   └── pdf.py              # LangChain PDF loaders
├── preprocessing/
│   ├── __init__.py
│   └── text.py             # Chunking, cleaning
├── rag/
│   ├── __init__.py
│   ├── vector_store.py     # ChromaDB management
│   ├── embeddings.py       # Embedding provider abstraction
│   └── retrieval.py        # Query and retrieval logic
├── mapping/
│   ├── __init__.py
│   ├── llm.py              # LLM provider abstraction
│   └── mapper.py           # ATT&CK mapping orchestration
├── output/
│   ├── __init__.py
│   ├── json.py
│   ├── csv.py
│   ├── markdown.py
│   └── navigator.py        # ATT&CK Navigator layer format
└── data/
    └── attack/             # Downloaded MITRE ATT&CK STIX data
```

## Risks / Trade-offs

### Risk: LLM Hallucination
- **Impact**: May map to non-existent technique IDs
- **Mitigation**:
  - Use structured output with validation against STIX data
  - Require evidence citations from retrieved techniques
  - Add confidence scoring and filtering

### Risk: High API Costs
- **Impact**: Expensive for large documents or batch processing
- **Mitigation**:
  - Chunk documents and process incrementally
  - Cache embeddings in vector store
  - Support local models (Ollama, etc.)
  - Set configurable token limits

### Risk: ATT&CK Framework Updates
- **Impact**: Vector store becomes stale, missing new techniques
- **Mitigation**:
  - Version the embedded framework data
  - Provide update command to refresh vector store
  - Log ATT&CK version in output metadata

### Risk: Poor Document Quality
- **Impact**: Low extraction accuracy from complex PDFs or unusual layouts
- **Mitigation**:
  - Multiple PDF parsing backends (PyPDF, PDFPlumber)
  - Preprocessing to clean extracted text
  - User feedback on parsing quality
  - Manual text input option

## Migration Plan

N/A - This is a new project with no existing users or data to migrate.

## Open Questions

1. **Chunking strategy**: Fixed token size vs semantic chunking (paragraphs)?
   - **Recommendation**: Start with fixed 500-token chunks with 50-token overlap

2. **Top-K retrieval**: How many techniques to retrieve for LLM context?
   - **Recommendation**: Default K=10, make configurable

3. **Confidence threshold**: What minimum confidence to include in output?
   - **Recommendation**: Default 0.5, expose as CLI flag

4. **Local model support**: Which models to prioritize?
   - **Recommendation**: Start with OpenAI/Anthropic, add Ollama support in v0.2

5. **STIX data source**: Official MITRE repo or ATT&CK API?
   - **Recommendation**: Download from official GitHub repo, embed on first run
