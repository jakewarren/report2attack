"""ATT&CK technique mapping with LLM-based extraction."""

from typing import Any

from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from .llm import LLMProvider


class TechniqueMapping(BaseModel):
    """Pydantic model for a single technique mapping."""

    technique_id: str = Field(description="MITRE ATT&CK technique ID (e.g., T1566.001)")
    technique_name: str = Field(description="Name of the technique")
    confidence: float = Field(description="Confidence score between 0 and 1", ge=0.0, le=1.0)
    evidence: str = Field(description="Quote from document supporting this mapping")
    tactics: list[str] = Field(description="Associated MITRE ATT&CK tactics")


class DocumentMappings(BaseModel):
    """Pydantic model for all technique mappings in a document."""

    techniques: list[TechniqueMapping] = Field(description="List of identified ATT&CK techniques")


class ATTACKMapper:
    """Maps document text to MITRE ATT&CK techniques using LLM."""

    SYSTEM_PROMPT = """You are an expert in cyber intelligence and the MITRE ATT&CK framework.
Your task is to analyze threat intelligence text and identify which ATT&CK techniques are described.

You will be provided with:
1. A chunk of text from a threat intelligence report
2. A list of potentially relevant ATT&CK techniques retrieved through semantic search

Your job is to:
- Identify which techniques from the retrieved list are actually described in the text
- Assign a confidence score (0.0 to 1.0) based on how explicitly the technique is mentioned
- Provide evidence by quoting the relevant part of the text
- Only include techniques that are clearly present in the text

CRITICAL: Only map techniques that describe ATTACKER/THREAT ACTOR behaviors and capabilities.
DO NOT map techniques for:
- Vendor/defender defensive actions (e.g., "Cisco blocked these IPs", "security team detected")
- Indicators of Compromise (IOCs) being reported (IPs, hashes, domains mentioned as evidence)
- Security product features or configurations
- Mitigation recommendations or patches

Confidence scoring guidelines:
- 0.8-1.0: Technique explicitly mentioned by name or with detailed behavioral description
- 0.5-0.8: Technique strongly implied with specific behavioral indicators
- 0.3-0.5: Technique possibly relevant but only tangentially related
- Below 0.3: Do not include

{format_instructions}
"""

    EXAMPLE_MAPPINGS = """
Example 1 (CORRECT - Attacker behavior):
Text: "The attackers sent phishing emails with malicious Excel documents attached."
Mapping: T1566.001 (Spearphishing Attachment), confidence 0.9
Evidence: "phishing emails with malicious Excel documents attached"

Example 2 (CORRECT - Attacker behavior):
Text: "Once inside, they established persistence using scheduled tasks."
Mapping: T1053.005 (Scheduled Task), confidence 0.85
Evidence: "established persistence using scheduled tasks"

Example 3 (CORRECT - Attacker behavior):
Text: "The malware communicated with command and control servers."
Mapping: T1071 (Application Layer Protocol), confidence 0.5
Evidence: "communicated with command and control servers"

Example 4 (INCORRECT - Vendor defensive action, DO NOT MAP):
Text: "Cisco has blocked the following IPs: 192.168.1.1, 10.0.0.1"
Mapping: NONE - This describes vendor blocking IOCs, not attacker reconnaissance

Example 5 (INCORRECT - IOC reporting, DO NOT MAP):
Text: "The following file hashes were observed: abc123, def456"
Mapping: NONE - This lists IOCs for reference, not attacker file collection techniques
"""

    def __init__(
        self,
        llm_provider: LLMProvider,
        min_confidence: float = 0.5,
    ) -> None:
        """
        Initialize the mapper.

        Args:
            llm_provider: LLM provider to use
            min_confidence: Minimum confidence threshold
        """
        self.llm = llm_provider.get_model()
        self.llm_name = llm_provider.get_name()
        self.min_confidence = min_confidence
        self.request_count = 0

        # Setup parser and prompt
        self.parser = PydanticOutputParser(pydantic_object=DocumentMappings)

        self.prompt = ChatPromptTemplate.from_messages(
            [
                ("system", self.SYSTEM_PROMPT),
                ("human", "{examples}\n\n---\n\n{context}\n\n---\n\nText to analyze:\n{text}"),
            ]
        )

    def map_chunk(
        self, text: str, retrieved_techniques: list[dict[str, Any]]
    ) -> list[TechniqueMapping]:
        """
        Map a single text chunk to ATT&CK techniques.

        Args:
            text: Text chunk to analyze
            retrieved_techniques: List of techniques retrieved from vector store

        Returns:
            List of technique mappings
        """
        # Format retrieved techniques as context
        context = self._format_techniques_context(retrieved_techniques)

        # Format prompt
        formatted_prompt = self.prompt.format_messages(
            format_instructions=self.parser.get_format_instructions(),
            examples=self.EXAMPLE_MAPPINGS,
            context=context,
            text=text,
        )

        # Get structured output from LLM
        try:
            result = self.llm.invoke(formatted_prompt)

            # Parse the result
            parsed = self.parser.parse(result.content)

            # Filter by confidence
            filtered = [t for t in parsed.techniques if t.confidence >= self.min_confidence]

            return filtered

        except Exception as e:
            print(f"Error mapping chunk: {e}")
            return []

    def map_document(
        self,
        chunks: list[dict[str, Any]],
        chunk_techniques: list[list[dict[str, Any]]],
        verbose: bool = False,
        progress_callback: Any = None,
    ) -> list[TechniqueMapping]:
        """
        Map entire document (multiple chunks) to ATT&CK techniques.

        Args:
            chunks: List of text chunks
            chunk_techniques: List of retrieved techniques for each chunk
            verbose: Whether to print verbose output
            progress_callback: Optional callback(chunk_index, total_chunks, num_found)

        Returns:
            Deduplicated list of technique mappings
        """
        all_mappings: list[TechniqueMapping] = []

        # Batch process chunks for better performance
        batch_size = 10  # Increased from 5 for better throughput
        for batch_start in range(0, len(chunks), batch_size):
            batch_end = min(batch_start + batch_size, len(chunks))
            batch_chunks = chunks[batch_start:batch_end]

            # Prepare batch prompts
            batch_prompts = []
            for i, chunk in enumerate(batch_chunks):
                idx = batch_start + i
                retrieved = chunk_techniques[idx] if idx < len(chunk_techniques) else []
                context = self._format_techniques_context(retrieved)

                formatted_prompt = self.prompt.format_messages(
                    format_instructions=self.parser.get_format_instructions(),
                    examples=self.EXAMPLE_MAPPINGS,
                    context=context,
                    text=chunk["text"],
                )
                batch_prompts.append(formatted_prompt)

            # Batch invoke LLM
            try:
                self.request_count += 1  # One batch request
                results = self.llm.batch(batch_prompts)

                for i, result in enumerate(results):
                    try:
                        parsed = self.parser.parse(result.content)
                        filtered = [
                            t for t in parsed.techniques if t.confidence >= self.min_confidence
                        ]
                        all_mappings.extend(filtered)

                        if progress_callback:
                            progress_callback(batch_start + i + 1, len(chunks), len(filtered))
                    except Exception as e:
                        if verbose:
                            print(f"Error parsing chunk {batch_start + i}: {e}")
                        if progress_callback:
                            progress_callback(batch_start + i + 1, len(chunks), 0)

            except Exception as e:
                # Fallback to sequential processing for this batch
                if verbose:
                    print(f"Batch processing failed, falling back to sequential: {e}")
                for i, chunk in enumerate(batch_chunks):
                    idx = batch_start + i
                    retrieved = chunk_techniques[idx] if idx < len(chunk_techniques) else []
                    self.request_count += 1  # One request per chunk in fallback
                    mappings = self.map_chunk(chunk["text"], retrieved)
                    all_mappings.extend(mappings)

                    if progress_callback:
                        progress_callback(idx + 1, len(chunks), len(mappings))

        # Deduplicate and consolidate
        return self._deduplicate_mappings(all_mappings)

    def _format_techniques_context(self, techniques: list[dict[str, Any]]) -> str:
        """Format retrieved techniques for LLM context."""
        if not techniques:
            return "No techniques retrieved."

        lines = ["Retrieved ATT&CK Techniques:\n"]

        for tech in techniques[:10]:  # Limit to top 10
            description = tech["description"]
            # For sub-techniques, show full description to help differentiate from parent/siblings
            # For parent techniques, limit to 400 chars to save tokens
            is_subtechnique = "." in tech["technique_id"]
            max_chars = 800 if is_subtechnique else 400

            if len(description) > max_chars:
                description = description[:max_chars] + "..."

            lines.append(
                f"- {tech['technique_id']}: {tech['name']}\n"
                f"  Tactics: {', '.join(tech['tactics'])}\n"
                f"  Description: {description}\n"
            )

        return "".join(lines)

    def _deduplicate_mappings(self, mappings: list[TechniqueMapping]) -> list[TechniqueMapping]:
        """
        Deduplicate technique mappings, keeping highest confidence.

        Args:
            mappings: List of technique mappings

        Returns:
            Deduplicated list
        """
        # Group by technique_id
        by_id: dict[str, list[TechniqueMapping]] = {}

        for mapping in mappings:
            if mapping.technique_id not in by_id:
                by_id[mapping.technique_id] = []
            by_id[mapping.technique_id].append(mapping)

        # Keep highest confidence for each technique
        deduplicated = []
        for technique_id, group in by_id.items():
            # Sort by confidence
            group.sort(key=lambda x: x.confidence, reverse=True)
            best = group[0]

            # Combine evidence from all occurrences
            all_evidence = [m.evidence for m in group]
            best.evidence = " | ".join(all_evidence[:3])  # Limit to 3 pieces

            deduplicated.append(best)

        return deduplicated


def create_mapper(
    llm_provider: str = "openai",
    model_name: str | None = None,
    min_confidence: float = 0.5,
) -> ATTACKMapper:
    """
    Factory function to create ATTACKMapper.

    Args:
        llm_provider: LLM provider name
        model_name: Optional model name
        min_confidence: Minimum confidence threshold

    Returns:
        ATTACKMapper instance
    """
    from .llm import get_llm_provider

    # Get provider with optional model name
    kwargs = {}
    if model_name:
        kwargs["model_name"] = model_name

    provider = get_llm_provider(llm_provider, **kwargs)
    return ATTACKMapper(provider, min_confidence=min_confidence)
