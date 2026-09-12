from __future__ import annotations

import hashlib
import importlib.util
import json
import shutil
import sqlite3
import subprocess
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, List, Sequence

import numpy as np


ESM2_MODEL = "esm2_t33_650M_UR50D"


@dataclass(frozen=True)
class KaptiveResult:
    best_match_locus: str
    confidence: str
    raw_record: Dict[str, str]


def capability_report() -> Dict[str, object]:
    tools = {
        "kaptive": shutil.which("kaptive"),
        "blastn": shutil.which("blastn"),
        "torch": importlib.util.find_spec("torch") is not None,
        "esm": importlib.util.find_spec("esm") is not None,
    }
    blockers = [name for name, value in tools.items() if not value]
    return {
        "novel_isolate_pipeline_ready": not blockers,
        "tools": {name: bool(value) for name, value in tools.items()},
        "blockers": blockers,
        "esm2_model": ESM2_MODEL,
        "embedding_dimensions": 1280,
    }


class KaptiveRunner:
    def __init__(self, executable: str = "kaptive", database: str = "kpsc_k", timeout_seconds: int = 600):
        self.executable = executable
        self.database = database
        self.timeout_seconds = timeout_seconds

    def type_assembly(self, fasta: str) -> KaptiveResult:
        if not shutil.which(self.executable):
            raise RuntimeError("Kaptive executable is unavailable")
        with tempfile.TemporaryDirectory(prefix="phagex-kaptive-") as directory:
            root = Path(directory)
            assembly = root / "isolate.fasta"
            output = root / "kaptive.tsv"
            assembly.write_text(fasta, encoding="utf-8")
            subprocess.run(
                [self.executable, "assembly", self.database, str(assembly), "-o", str(output)],
                check=True,
                timeout=self.timeout_seconds,
                capture_output=True,
                text=True,
            )
            lines = output.read_text(encoding="utf-8").splitlines()
            if len(lines) < 2:
                raise RuntimeError("Kaptive did not return a typing record")
            header, values = lines[0].split("\t"), lines[1].split("\t")
            record = dict(zip(header, values))
            locus = record.get("Best match locus") or record.get("Best match locus name") or "Unknown"
            confidence = record.get("Confidence") or "Unknown"
            return KaptiveResult(best_match_locus=locus, confidence=confidence, raw_record=record)


class EmbeddingCache:
    def __init__(self, path: Path):
        self.path = path

    @staticmethod
    def key(proteins: Sequence[str], model_name: str = ESM2_MODEL) -> str:
        normalized = "\n".join(sequence.strip().upper() for sequence in proteins)
        return hashlib.sha256(f"{model_name}\n{normalized}".encode()).hexdigest()

    def get(self, key: str) -> np.ndarray | None:
        if not self.path.exists():
            return None
        with sqlite3.connect(self.path) as connection:
            connection.execute("CREATE TABLE IF NOT EXISTS embeddings (key TEXT PRIMARY KEY, vector BLOB NOT NULL, metadata TEXT NOT NULL)")
            row = connection.execute("SELECT vector FROM embeddings WHERE key = ?", (key,)).fetchone()
        return np.frombuffer(row[0], dtype=np.float32).copy() if row else None

    def put(self, key: str, vector: np.ndarray, metadata: Dict[str, object]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        value = np.asarray(vector, dtype=np.float32)
        with sqlite3.connect(self.path) as connection:
            connection.execute("CREATE TABLE IF NOT EXISTS embeddings (key TEXT PRIMARY KEY, vector BLOB NOT NULL, metadata TEXT NOT NULL)")
            connection.execute(
                "INSERT OR REPLACE INTO embeddings (key, vector, metadata) VALUES (?, ?, ?)",
                (key, value.tobytes(), json.dumps(metadata, sort_keys=True)),
            )


class ESM2Embedder:
    """Lazy local ESM-2 provider matching PhageHostLearn's 1,280D model family."""

    def __init__(self, cache: EmbeddingCache):
        self.cache = cache
        self._model = None
        self._alphabet = None

    def embed(self, proteins: Sequence[str]) -> np.ndarray:
        if not proteins:
            raise ValueError("At least one protein sequence is required")
        key = self.cache.key(proteins)
        cached = self.cache.get(key)
        if cached is not None:
            return cached
        try:
            import esm
            import torch
        except ImportError as error:
            raise RuntimeError("Local PyTorch and fair-esm are required for uncached ESM-2 inference") from error
        if self._model is None:
            self._model, self._alphabet = esm.pretrained.esm2_t33_650M_UR50D()
            self._model.eval()
        converter = self._alphabet.get_batch_converter()
        cleaned = [sequence.strip().upper() for sequence in proteins]
        if any(len(sequence) > 1022 for sequence in cleaned):
            raise ValueError("ESM-2 provider limits individual proteins to 1,022 residues")
        data = [(f"protein-{index}", sequence) for index, sequence in enumerate(cleaned)]
        _, _, tokens = converter(data)
        with torch.no_grad():
            output = self._model(tokens, repr_layers=[33], return_contacts=False)["representations"][33]
        vectors = [output[index, 1 : len(sequence) + 1].mean(0).cpu().numpy() for index, sequence in enumerate(cleaned)]
        combined = np.mean(vectors, axis=0).astype(np.float32)
        self.cache.put(key, combined, {"model": ESM2_MODEL, "protein_count": len(cleaned), "dimensions": 1280})
        return combined

