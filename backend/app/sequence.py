from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from typing import List


MAX_FASTA_BYTES = 5_000_000


@dataclass(frozen=True)
class ParsedSequence:
    header: str
    sequence: str
    sha256: str
    gc_fraction: float
    ambiguous_fraction: float
    status: str
    warnings: List[str]


def parse_single_fasta(fasta: str) -> ParsedSequence:
    if len(fasta.encode("utf-8")) > MAX_FASTA_BYTES:
        raise ValueError("FASTA input exceeds the 5 MB research-demo limit")
    lines = [line.strip() for line in fasta.strip().splitlines() if line.strip()]
    headers = [index for index, line in enumerate(lines) if line.startswith(">")]
    if not headers or headers[0] != 0:
        raise ValueError("FASTA input must start with a header line beginning with '>'")
    if len(headers) != 1:
        raise ValueError("Submit exactly one FASTA record per analysis")
    sequence = "".join(lines[1:]).upper()
    if len(sequence) < 100:
        raise ValueError("FASTA sequence must contain at least 100 bases for this demo")
    if re.search(r"[^ACGTN]", sequence):
        raise ValueError("FASTA sequence contains unsupported characters")
    ambiguous = sequence.count("N") / len(sequence)
    canonical = max(len(sequence) - sequence.count("N"), 1)
    gc = (sequence.count("G") + sequence.count("C")) / canonical
    warnings = []
    if ambiguous > 0.05:
        warnings.append("More than 5% of bases are ambiguous")
    if gc < 0.25 or gc > 0.75:
        warnings.append("GC fraction is outside the broad bacterial QC range")
    return ParsedSequence(
        header=lines[0][1:].strip() or "Uploaded isolate",
        sequence=sequence,
        sha256=hashlib.sha256(sequence.encode()).hexdigest(),
        gc_fraction=round(gc, 4),
        ambiguous_fraction=round(ambiguous, 4),
        status="review" if warnings else "pass",
        warnings=warnings,
    )

