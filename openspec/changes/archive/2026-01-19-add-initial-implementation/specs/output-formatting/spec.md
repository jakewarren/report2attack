# Capability: Output Formatting

## ADDED Requirements

### Requirement: JSON Output Format
The system SHALL generate structured JSON output with complete mapping results.

#### Scenario: Standard JSON structure
- **WHEN** user requests JSON output
- **THEN** system generates file with metadata, techniques array, and statistics

#### Scenario: JSON schema compliance
- **WHEN** generating JSON
- **THEN** output includes source, timestamp, ATT&CK version, confidence threshold, and technique details

#### Scenario: Technique detail structure
- **WHEN** including techniques in JSON
- **THEN** each entry has id, name, tactics, confidence, evidence, and chunk_source

### Requirement: CSV Output Format
The system SHALL generate CSV output compatible with spreadsheet tools.

#### Scenario: Flat CSV structure
- **WHEN** user requests CSV output
- **THEN** system generates rows with columns: technique_id, technique_name, tactic, confidence, evidence

#### Scenario: Multi-tactic handling
- **WHEN** technique has multiple tactics
- **THEN** system creates separate row for each tactic or joins with semicolons

#### Scenario: Evidence truncation
- **WHEN** evidence text exceeds 500 characters
- **THEN** system truncates with ellipsis for CSV readability

### Requirement: Markdown Report Format
The system SHALL generate human-readable markdown reports.

#### Scenario: Report structure
- **WHEN** user requests markdown output
- **THEN** system generates document with header, summary statistics, and techniques grouped by tactic

#### Scenario: Technique detail formatting
- **WHEN** listing techniques
- **THEN** each entry includes technique name, ID, confidence bar, and quoted evidence

#### Scenario: Table of contents
- **WHEN** report has multiple tactics
- **THEN** system includes clickable table of contents with tactic links

### Requirement: ATT&CK Navigator Layer Format
The system SHALL generate layer files compatible with MITRE ATT&CK Navigator.

#### Scenario: Layer metadata
- **WHEN** generating Navigator layer
- **THEN** system includes name, description, domain (enterprise), and version fields

#### Scenario: Technique scoring
- **WHEN** adding techniques to layer
- **THEN** system maps confidence scores to color intensity (0.0-1.0 scale)

#### Scenario: Technique annotations
- **WHEN** techniques are included in layer
- **THEN** system adds metadata comments with evidence and confidence

#### Scenario: Navigator compatibility validation
- **WHEN** layer file is generated
- **THEN** output conforms to ATT&CK Navigator v4.x JSON schema

### Requirement: Output File Naming
The system SHALL generate output files with consistent naming conventions.

#### Scenario: Default filename
- **WHEN** user does not specify output path
- **THEN** system generates filename from source: report2attack_<source_name>_<timestamp>.<ext>

#### Scenario: Custom output path
- **WHEN** user provides output file path
- **THEN** system writes to specified location

#### Scenario: Multiple format output
- **WHEN** user requests multiple formats
- **THEN** system generates separate files with appropriate extensions

### Requirement: Output Statistics
The system SHALL include analysis statistics in all output formats.

#### Scenario: Technique count summary
- **WHEN** generating output
- **THEN** system includes total techniques, unique techniques, and techniques per tactic

#### Scenario: Confidence distribution
- **WHEN** including statistics
- **THEN** system reports count of high/medium/low confidence mappings

#### Scenario: Processing metadata
- **WHEN** output is created
- **THEN** system includes processing time, LLM provider used, and ATT&CK version

### Requirement: Error and Warning Reporting
The system SHALL report warnings and errors in output.

#### Scenario: Partial results warning
- **WHEN** processing encounters non-fatal errors
- **THEN** system includes warnings in output metadata

#### Scenario: Low quality indication
- **WHEN** analysis has fewer than 3 techniques or all low confidence
- **THEN** system adds quality warning to output

#### Scenario: Error details
- **WHEN** processing fails completely
- **THEN** system generates error output with diagnostic information
