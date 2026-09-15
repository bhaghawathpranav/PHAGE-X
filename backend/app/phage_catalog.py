from __future__ import annotations

import csv
import hashlib
import json
import zipfile
from functools import lru_cache
from pathlib import Path
from typing import Dict, Set


DATA_DIR = Path(__file__).parent.parent / "data" / "phages"


def _sha256(path: Path) -> str:
    """
    Compute SHA256. Normalize CSV line endings so the catalog
    works on Windows (CRLF) and Linux/macOS (LF).
    """
    if path.suffix == ".csv":
        text = path.read_text(encoding="utf-8")
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


@lru_cache
def validate_phage_catalog() -> Dict[str, object]:
    manifest = json.loads((DATA_DIR / "manifest.json").read_text(encoding="utf-8"))
    for item in manifest["files"]:
        path = DATA_DIR / item["filename"]
        if not path.is_file() or _sha256(path) != item["sha256"]:
            raise RuntimeError(f"Phage catalog integrity failed: {item['filename']}")
    with zipfile.ZipFile(DATA_DIR / "phages_genomes.zip") as archive:
        genome_ids: Set[str] = {
            Path(name).stem for name in archive.namelist()
            if name.startswith("phages_genomes/") and name.endswith(".fasta") and not name.startswith("__MACOSX/")
        }
    with (DATA_DIR / "RBPbase.csv").open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    required = {"phage_ID", "protein_ID", "protein_sequence", "dna_sequence", "xgb_score"}
    if not rows or not required.issubset(rows[0]):
        raise RuntimeError("RBP catalog schema is invalid")
    rbp_ids = {row["phage_ID"] for row in rows}
    protein_ids = {row["protein_ID"] for row in rows}
    if len(protein_ids) != len(rows):
        raise RuntimeError("RBP catalog contains duplicate protein identifiers")
    if rbp_ids != genome_ids:
        raise RuntimeError("Phage genome and RBP identifiers are not aligned")
    if any(not row["protein_sequence"] or not row["dna_sequence"] for row in rows):
        raise RuntimeError("RBP catalog contains empty sequences")
    return {
        "status": "verified",
        "doi": manifest["doi"],
        "license": manifest["license"],
        "phage_genomes": len(genome_ids),
        "rbp_proteins": len(rows),
        "phage_ids": sorted(genome_ids),
        "raw_sequences_returned": False,
    }
