from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path


DATA_DIR = Path(__file__).parent.parent / "data" / "species"
MANIFEST_PATH = DATA_DIR / "manifest.json"
REFERENCE_PATH = DATA_DIR / "GCF_000240185.1_ASM24018v2_genomic.fna.gz"


@dataclass(frozen=True)
class SpeciesConfirmation:
    organism: str
    reference_accession: str
    ani_percent: float
    alignment_fraction: float
    mapped_fragments: int
    total_fragments: int
    status: str
    reference_sha256: str
    fastani_version: str


def _executable(name: str) -> str | None:
    resolved = shutil.which(name)
    if resolved:
        return resolved
    candidate = Path(sys.prefix) / "bin" / name
    return str(candidate) if candidate.is_file() else None


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


class FastANIRunner:
    def __init__(self, executable: str = "fastANI", timeout_seconds: int = 300):
        self.executable = executable
        self.timeout_seconds = timeout_seconds

    def confirm_klebsiella_pneumoniae(self, fasta: str) -> SpeciesConfirmation:
        executable = _executable(self.executable)
        if not executable:
            raise RuntimeError("fastANI executable is unavailable")
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        observed_digest = _sha256(REFERENCE_PATH)
        if observed_digest != manifest["compressed_sha256"]:
            raise RuntimeError("Species reference genome failed checksum verification")
        with tempfile.TemporaryDirectory(prefix="phagex-fastani-") as directory:
            root = Path(directory)
            query = root / "isolate.fasta"
            output = root / "fastani.tsv"
            query.write_text(fasta, encoding="utf-8")
            try:
                subprocess.run(
                    [executable, "-q", str(query), "-r", str(REFERENCE_PATH), "-o", str(output), "-t", "1"],
                    check=True,
                    timeout=self.timeout_seconds,
                    capture_output=True,
                    text=True,
                )
            except subprocess.TimeoutExpired as error:
                raise RuntimeError("fastANI species confirmation timed out") from error
            except subprocess.CalledProcessError as error:
                detail = (error.stderr or "fastANI species confirmation failed").strip().splitlines()[-1]
                raise RuntimeError(detail[:300]) from error
            lines = [line for line in output.read_text(encoding="utf-8").splitlines() if line.strip()]
            if len(lines) != 1:
                raise ValueError("No trustworthy ANI match was reported for the K. pneumoniae reference")
            columns = lines[0].split("\t")
            if len(columns) != 5:
                raise RuntimeError("fastANI returned a malformed result")
            ani = float(columns[2])
            mapped, total = int(columns[3]), int(columns[4])
            fraction = mapped / total if total else 0.0
            if ani < manifest["minimum_ani_percent"] or fraction < manifest["minimum_alignment_fraction"]:
                raise ValueError(
                    f"Species confirmation failed: ANI {ani:.2f}% and alignment fraction {fraction:.3f}"
                )
            version = subprocess.run(
                [executable, "--version"], check=True, capture_output=True, text=True, timeout=30
            )
            return SpeciesConfirmation(
                organism="Klebsiella pneumoniae",
                reference_accession=manifest["reference_accession"],
                ani_percent=ani,
                alignment_fraction=fraction,
                mapped_fragments=mapped,
                total_fragments=total,
                status="confirmed-reference-ani",
                reference_sha256=observed_digest,
                fastani_version=(version.stdout or version.stderr).strip(),
            )


def fastani_available() -> bool:
    return _executable("fastANI") is not None
