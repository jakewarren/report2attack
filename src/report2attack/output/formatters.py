"""Output formatters for ATT&CK mappings."""

import json
import csv
from pathlib import Path
from typing import Any
from datetime import datetime
from collections import defaultdict


class OutputFormatter:
    """Base class for output formatters."""

    def __init__(self, results: dict[str, Any]) -> None:
        """
        Initialize formatter.

        Args:
            results: Analysis results dictionary
        """
        self.results = results

    def _generate_filename(self, source: str, extension: str) -> str:
        """Generate output filename."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        source_name = Path(source).stem if Path(source).exists() else "report"
        return f"report2attack_{source_name}_{timestamp}.{extension}"


class JSONFormatter(OutputFormatter):
    """JSON output formatter."""

    def format(self, output_path: str | None = None) -> str:
        """
        Format results as JSON.

        Args:
            output_path: Optional output file path

        Returns:
            Path to output file
        """
        if not output_path:
            output_path = self._generate_filename(self.results.get("source", "unknown"), "json")

        output_data = {
            "metadata": {
                "source": self.results.get("source"),
                "title": self.results.get("title"),
                "timestamp": datetime.utcnow().isoformat(),
                "attack_version": self.results.get("attack_version", "unknown"),
                "llm_provider": self.results.get("llm_provider", "unknown"),
                "min_confidence": self.results.get("min_confidence", 0.5),
            },
            "statistics": {
                "total_techniques": len(self.results.get("techniques", [])),
                "unique_techniques": len(
                    set(t["technique_id"] for t in self.results.get("techniques", []))
                ),
                "high_confidence": len(
                    [t for t in self.results.get("techniques", []) if t["confidence"] >= 0.8]
                ),
                "medium_confidence": len(
                    [t for t in self.results.get("techniques", []) if 0.5 <= t["confidence"] < 0.8]
                ),
                "low_confidence": len(
                    [t for t in self.results.get("techniques", []) if t["confidence"] < 0.5]
                ),
            },
            "techniques": self.results.get("techniques", []),
        }

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)

        return output_path


class CSVFormatter(OutputFormatter):
    """CSV output formatter."""

    def format(self, output_path: str | None = None) -> str:
        """
        Format results as CSV.

        Args:
            output_path: Optional output file path

        Returns:
            Path to output file
        """
        if not output_path:
            output_path = self._generate_filename(self.results.get("source", "unknown"), "csv")

        techniques = self.results.get("techniques", [])

        with open(output_path, "w", newline="", encoding="utf-8") as f:
            fieldnames = [
                "technique_id",
                "technique_name",
                "tactics",
                "confidence",
                "evidence",
            ]
            writer = csv.DictWriter(f, fieldnames=fieldnames)

            writer.writeheader()

            for tech in techniques:
                # Truncate evidence if too long
                evidence = tech.get("evidence", "")
                if len(evidence) > 500:
                    evidence = evidence[:497] + "..."

                writer.writerow(
                    {
                        "technique_id": tech.get("technique_id", ""),
                        "technique_name": tech.get("technique_name", ""),
                        "tactics": "; ".join(tech.get("tactics", [])),
                        "confidence": f"{tech.get('confidence', 0):.2f}",
                        "evidence": evidence,
                    }
                )

        return output_path


class MarkdownFormatter(OutputFormatter):
    """Markdown report formatter."""

    def format(self, output_path: str | None = None) -> str:
        """
        Format results as Markdown.

        Args:
            output_path: Optional output file path

        Returns:
            Path to output file
        """
        if not output_path:
            output_path = self._generate_filename(self.results.get("source", "unknown"), "md")

        techniques = self.results.get("techniques", [])

        # Group by tactic
        by_tactic: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for tech in techniques:
            for tactic in tech.get("tactics", ["uncategorized"]):
                by_tactic[tactic].append(tech)

        # Build markdown
        lines = [
            "# ATT&CK Mapping Report\n\n",
            f"**Source:** {self.results.get('source', 'Unknown')}\n",
            f"**Title:** {self.results.get('title', 'N/A')}\n",
            f"**Generated:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC\n",
            f"**LLM Provider:** {self.results.get('llm_provider', 'Unknown')}\n\n",
            "## Summary\n\n",
            f"- **Total Techniques:** {len(techniques)}\n",
            f"- **High Confidence (≥0.8):** {len([t for t in techniques if t['confidence'] >= 0.8])}\n",
            f"- **Medium Confidence (0.5-0.8):** {len([t for t in techniques if 0.5 <= t['confidence'] < 0.8])}\n",
            f"- **Tactics Covered:** {len(by_tactic)}\n\n",
            "## Table of Contents\n\n",
        ]

        # Add TOC
        for tactic in sorted(by_tactic.keys()):
            tactic_display = tactic.replace("-", " ").title()
            lines.append(f"- [{tactic_display}](#{tactic})\n")

        lines.append("\n---\n\n")

        # Add techniques by tactic
        for tactic in sorted(by_tactic.keys()):
            tactic_display = tactic.replace("-", " ").title()
            lines.append(f"## {tactic_display} {{#{tactic}}}\n\n")

            techs = by_tactic[tactic]
            techs.sort(key=lambda x: x["confidence"], reverse=True)

            for tech in techs:
                filled = int(tech["confidence"] * 10)
                empty = 10 - filled
                confidence_bar = "█" * filled + "░" * empty
                lines.append(f"### {tech['technique_id']}: {tech['technique_name']}\n\n")
                lines.append(f"**Confidence:** {confidence_bar} ({tech['confidence']:.2f})\n\n")
                lines.append(f"**Evidence:**\n> {tech['evidence']}\n\n")

            lines.append("---\n\n")

        with open(output_path, "w", encoding="utf-8") as f:
            f.writelines(lines)

        return output_path


class NavigatorFormatter(OutputFormatter):
    """ATT&CK Navigator layer formatter."""

    def _generate_filename(self, source: str, extension: str) -> str:
        """Generate output filename with navigator suffix."""
        filename = super()._generate_filename(source, extension)
        return filename.replace(f".{extension}", f"_navigator.{extension}")

    def format(self, output_path: str | None = None) -> str:
        """
        Format results as ATT&CK Navigator layer.

        Args:
            output_path: Optional output file path

        Returns:
            Path to output file
        """
        if not output_path:
            output_path = self._generate_filename(self.results.get("source", "unknown"), "json")

        techniques = self.results.get("techniques", [])

        # Build layer
        layer = {
            "name": f"report2attack - {self.results.get('title', 'Analysis')}",
            "versions": {
                "attack": "18.1",
                "navigator": "5.3.0",
                "layer": "4.5",
            },
            "domain": "enterprise-attack",
            "description": f"ATT&CK mapping generated from: {self.results.get('source', 'Unknown')}",
            "filters": {"platforms": []},
            "sorting": 0,
            "layout": {
                "layout": "side",
                "aggregateFunction": "average",
                "showID": True,
                "showName": True,
                "showAggregateScores": False,
                "countUnscored": False,
                "expandedSubtechniques": "annotated",
            },
            "hideDisabled": False,
            "techniques": [],
            "gradient": {
                "colors": ["#ffffff", "#42a5f5", "#ff4444"],
                "minValue": 0,
                "maxValue": 1,
            },
            "legendItems": [],
            "metadata": [],
            "links": [],
            "showTacticRowBackground": False,
            "tacticRowBackground": "#dddddd",
        }

        # Add techniques
        for tech in techniques:
            layer["techniques"].append(
                {
                    "techniqueID": tech["technique_id"],
                    "tactic": tech["tactics"][0] if tech["tactics"] else "",
                    "color": "",
                    "comment": f"Confidence: {tech['confidence']:.2f}\nEvidence: {tech['evidence'][:200]}",
                    "enabled": True,
                    "metadata": [],
                    "links": [],
                    "showSubtechniques": True,
                    "score": tech["confidence"],
                }
            )

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(layer, f, indent=2)

        return output_path


def format_results(
    results: dict[str, Any],
    formats: list[str],
    output_dir: str | None = None,
) -> dict[str, str]:
    """
    Format results in multiple formats.

    Args:
        results: Analysis results
        formats: List of format names ('json', 'csv', 'markdown', 'navigator')
        output_dir: Optional output directory

    Returns:
        Dictionary mapping format name to output file path
    """
    output_files = {}

    for fmt in formats:
        formatter = None

        if fmt == "json":
            formatter = JSONFormatter(results)
        elif fmt == "csv":
            formatter = CSVFormatter(results)
        elif fmt == "markdown":
            formatter = MarkdownFormatter(results)
        elif fmt == "navigator":
            formatter = NavigatorFormatter(results)
        else:
            print(f"Unknown format: {fmt}")
            continue

        output_path = None
        if output_dir:
            Path(output_dir).mkdir(parents=True, exist_ok=True)
            # Map format names to file extensions
            extension_map = {"json": "json", "csv": "csv", "markdown": "md", "navigator": "json"}
            ext = extension_map.get(fmt, fmt)
            filename = formatter._generate_filename(
                results.get("source", "unknown"),
                ext,
            )
            output_path = str(Path(output_dir) / filename)

        output_file = formatter.format(output_path)
        output_files[fmt] = output_file
        print(f"Generated {fmt} output: {output_file}")

    return output_files
