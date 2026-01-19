# Capability: ATT&CK Mapping

## ADDED Requirements

### Requirement: LLM Provider Support
The system SHALL support multiple LLM providers for technique mapping.

#### Scenario: OpenAI integration
- **WHEN** configured with OpenAI provider
- **THEN** system uses GPT-4 or GPT-3.5-turbo based on configuration

#### Scenario: Anthropic integration
- **WHEN** configured with Anthropic provider
- **THEN** system uses Claude 3 models (Opus, Sonnet, or Haiku)

#### Scenario: Local model support
- **WHEN** configured with Ollama provider
- **THEN** system connects to local Ollama instance with specified model

#### Scenario: API failure handling
- **WHEN** LLM API request fails
- **THEN** system retries with backoff or returns partial results with error indication

### Requirement: Structured Technique Extraction
The system SHALL extract ATT&CK mappings using structured output with Pydantic validation.

#### Scenario: Extract techniques from chunk
- **WHEN** LLM processes document chunk with retrieved ATT&CK context
- **THEN** system returns structured output with technique IDs, confidence scores, and evidence quotes

#### Scenario: Validate technique IDs
- **WHEN** LLM returns technique IDs
- **THEN** system validates IDs against MITRE ATT&CK framework
- **AND** rejects hallucinated or invalid IDs

#### Scenario: Evidence citation
- **WHEN** mapping techniques
- **THEN** system requires LLM to cite specific text from document that supports each mapping

### Requirement: Confidence Scoring
The system SHALL assign confidence scores to each technique mapping.

#### Scenario: High confidence mapping
- **WHEN** document explicitly mentions technique name or detailed behavior
- **THEN** system assigns confidence score >= 0.8

#### Scenario: Inferred mapping
- **WHEN** technique is implied but not explicitly stated
- **THEN** system assigns confidence score 0.5-0.8

#### Scenario: Low confidence mapping
- **WHEN** mapping is speculative or tangential
- **THEN** system assigns confidence score < 0.5

#### Scenario: Confidence filtering
- **WHEN** user sets minimum confidence threshold
- **THEN** system filters output to only include mappings above threshold

### Requirement: Prompt Engineering
The system SHALL use structured prompts to guide LLM technique identification.

#### Scenario: System prompt structure
- **WHEN** initializing LLM conversation
- **THEN** system provides role definition, task description, and output format instructions

#### Scenario: Few-shot examples
- **WHEN** prompting LLM
- **THEN** system includes 2-3 example mappings to demonstrate expected format

#### Scenario: Retrieved context injection
- **WHEN** querying LLM
- **THEN** system includes top-K retrieved ATT&CK techniques in prompt context

### Requirement: Multi-Chunk Aggregation
The system SHALL aggregate technique mappings across document chunks.

#### Scenario: Combine chunk results
- **WHEN** document is processed in multiple chunks
- **THEN** system collects mappings from all chunks

#### Scenario: Deduplicate techniques
- **WHEN** same technique appears in multiple chunks
- **THEN** system keeps mapping with highest confidence score

#### Scenario: Evidence consolidation
- **WHEN** technique mapped multiple times
- **THEN** system combines evidence quotes from all chunks

### Requirement: Tactic Association
The system SHALL associate each mapped technique with its MITRE ATT&CK tactics.

#### Scenario: Single tactic technique
- **WHEN** technique belongs to one tactic
- **THEN** system includes tactic name in output

#### Scenario: Multi-tactic technique
- **WHEN** technique spans multiple tactics (e.g., T1078 Valid Accounts)
- **THEN** system includes all associated tactics in output

#### Scenario: Tactic-level analysis
- **WHEN** generating final output
- **THEN** system groups techniques by tactic for kill-chain visualization
