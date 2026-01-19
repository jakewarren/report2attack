# Capability: RAG Pipeline

## ADDED Requirements

### Requirement: MITRE ATT&CK Data Ingestion
The system SHALL download and embed the MITRE ATT&CK framework on first run.

#### Scenario: Initial setup
- **WHEN** vector store does not exist or is empty
- **THEN** system downloads latest ATT&CK STIX data from official GitHub repository
- **AND** embeds all techniques, sub-techniques, tactics, and descriptions

#### Scenario: Version tracking
- **WHEN** ATT&CK data is embedded
- **THEN** system stores framework version and embed date in metadata

#### Scenario: Update check
- **WHEN** user requests vector store update
- **THEN** system downloads latest framework and re-embeds if version changed

### Requirement: Vector Store Management
The system SHALL maintain a persistent ChromaDB vector store for ATT&CK techniques.

#### Scenario: Create collection
- **WHEN** initializing vector store
- **THEN** system creates ChromaDB collection with configured embedding dimension

#### Scenario: Store metadata
- **WHEN** embedding techniques
- **THEN** system stores technique ID, name, tactic, description, and STIX version

#### Scenario: Persistent storage
- **WHEN** vector store is created or updated
- **THEN** system persists to local directory for offline access

### Requirement: Embedding Provider Support
The system SHALL support multiple embedding providers with consistent interface.

#### Scenario: OpenAI embeddings
- **WHEN** configured with OpenAI provider
- **THEN** system uses text-embedding-3-small model by default

#### Scenario: Local embeddings
- **WHEN** configured with sentence-transformers provider
- **THEN** system uses all-MiniLM-L6-v2 model locally

#### Scenario: Embedding failure
- **WHEN** embedding request fails (API error, rate limit)
- **THEN** system retries with exponential backoff or falls back to cached embeddings

### Requirement: Semantic Retrieval
The system SHALL retrieve relevant ATT&CK techniques using semantic similarity.

#### Scenario: Query vector store
- **WHEN** document chunk is processed
- **THEN** system embeds chunk and retrieves top-K most similar techniques (default K=10)

#### Scenario: Similarity threshold
- **WHEN** configuring retrieval
- **THEN** system allows minimum similarity score threshold (default 0.3)

#### Scenario: Tactic filtering
- **WHEN** user specifies target tactics (e.g., Initial Access, Persistence)
- **THEN** system filters retrieved techniques to match specified tactics

### Requirement: Retrieval Context Preparation
The system SHALL format retrieved techniques for LLM consumption.

#### Scenario: Context formatting
- **WHEN** techniques are retrieved
- **THEN** system formats as structured context including technique ID, name, tactic, and description

#### Scenario: Token budget management
- **WHEN** retrieved context exceeds token budget
- **THEN** system truncates to highest similarity matches within budget

#### Scenario: Deduplication
- **WHEN** multiple chunks retrieve overlapping techniques
- **THEN** system deduplicates by technique ID before passing to LLM
