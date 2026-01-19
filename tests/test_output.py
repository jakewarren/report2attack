"""Tests for output formatters."""

import csv
import json
from pathlib import Path

import pytest

from report2attack.output.formatters import (
    CSVFormatter,
    JSONFormatter,
    MarkdownFormatter,
    NavigatorFormatter,
    format_results,
)


@pytest.fixture
def sample_results() -> dict:
    """Sample results for testing."""
    return {
        "source": "https://example.com/threat-report",
        "title": "Sample Threat Report",
        "llm_provider": "openai-gpt-4",
        "min_confidence": 0.5,
        "attack_version": "18.1",
        "techniques": [
            {
                "technique_id": "T1566.001",
                "technique_name": "Spearphishing Attachment",
                "confidence": 0.9,
                "evidence": "Attackers sent malicious email attachments to targets",
                "tactics": ["initial-access"],
            },
            {
                "technique_id": "T1078",
                "technique_name": "Valid Accounts",
                "confidence": 0.7,
                "evidence": "Used stolen credentials to access systems",
                "tactics": ["defense-evasion", "persistence"],
            },
            {
                "technique_id": "T1059.001",
                "technique_name": "PowerShell",
                "confidence": 0.4,  # Below typical threshold
                "evidence": "Executed PowerShell commands",
                "tactics": ["execution"],
            },
        ],
    }


class TestJSONFormatter:
    """Tests for JSON output formatter."""

    def test_format_json(self, sample_results: dict, tmp_path: Path) -> None:
        """Test JSON formatting."""
        formatter = JSONFormatter(sample_results)
        output_path = tmp_path / "output.json"

        result_path = formatter.format(str(output_path))

        assert Path(result_path).exists()
        with open(result_path) as f:
            data = json.load(f)

        assert "metadata" in data
        assert "statistics" in data
        assert "techniques" in data
        assert data["metadata"]["source"] == sample_results["source"]

    def test_json_statistics(self, sample_results: dict, tmp_path: Path) -> None:
        """Test statistics in JSON output."""
        formatter = JSONFormatter(sample_results)
        output_path = tmp_path / "output.json"

        formatter.format(str(output_path))

        with open(output_path) as f:
            data = json.load(f)

        stats = data["statistics"]
        assert stats["total_techniques"] == 3
        assert stats["high_confidence"] == 1  # >= 0.8
        assert stats["medium_confidence"] == 1  # 0.5-0.8
        assert stats["low_confidence"] == 1  # < 0.5

    def test_json_without_output_path(self, sample_results: dict) -> None:
        """Test JSON formatting with auto-generated filename."""
        formatter = JSONFormatter(sample_results)
        result_path = formatter.format()

        assert Path(result_path).exists()
        assert result_path.endswith(".json")

        # Cleanup
        Path(result_path).unlink()


class TestCSVFormatter:
    """Tests for CSV output formatter."""

    def test_format_csv(self, sample_results: dict, tmp_path: Path) -> None:
        """Test CSV formatting."""
        formatter = CSVFormatter(sample_results)
        output_path = tmp_path / "output.csv"

        result_path = formatter.format(str(output_path))

        assert Path(result_path).exists()
        with open(result_path, newline="") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        assert len(rows) == 3
        assert rows[0]["technique_id"] == "T1566.001"
        assert rows[0]["technique_name"] == "Spearphishing Attachment"

    def test_csv_multi_tactic_handling(self, sample_results: dict, tmp_path: Path) -> None:
        """Test handling of techniques with multiple tactics."""
        formatter = CSVFormatter(sample_results)
        output_path = tmp_path / "output.csv"

        formatter.format(str(output_path))

        with open(output_path, newline="") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        # Find T1078 which has multiple tactics
        t1078 = next(r for r in rows if r["technique_id"] == "T1078")
        assert ";" in t1078["tactics"] or "," in t1078["tactics"]

    def test_csv_evidence_truncation(self, tmp_path: Path) -> None:
        """Test that long evidence is truncated."""
        results = {
            "source": "test",
            "title": "Test",
            "llm_provider": "test",
            "min_confidence": 0.5,
            "attack_version": "18.1",
            "techniques": [
                {
                    "technique_id": "T1566.001",
                    "technique_name": "Test",
                    "confidence": 0.9,
                    "evidence": "A" * 600,  # Very long evidence
                    "tactics": ["initial-access"],
                }
            ],
        }

        formatter = CSVFormatter(results)
        output_path = tmp_path / "output.csv"
        formatter.format(str(output_path))

        with open(output_path, newline="") as f:
            reader = csv.DictReader(f)
            row = next(reader)

        assert len(row["evidence"]) <= 503  # 500 + "..."


class TestMarkdownFormatter:
    """Tests for Markdown output formatter."""

    def test_format_markdown(self, sample_results: dict, tmp_path: Path) -> None:
        """Test Markdown formatting."""
        formatter = MarkdownFormatter(sample_results)
        output_path = tmp_path / "output.md"

        result_path = formatter.format(str(output_path))

        assert Path(result_path).exists()
        with open(result_path) as f:
            content = f.read()

        assert "# ATT&CK Mapping Report" in content
        assert "## Summary" in content
        assert "T1566.001" in content

    def test_markdown_tactic_grouping(self, sample_results: dict, tmp_path: Path) -> None:
        """Test that techniques are grouped by tactic."""
        formatter = MarkdownFormatter(sample_results)
        output_path = tmp_path / "output.md"

        formatter.format(str(output_path))

        with open(output_path) as f:
            content = f.read()

        # Should have sections for each tactic
        assert "## Initial Access" in content or "## initial-access" in content.lower()
        assert "## Execution" in content or "## execution" in content.lower()

    def test_markdown_confidence_bars(self, sample_results: dict, tmp_path: Path) -> None:
        """Test confidence bars in markdown."""
        formatter = MarkdownFormatter(sample_results)
        output_path = tmp_path / "output.md"

        formatter.format(str(output_path))

        with open(output_path) as f:
            content = f.read()

        # Should contain confidence bars (█)
        assert "█" in content

    def test_markdown_table_of_contents(self, sample_results: dict, tmp_path: Path) -> None:
        """Test TOC generation."""
        formatter = MarkdownFormatter(sample_results)
        output_path = tmp_path / "output.md"

        formatter.format(str(output_path))

        with open(output_path) as f:
            content = f.read()

        assert "## Table of Contents" in content


class TestNavigatorFormatter:
    """Tests for ATT&CK Navigator formatter."""

    def test_format_navigator(self, sample_results: dict, tmp_path: Path) -> None:
        """Test Navigator layer formatting."""
        formatter = NavigatorFormatter(sample_results)
        output_path = tmp_path / "output.json"

        result_path = formatter.format(str(output_path))

        assert Path(result_path).exists()
        with open(result_path) as f:
            layer = json.load(f)

        assert "name" in layer
        assert "versions" in layer
        assert "domain" in layer
        assert layer["domain"] == "enterprise-attack"

    def test_navigator_techniques(self, sample_results: dict, tmp_path: Path) -> None:
        """Test techniques in Navigator layer."""
        formatter = NavigatorFormatter(sample_results)
        output_path = tmp_path / "output.json"

        formatter.format(str(output_path))

        with open(output_path) as f:
            layer = json.load(f)

        assert "techniques" in layer
        assert len(layer["techniques"]) == 3

        # Verify technique structure
        tech = layer["techniques"][0]
        assert "techniqueID" in tech
        assert "score" in tech
        assert "comment" in tech

    def test_navigator_confidence_mapping(self, sample_results: dict, tmp_path: Path) -> None:
        """Test confidence score mapping."""
        formatter = NavigatorFormatter(sample_results)
        output_path = tmp_path / "output.json"

        formatter.format(str(output_path))

        with open(output_path) as f:
            layer = json.load(f)

        # Find T1566.001 which has 0.9 confidence
        tech = next(t for t in layer["techniques"] if t["techniqueID"] == "T1566.001")
        assert tech["score"] == 0.9

    def test_navigator_gradient(self, sample_results: dict, tmp_path: Path) -> None:
        """Test gradient configuration."""
        formatter = NavigatorFormatter(sample_results)
        output_path = tmp_path / "output.json"

        formatter.format(str(output_path))

        with open(output_path) as f:
            layer = json.load(f)

        assert "gradient" in layer
        assert layer["gradient"]["minValue"] == 0
        assert layer["gradient"]["maxValue"] == 1


class TestFormatResults:
    """Tests for format_results helper function."""

    def test_format_multiple_formats(self, sample_results: dict, tmp_path: Path) -> None:
        """Test formatting in multiple formats."""
        formats = ["json", "csv", "markdown"]
        output_files = format_results(sample_results, formats, str(tmp_path))

        assert len(output_files) == 3
        assert "json" in output_files
        assert "csv" in output_files
        assert "markdown" in output_files

        # Verify all files exist
        for fmt, path in output_files.items():
            assert Path(path).exists()

    def test_format_all_formats(self, sample_results: dict, tmp_path: Path) -> None:
        """Test formatting all supported formats."""
        formats = ["json", "csv", "markdown", "navigator"]
        output_files = format_results(sample_results, formats, str(tmp_path))

        assert len(output_files) == 4

    def test_format_invalid_format(self, sample_results: dict, tmp_path: Path) -> None:
        """Test handling of invalid format."""
        formats = ["json", "invalid_format"]
        output_files = format_results(sample_results, formats, str(tmp_path))

        # Should skip invalid format but process valid ones
        assert len(output_files) == 1
        assert "json" in output_files

    def test_format_without_output_dir(self, sample_results: dict) -> None:
        """Test formatting without output directory."""
        formats = ["json"]
        output_files = format_results(sample_results, formats)

        assert len(output_files) == 1
        # Cleanup
        for path in output_files.values():
            Path(path).unlink()


class TestEdgeCases:
    """Tests for edge cases in formatters."""

    def test_empty_techniques_list(self, tmp_path: Path) -> None:
        """Test formatting with no techniques."""
        results = {
            "source": "test",
            "title": "Test",
            "llm_provider": "test",
            "min_confidence": 0.5,
            "attack_version": "18.1",
            "techniques": [],
        }

        formatter = JSONFormatter(results)
        output_path = tmp_path / "empty.json"
        formatter.format(str(output_path))

        with open(output_path) as f:
            data = json.load(f)

        assert data["statistics"]["total_techniques"] == 0

    def test_special_characters_in_evidence(self, tmp_path: Path) -> None:
        """Test handling of special characters in evidence."""
        results = {
            "source": "test",
            "title": "Test",
            "llm_provider": "test",
            "min_confidence": 0.5,
            "attack_version": "18.1",
            "techniques": [
                {
                    "technique_id": "T1566.001",
                    "technique_name": "Test",
                    "confidence": 0.9,
                    "evidence": 'Evidence with "quotes" and \\slashes\\',
                    "tactics": ["initial-access"],
                }
            ],
        }

        # Test JSON
        formatter = JSONFormatter(results)
        json_path = tmp_path / "special.json"
        formatter.format(str(json_path))

        with open(json_path) as f:
            data = json.load(f)
        assert data["techniques"][0]["evidence"] == results["techniques"][0]["evidence"]

        # Test CSV
        csv_formatter = CSVFormatter(results)
        csv_path = tmp_path / "special.csv"
        csv_formatter.format(str(csv_path))

        with open(csv_path, newline="") as f:
            reader = csv.DictReader(f)
            row = next(reader)
        assert '"' in row["evidence"] or "quotes" in row["evidence"]
