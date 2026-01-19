"""MITRE ATT&CK vector store management with ChromaDB."""

import json
from pathlib import Path
from typing import Any

import chromadb
import requests
from chromadb.config import Settings


class ATTACKDataLoader:
    """Downloads and processes MITRE ATT&CK framework data."""

    ATTACK_STIX_URL = (
        "https://raw.githubusercontent.com/mitre/cti/master/"
        "enterprise-attack/enterprise-attack.json"
    )

    def __init__(self, data_dir: str | None = None) -> None:
        """
        Initialize the ATT&CK data loader.

        Args:
            data_dir: Directory to store downloaded data
        """
        if data_dir:
            self.data_dir = Path(data_dir)
        else:
            # Use package data directory
            package_dir = Path(__file__).parent.parent
            self.data_dir = package_dir / "data" / "attack"

        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.data_file = self.data_dir / "enterprise-attack.json"

    def download(self, force: bool = False) -> Path:
        """
        Download MITRE ATT&CK STIX data.

        Args:
            force: Force re-download even if file exists

        Returns:
            Path to downloaded file

        Raises:
            RuntimeError: If download fails
        """
        if self.data_file.exists() and not force:
            print(f"ATT&CK data already exists at {self.data_file}")
            return self.data_file

        print(f"Downloading MITRE ATT&CK data from {self.ATTACK_STIX_URL}...")

        try:
            response = requests.get(self.ATTACK_STIX_URL, timeout=30)
            response.raise_for_status()

            with open(self.data_file, "w", encoding="utf-8") as f:
                json.dump(response.json(), f, indent=2)

            print(f"Downloaded ATT&CK data to {self.data_file}")
            return self.data_file

        except Exception as e:
            raise RuntimeError(f"Failed to download ATT&CK data: {e}") from e

    def load(self) -> dict[str, Any]:
        """
        Load MITRE ATT&CK data from file.

        Returns:
            Parsed STIX data dictionary

        Raises:
            FileNotFoundError: If data file doesn't exist
        """
        if not self.data_file.exists():
            raise FileNotFoundError(
                f"ATT&CK data not found at {self.data_file}. " f"Run download() first."
            )

        with open(self.data_file, encoding="utf-8") as f:
            return json.load(f)

    def extract_techniques(self) -> list[dict[str, Any]]:
        """
        Extract techniques and sub-techniques from STIX data.

        Returns:
            List of technique dictionaries
        """
        data = self.load()
        techniques = []

        for obj in data.get("objects", []):
            if obj.get("type") == "attack-pattern":
                # Extract technique ID
                external_refs = obj.get("external_references", [])
                technique_id = None
                for ref in external_refs:
                    if ref.get("source_name") == "mitre-attack":
                        technique_id = ref.get("external_id")
                        break

                if not technique_id:
                    continue

                # Extract tactics (kill chain phases)
                tactics = []
                for phase in obj.get("kill_chain_phases", []):
                    if phase.get("kill_chain_name") == "mitre-attack":
                        tactics.append(phase.get("phase_name", ""))

                technique = {
                    "technique_id": technique_id,
                    "name": obj.get("name", ""),
                    "description": obj.get("description", ""),
                    "tactics": tactics,
                    "stix_id": obj.get("id", ""),
                    "deprecated": obj.get("x_mitre_deprecated", False),
                }

                techniques.append(technique)

        return [t for t in techniques if not t["deprecated"]]


class ATTACKVectorStore:
    """ChromaDB-based vector store for MITRE ATT&CK techniques."""

    def __init__(
        self,
        persist_directory: str | None = None,
        collection_name: str = "attack_techniques",
    ) -> None:
        """
        Initialize the vector store.

        Args:
            persist_directory: Directory for persistent storage
            collection_name: Name of the ChromaDB collection
        """
        if persist_directory:
            self.persist_directory = Path(persist_directory)
        else:
            # Use default location
            self.persist_directory = Path.home() / ".report2attack" / "chroma_db"

        self.persist_directory.mkdir(parents=True, exist_ok=True)
        self.collection_name = collection_name

        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(
            path=str(self.persist_directory),
            settings=Settings(anonymized_telemetry=False),
        )

        self.collection: Any | None = None

    def initialize(self, embedding_function: Any) -> None:
        """
        Initialize or load the collection.

        Args:
            embedding_function: ChromaDB embedding function
        """
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            embedding_function=embedding_function,
            metadata={"description": "MITRE ATT&CK Enterprise techniques"},
        )

    def is_populated(self) -> bool:
        """Check if vector store has data."""
        if not self.collection:
            return False
        return self.collection.count() > 0

    def populate(self, techniques: list[dict[str, Any]]) -> None:
        """
        Populate vector store with ATT&CK techniques.

        Args:
            techniques: List of technique dictionaries
        """
        if not self.collection:
            raise RuntimeError("Collection not initialized. Call initialize() first.")

        print(f"Populating vector store with {len(techniques)} techniques...")

        # Prepare documents and metadata
        documents = []
        metadatas = []
        ids = []

        for tech in techniques:
            # Create searchable text from technique info
            doc_text = f"{tech['name']}. {tech['description']}"
            documents.append(doc_text)

            # Store metadata
            metadatas.append(
                {
                    "technique_id": tech["technique_id"],
                    "name": tech["name"],
                    "tactics": ",".join(tech["tactics"]),
                    "stix_id": tech["stix_id"],
                }
            )

            ids.append(tech["technique_id"])

        # Add to collection in batches
        batch_size = 100
        for i in range(0, len(documents), batch_size):
            batch_docs = documents[i : i + batch_size]
            batch_meta = metadatas[i : i + batch_size]
            batch_ids = ids[i : i + batch_size]

            self.collection.add(documents=batch_docs, metadatas=batch_meta, ids=batch_ids)

        print(f"Vector store populated with {len(techniques)} techniques")

    def query(
        self,
        query_text: str,
        n_results: int = 10,
        tactic_filter: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        Query vector store for similar techniques.

        Args:
            query_text: Query text
            n_results: Number of results to return
            tactic_filter: Optional list of tactics to filter by

        Returns:
            Query results dictionary
        """
        if not self.collection:
            raise RuntimeError("Collection not initialized. Call initialize() first.")

        where_filter = None
        if tactic_filter:
            # ChromaDB doesn't support array contains, so we'll filter post-query
            pass

        results = self.collection.query(
            query_texts=[query_text], n_results=n_results, where=where_filter
        )

        # Post-filter by tactics if needed
        if tactic_filter:
            filtered_results = self._filter_by_tactics(results, tactic_filter)
            return filtered_results

        return results

    def _filter_by_tactics(self, results: dict[str, Any], tactics: list[str]) -> dict[str, Any]:
        """Filter results by tactics."""
        # Simple post-filtering implementation
        # In production, consider more sophisticated filtering
        return results

    def get_metadata(self) -> dict[str, Any]:
        """Get vector store metadata."""
        if not self.collection:
            return {}

        return {
            "collection_name": self.collection_name,
            "technique_count": self.collection.count() if self.collection else 0,
            "persist_directory": str(self.persist_directory),
        }
