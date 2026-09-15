from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from typing import List, Tuple


from .limits import ASSEMBLY_FASTA_MAX_BYTES


MAX_ASSEMBLY_BYTES = ASSEMBLY_FASTA_MAX_BYTES


@dataclass(frozen=True)
class AssemblyQC:
    assembly_sha256: str
    contig_count: int
    total_length_bp: int
    n50_bp: int
    gc_fraction: float
    ambiguous_fraction: float
    status: str
    warnings: List[str]


def parse_assembly_fasta(fasta: str) -> Tuple[List[Tuple[str, str]], AssemblyQC]:
    if len(fasta.encode("utf-8")) > MAX_ASSEMBLY_BYTES:
        raise ValueError("Assembly FASTA exceeds the 15 MB processing limit")
    records: List[Tuple[str, str]] = []
    header = None
    sequence_parts: List[str] = []
    for raw_line in fasta.strip().splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith(">"):
            if header is not None:
                records.append((header, "".join(sequence_parts).upper()))
            header = line[1:].strip() or f"contig-{len(records) + 1}"
            sequence_parts = []
        elif header is None:
            raise ValueError("Assembly FASTA must start with a header")
        else:
            sequence_parts.append(line)
    if header is not None:
        records.append((header, "".join(sequence_parts).upper()))
    if not records or any(not sequence for _, sequence in records):
        raise ValueError("Every FASTA record must contain sequence bases")
    if any(re.search(r"[^ACGTN]", sequence) for _, sequence in records):
        raise ValueError("Assembly FASTA contains unsupported characters")
    total = sum(len(sequence) for _, sequence in records)
    if total < 100:
        raise ValueError("Assembly FASTA must contain at least 100 bases")
    lengths = sorted((len(sequence) for _, sequence in records), reverse=True)
    cumulative = 0
    n50 = 0
    for length in lengths:
        cumulative += length
        if cumulative >= total / 2:
            n50 = length
            break
    joined = "".join(sequence for _, sequence in records)
    n_count = joined.count("N")
    canonical = max(total - n_count, 1)
    gc = (joined.count("G") + joined.count("C")) / canonical
    ambiguous = n_count / total
    warnings = []
    if total < 4_000_000 or total > 7_000_000:
        warnings.append("Assembly length is outside the broad expected K. pneumoniae genome range")
    if ambiguous > 0.01:
        warnings.append("More than 1% of assembly bases are ambiguous")
    if len(records) > 500:
        warnings.append("Assembly is highly fragmented (>500 contigs)")
    if n50 < 20_000:
        warnings.append("Assembly N50 is below 20 kbp")
    normalized = "\n".join(f">{name}\n{sequence}" for name, sequence in records)
    qc = AssemblyQC(
        assembly_sha256=hashlib.sha256(normalized.encode()).hexdigest(),
        contig_count=len(records),
        total_length_bp=total,
        n50_bp=n50,
        gc_fraction=round(gc, 4),
        ambiguous_fraction=round(ambiguous, 4),
        status="review" if warnings else "pass",
        warnings=warnings,
    )
    return records, qc
