# report2attack

Automated threat intelligence to MITRE ATT&CK framework mapping tool.

## Overview

**report2attack** reads threat intelligence reports from websites and PDFs, then automatically maps the described tactics and techniques to the MITRE ATT&CK framework. This enables security analysts to quickly understand and classify threat behaviors in a standardized format.

### Key Features

- **Multi-Source Input**: Parse threat reports from web URLs or PDF documents
- **RAG-Based Mapping**: Uses Retrieval-Augmented Generation with embedded ATT&CK framework
- **Multiple LLM Providers**: Supports OpenAI, Anthropic Claude, and local models via Ollama
- **Flexible Output Formats**: Generate results in JSON, CSV, Markdown, and ATT&CK Navigator formats
- **Confidence Scoring**: Each technique mapping includes a confidence score with evidence citations

## Examples

Check out the [examples](examples/) directory for example analysis output:

- **[Markdown Report](examples/report2attack_report_20260119_122828.md)** - Human-readable analysis with detected techniques and evidence
- **[JSON Output](examples/report2attack_report_20260119_122828.json)** - Structured data for programmatic access
- **[ATT&CK Navigator](https://mitre-attack.github.io/attack-navigator/?tab=navigator&url=https://raw.githubusercontent.com/jakewarren/report2attack/refs/heads/main/examples/report2attack_report_20260119_122828_navigator.json)** - Interactive visualization of mapped techniques using the MITRE ATT&CK Navigator

## Architecture

report2attack uses a sophisticated RAG (Retrieval-Augmented Generation) pipeline:

1. **Input Parsing**: Extracts clean text from web pages (trafilatura) or PDFs (PyPDF/PDFPlumber)
2. **Text Preprocessing**: Cleans and chunks documents for optimal processing
3. **Semantic Retrieval**: Queries embedded MITRE ATT&CK techniques using ChromaDB vector store
4. **LLM Mapping**: Maps document text to techniques using structured LLM output with evidence
5. **Output Generation**: Produces multiple output formats with statistics and metadata

## Installation

### Prerequisites

- Python 3.11 or higher
- API keys for your chosen LLM/embedding provider (OpenAI, Anthropic, or local Ollama)

### Install with uv (recommended)

```bash
# Clone the repository
git clone https://github.com/jakewarren/report2attack.git
cd report2attack

# Install with uv
uv sync

# Or install in development mode with dev dependencies
uv sync --extra dev
```

### Install with pip

```bash
pip install -e .

# Or with development dependencies
pip install -e ".[dev]"
```

## Quick Start

### Basic Usage

```bash
# Analyze a web article
uv run report2attack https://example.com/threat-report.html

# Analyze a PDF report
uv run report2attack /path/to/report.pdf

# Specify output directory and formats
uv run report2attack https://example.com/report.html \
  --output-dir ./results \
  --formats json csv markdown navigator
```

### Configuration

Set API keys as environment variables:

```bash
# For OpenAI (default)
export OPENAI_API_KEY="your-api-key"

# For Anthropic Claude
export ANTHROPIC_API_KEY="your-api-key"

# For local embeddings, no API key needed
```

### First Run

On first run, report2attack will:
1. Download the MITRE ATT&CK framework data (~30MB)
2. Embed all techniques in a local ChromaDB vector store
3. Cache everything for offline use

This one-time setup takes 5-10 minutes depending on your connection and compute.

## CLI Options

```
Usage: report2attack [OPTIONS] INPUT_SOURCE

Arguments:
  INPUT_SOURCE  URL (http:// or https://) or path to PDF file

Options:
  -o, --output-dir PATH           Output directory [default: .]
  -f, --formats TEXT              Output format(s): json, csv, markdown, navigator
                                  [default: json, markdown]
  --llm-provider [openai|anthropic|ollama]
                                  LLM provider [default: openai]
  --llm-model TEXT                LLM model name (provider-specific)
  --embedding-provider [openai|sentence-transformers]
                                  Embedding provider [default: openai]
  --chunk-size INT                Max tokens per chunk [default: 500]
  --chunk-overlap INT             Token overlap between chunks [default: 50]
  --top-k INT                     Techniques to retrieve per chunk [default: 10]
  --min-confidence FLOAT          Minimum confidence threshold [default: 0.5]
  --force-reload                  Force reload of ATT&CK data
  -v, --verbose                   Verbose output
  --version                       Show version
  --help                          Show this message
```

## Examples

### Using Different LLM Providers

```bash
# OpenAI GPT-5 Nano (default)
report2attack report.pdf --llm-provider openai --llm-model gpt-5-nano

# Anthropic Claude Sonnet 4.5 (default for anthropic)
report2attack report.pdf --llm-provider anthropic --llm-model claude-sonnet-4-5-20250929

# Local Ollama model
report2attack report.pdf --llm-provider ollama --llm-model llama2
```

### Using Local Embeddings

```bash
# Use sentence-transformers for offline embeddings
report2attack report.pdf --embedding-provider sentence-transformers
```

### Adjusting Confidence Threshold

```bash
# Only include high-confidence mappings
report2attack report.pdf --min-confidence 0.8

# Include more speculative mappings
report2attack report.pdf --min-confidence 0.3
```

### Generating ATT&CK Navigator Layer

```bash
# Generate Navigator layer for visualization
report2attack report.pdf --formats navigator

# Import the generated JSON into ATT&CK Navigator:
# https://mitre-attack.github.io/attack-navigator/
```

## Output Formats

### JSON
Structured output with metadata, statistics, and detailed technique mappings:

```json
{
  "metadata": {
    "source": "https://example.com/report.html",
    "title": "Threat Report Title",
    "timestamp": "2024-01-15T10:30:00",
    "attack_version": "18.1"
  },
  "statistics": {
    "total_techniques": 12,
    "high_confidence": 8,
    "medium_confidence": 4
  },
  "techniques": [
    {
      "technique_id": "T1566.001",
      "technique_name": "Spearphishing Attachment",
      "confidence": 0.92,
      "evidence": "attackers sent malicious Excel documents...",
      "tactics": ["initial-access"]
    }
  ]
}
```

### CSV
Spreadsheet-friendly flat format:

```csv
technique_id,technique_name,tactics,confidence,evidence
T1566.001,Spearphishing Attachment,initial-access,0.92,"attackers sent malicious Excel documents..."
```

### Markdown
Human-readable report with techniques grouped by tactic:

```markdown
# ATT&CK Mapping Report

## Summary
- Total Techniques: 12
- High Confidence: 8

## Initial Access

### T1566.001: Spearphishing Attachment
**Confidence:** ██████████ (0.92)
**Evidence:** attackers sent malicious Excel documents...
```

### ATT&CK Navigator
JSON layer file compatible with MITRE's ATT&CK Navigator for visualization:
- Import at: https://mitre-attack.github.io/attack-navigator/
- Techniques colored by confidence score
- Evidence included in technique annotations

## Development

### Setup Development Environment

```bash
# Clone and install with dev dependencies
git clone https://github.com/jakewarren/report2attack.git
cd report2attack
make install

# Run tests
make test

# Run tests with coverage
make test-cov

# Format code
make format

# Lint code
make lint

# Type check
make typecheck

# Run all checks
make check
```

### Project Structure

```
report2attack/
├── src/report2attack/
│   ├── parsers/          # Web and PDF input parsing
│   ├── preprocessing/    # Text cleaning and chunking
│   ├── rag/             # Vector store and retrieval
│   ├── mapping/         # LLM-based technique mapping
│   ├── output/          # Output formatters
│   ├── cli.py           # CLI interface
│   └── data/attack/     # MITRE ATT&CK data cache
├── tests/               # Unit and integration tests
├── openspec/            # OpenSpec change proposals
├── pyproject.toml       # Project configuration
└── README.md
```

## API Usage

report2attack can also be used as a Python library:

```python
from report2attack.parsers import parse_input
from report2attack.preprocessing import preprocess_text, chunk_text
from report2attack.rag import setup_retrieval_system
from report2attack.mapping import create_mapper
from report2attack.output import format_results

# Parse input
parsed = parse_input("https://example.com/report.html")
text = parsed["text"]

# Preprocess and chunk
cleaned = preprocess_text(text)
chunks = chunk_text(cleaned)

# Setup retrieval
retriever = setup_retrieval_system(embedding_provider="openai")

# Retrieve and map
mapper = create_mapper(llm_provider="openai", min_confidence=0.5)
chunk_dicts = [{"text": c.text, "chunk_index": c.chunk_index} for c in chunks]
all_retrieved = [retriever.retrieve(c.text) for c in chunks]
mappings = mapper.map_document(chunk_dicts, all_retrieved)

# Format output
results = {
    "source": parsed["source"],
    "title": parsed["title"],
    "techniques": [m.dict() for m in mappings],
}
format_results(results, ["json", "markdown"], "./output")
```

## Configuration

### Environment Variables

- `OPENAI_API_KEY`: OpenAI API key (for LLM and embeddings)
- `ANTHROPIC_API_KEY`: Anthropic API key (for Claude models)

### Data Directories

- **ATT&CK Data**: `src/report2attack/data/attack/`
- **Vector Store**: `~/.report2attack/chroma_db/`

### Updating ATT&CK Framework

```bash
# Force download latest ATT&CK data
report2attack report.pdf --force-reload
```


## License

MIT License - see LICENSE file for details

