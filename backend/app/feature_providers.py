from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import re
import shutil
import sqlite3
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Sequence

import numpy as np

from .species import fastani_available


ESM2_MODEL = "esm2_t33_650M_UR50D"
ESM2_MANIFEST = Path(__file__).parent.parent / "data" / "esm2" / "manifest.json"


def esm2_checkpoint_directory() -> Path:
    configured = os.getenv("PHAGEX_ESM2_CHECKPOINT_DIR")
    return Path(configured) if configured else Path.home() / ".cache" / "torch" / "hub" / "checkpoints"


def esm2_checkpoint_report() -> Dict[str, object]:
    if not ESM2_MANIFEST.exists():
        return {"ready": False, "reason": "checkpoint manifest is unavailable"}
    manifest = json.loads(ESM2_MANIFEST.read_text(encoding="utf-8"))
    directory = esm2_checkpoint_directory()
    signatures = tuple(
        (
            item["filename"],
            (directory / item["filename"]).stat().st_size,
            (directory / item["filename"]).stat().st_mtime_ns,
        )
        for item in manifest["files"]
        if (directory / item["filename"]).is_file()
    )
    if len(signatures) != len(manifest["files"]):
        missing = next(item["filename"] for item in manifest["files"] if not (directory / item["filename"]).is_file())
        return {"ready": False, "reason": f"missing {missing}"}
    return _verify_esm2_files(json.dumps(manifest, sort_keys=True), str(directory), signatures)


@lru_cache(maxsize=4)
def _verify_esm2_files(manifest_json: str, directory_value: str, signatures: tuple) -> Dict[str, object]:
    manifest = json.loads(manifest_json)
    directory = Path(directory_value)
    observed: Dict[str, str] = {}
    for item in manifest["files"]:
        path = directory / item["filename"]
        digest = file_sha256(path)
        if digest != item["sha256"]:
            return {"ready": False, "reason": f"checksum mismatch for {item['filename']}"}
        observed[item["filename"]] = digest
    return {"ready": True, "sha256": observed}


def find_executable(name: str) -> str | None:
    resolved = shutil.which(name)
    if resolved:
        return resolved
    candidates = [
        Path(sys.prefix) / "bin" / name,
        Path(sys.executable).parent / name,
    ]
    return next((str(candidate) for candidate in candidates if candidate.exists() and candidate.is_file()), None)


@dataclass(frozen=True)
class KaptiveResult:
    best_match_locus: str
    confidence: str
    raw_record: Dict[str, str]


@dataclass(frozen=True)
class LocusProteinSet:
    locus: str
    names: List[str]
    sequences: List[str]
    protein_set_sha256: str
    database_sha256: str
    kaptive_version: str


@dataclass(frozen=True)
class IsolateLocusProteinSet:
    locus: str
    confidence: str
    percent_identity: float
    percent_coverage: float
    names: List[str]
    sequences: List[str]
    protein_set_sha256: str
    missing_genes: List[str]
    problems: str
    kaptive_version: str


@dataclass(frozen=True)
class LocusFeatureResult:
    locus: str
    protein_count: int
    protein_set_sha256: str
    embedding_cache_key: str
    embedding: np.ndarray


def capability_report() -> Dict[str, object]:
    checkpoint = esm2_checkpoint_report()
    tools = {
        "kaptive": find_executable("kaptive"),
        "blastn": find_executable("blastn"),
        "minimap2": find_executable("minimap2"),
        "fastani": fastani_available(),
        "torch": importlib.util.find_spec("torch") is not None,
        "esm": importlib.util.find_spec("esm") is not None,
        "esm2_checkpoint": checkpoint["ready"],
    }
    blockers = [name for name, value in tools.items() if not value]
    return {
        "novel_isolate_pipeline_ready": not blockers,
        "tools": {name: bool(value) for name, value in tools.items()},
        "blockers": blockers,
        "esm2_model": ESM2_MODEL,
        "embedding_dimensions": 1280,
        "esm2_checkpoint": checkpoint,
    }


class KaptiveRunner:
    def __init__(self, executable: str = "kaptive", database: str = "kpsc_k", timeout_seconds: int = 600):
        self.executable = executable
        self.database = database
        self.timeout_seconds = timeout_seconds

    def type_assembly(self, fasta: str) -> KaptiveResult:
        executable = find_executable(self.executable)
        if not executable:
            raise RuntimeError("Kaptive executable is unavailable")
        if not find_executable("minimap2"):
            raise RuntimeError("minimap2 executable is unavailable")
        with tempfile.TemporaryDirectory(prefix="phagex-kaptive-") as directory:
            root = Path(directory)
            assembly = root / "isolate.fasta"
            output = root / "kaptive.tsv"
            assembly.write_text(fasta, encoding="utf-8")
            subprocess.run(
                [executable, "assembly", self.database, str(assembly), "-o", str(output)],
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
            confidence = record.get("Match confidence") or record.get("Confidence") or "Unknown"
            return KaptiveResult(best_match_locus=locus, confidence=confidence, raw_record=record)

    def type_and_extract_assembly(self, fasta: str) -> IsolateLocusProteinSet:
        executable = find_executable(self.executable)
        if not executable:
            raise RuntimeError("Kaptive executable is unavailable")
        if not find_executable("minimap2"):
            raise RuntimeError("minimap2 executable is unavailable")
        with tempfile.TemporaryDirectory(prefix="phagex-kaptive-") as directory:
            root = Path(directory)
            assembly = root / "isolate.fasta"
            json_output = root / "kaptive.jsonl"
            assembly.write_text(fasta, encoding="utf-8")
            try:
                subprocess.run(
                    [
                        executable,
                        "assembly",
                        self.database,
                        str(assembly),
                        "--json",
                        str(json_output),
                        "--out",
                        str(root / "kaptive.tsv"),
                        "--threads",
                        "1",
                    ],
                    check=True,
                    timeout=self.timeout_seconds,
                    capture_output=True,
                    text=True,
                )
            except subprocess.TimeoutExpired as error:
                raise RuntimeError("Kaptive assembly typing timed out") from error
            except subprocess.CalledProcessError as error:
                detail = (error.stderr or "Kaptive assembly typing failed").strip().splitlines()[-1]
                raise RuntimeError(detail[:300]) from error
            lines = [line for line in json_output.read_text(encoding="utf-8").splitlines() if line.strip()]
            if len(lines) != 1:
                raise RuntimeError("Kaptive did not return exactly one isolate record")
            result = isolate_proteins_from_kaptive_record(json.loads(lines[0]))
            return IsolateLocusProteinSet(
                **result,
                kaptive_version=self._version(executable),
            )

    def extract_reference_proteins(self, locus: str) -> LocusProteinSet:
        if not re.fullmatch(r"KL[0-9]{1,4}", locus):
            raise ValueError("K locus must use the form KL followed by 1–4 digits")
        executable = find_executable(self.executable)
        if not executable:
            raise RuntimeError("Kaptive executable is unavailable")
        completed = subprocess.run(
            [executable, "extract", self.database, "--filter", f"^{locus}$", "--faa", "-"],
            check=True,
            timeout=self.timeout_seconds,
            capture_output=True,
            text=True,
        )
        names, sequences = parse_protein_fasta(completed.stdout)
        if not sequences:
            raise ValueError(f"No reference proteins found for {locus}")
        version = self._version(executable)
        try:
            import kaptive

            database_path = Path(kaptive.__file__).parent.parent / "reference_database" / "Klebsiella_k_locus_primary_reference.gbk"
            database_sha256 = file_sha256(database_path)
        except (ImportError, FileNotFoundError):
            database_sha256 = "unavailable"
        normalized = "\n".join(f">{name}\n{sequence}" for name, sequence in zip(names, sequences))
        return LocusProteinSet(
            locus=locus,
            names=names,
            sequences=sequences,
            protein_set_sha256=hashlib.sha256(normalized.encode()).hexdigest(),
            database_sha256=database_sha256,
            kaptive_version=version,
        )

    @staticmethod
    def _version(executable: str) -> str:
        return subprocess.run(
            [executable, "--version"], check=True, capture_output=True, text=True, timeout=30
        ).stdout.strip()


def file_sha256(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def parse_protein_fasta(value: str) -> tuple[List[str], List[str]]:
    names: List[str] = []
    sequences: List[str] = []
    current_name = None
    parts: List[str] = []
    for raw_line in value.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith(">"):
            if current_name is not None:
                sequences.append("".join(parts).rstrip("*").upper())
            current_name = line[1:].split()[0]
            names.append(current_name)
            parts = []
        elif current_name is None:
            raise ValueError("Protein FASTA must begin with a header")
        else:
            parts.append(line)
    if current_name is not None:
        sequences.append("".join(parts).rstrip("*").upper())
    if len(names) != len(sequences) or any(not sequence for sequence in sequences):
        raise ValueError("Protein FASTA contains an empty or malformed record")
    allowed = re.compile(r"^[ACDEFGHIKLMNPQRSTVWYBXZJUO]+$")
    if any(not allowed.fullmatch(sequence) for sequence in sequences):
        raise ValueError("Protein FASTA contains unsupported residues")
    return names, sequences


def isolate_proteins_from_kaptive_record(record: Dict[str, object]) -> Dict[str, object]:
    locus = str(record.get("best_match", ""))
    if not re.fullmatch(r"KL[0-9]{1,4}", locus):
        raise ValueError("Kaptive did not produce a valid Klebsiella K-locus call")
    genes = record.get("expected_genes_inside_locus")
    if not isinstance(genes, list) or not genes:
        raise ValueError("Kaptive returned no expected genes inside the called locus")
    missing = record.get("missing_genes", [])
    if not isinstance(missing, list):
        raise ValueError("Kaptive returned malformed missing-gene evidence")
    confidence = str(record.get("confidence", "Unknown"))
    problems = str(record.get("problems", ""))
    if confidence != "Typeable":
        raise ValueError(f"Kaptive confidence is {confidence}; a Typeable call is required")
    if missing:
        raise ValueError(f"Missing K-locus genes prevent embedding: {', '.join(map(str, missing[:5]))}")
    if problems:
        raise ValueError(f"Kaptive reported locus problems ({problems}); manual review is required")
    names: List[str] = []
    sequences: List[str] = []
    incomplete: List[str] = []
    for gene in genes:
        if not isinstance(gene, dict):
            raise ValueError("Kaptive returned a malformed gene record")
        name = str(gene.get("gene", ""))
        sequence = str(gene.get("protein_seq", "")).rstrip("*").upper()
        partial = str(gene.get("partial", "False")).lower() == "true"
        phenotype = str(gene.get("phenotype", ""))
        coverage = float(gene.get("percent_coverage", 0))
        if not name or not sequence:
            incomplete.append(name or "unnamed")
            continue
        if partial or phenotype == "truncated" or coverage < 95:
            incomplete.append(name)
        if len(sequence) > 1022:
            incomplete.append(name)
        names.append(name)
        sequences.append(sequence)
    if incomplete:
        raise ValueError(f"Incomplete K-locus genes prevent embedding: {', '.join(incomplete[:5])}")
    if len(names) != len(set(names)):
        raise ValueError("Kaptive returned duplicate expected genes")
    parse_protein_fasta("".join(f">{name}\n{sequence}\n" for name, sequence in zip(names, sequences)))
    normalized = "\n".join(f">{name}\n{sequence}" for name, sequence in zip(names, sequences))
    return {
        "locus": locus,
        "confidence": confidence,
        "percent_identity": float(record.get("percent_identity", 0)),
        "percent_coverage": float(record.get("percent_coverage", 0)),
        "names": names,
        "sequences": sequences,
        "protein_set_sha256": hashlib.sha256(normalized.encode()).hexdigest(),
        "missing_genes": [str(item) for item in missing],
        "problems": problems,
    }


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
            checkpoint = esm2_checkpoint_report()
            if not checkpoint["ready"]:
                raise RuntimeError(f"Verified local ESM-2 checkpoint required: {checkpoint['reason']}")
            model_path = esm2_checkpoint_directory() / f"{ESM2_MODEL}.pt"
            safe_globals = getattr(torch.serialization, "safe_globals", None)
            if safe_globals:
                with safe_globals([argparse.Namespace]):
                    self._model, self._alphabet = esm.pretrained.load_model_and_alphabet_local(model_path)
            else:
                self._model, self._alphabet = esm.pretrained.load_model_and_alphabet_local(model_path)
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


class ReferenceLocusFeaturePipeline:
    """Extract canonical K-locus proteins and pass them to the local ESM-2 provider.

    This is a reference-locus feature path, not proof that an uploaded isolate has
    a complete or identical locus. Isolate-specific CDS extraction remains gated.
    """

    def __init__(self, extractor: KaptiveRunner, embedder: ESM2Embedder):
        self.extractor = extractor
        self.embedder = embedder

    def build(self, locus: str) -> LocusFeatureResult:
        proteins = self.extractor.extract_reference_proteins(locus)
        embedding = np.asarray(self.embedder.embed(proteins.sequences), dtype=np.float32)
        if embedding.shape != (1280,):
            raise ValueError(f"ESM-2 provider returned {embedding.shape}, expected (1280,)")
        if not np.isfinite(embedding).all():
            raise ValueError("ESM-2 provider returned non-finite values")
        return LocusFeatureResult(
            locus=proteins.locus,
            protein_count=len(proteins.sequences),
            protein_set_sha256=proteins.protein_set_sha256,
            embedding_cache_key=EmbeddingCache.key(proteins.sequences),
            embedding=embedding,
        )


class IsolateLocusFeaturePipeline:
    """Type an assembly, extract validated isolate proteins, and embed them."""

    def __init__(self, extractor: KaptiveRunner, embedder: ESM2Embedder):
        self.extractor = extractor
        self.embedder = embedder

    def build(self, fasta: str) -> LocusFeatureResult:
        proteins = self.extractor.type_and_extract_assembly(fasta)
        embedding = np.asarray(self.embedder.embed(proteins.sequences), dtype=np.float32)
        if embedding.shape != (1280,):
            raise ValueError(f"ESM-2 provider returned {embedding.shape}, expected (1280,)")
        if not np.isfinite(embedding).all():
            raise ValueError("ESM-2 provider returned non-finite values")
        return LocusFeatureResult(
            locus=proteins.locus,
            protein_count=len(proteins.sequences),
            protein_set_sha256=proteins.protein_set_sha256,
            embedding_cache_key=EmbeddingCache.key(proteins.sequences),
            embedding=embedding,
        )
