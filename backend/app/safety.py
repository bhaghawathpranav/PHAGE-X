from dataclasses import dataclass, fields
from typing import List, Optional


@dataclass(frozen=True)
class GenomicSafetyEvidence:
    lysogeny_screen_passed: Optional[bool] = None
    toxin_screen_passed: Optional[bool] = None
    virulence_screen_passed: Optional[bool] = None
    amr_screen_passed: Optional[bool] = None
    contamination_screen_passed: Optional[bool] = None
    assembly_qc_passed: Optional[bool] = None
    source_digest: Optional[str] = None
    reviewer: Optional[str] = None


@dataclass(frozen=True)
class SafetyGateResult:
    eligible: bool
    status: str
    blockers: List[str]


def evaluate_genomic_safety(evidence: GenomicSafetyEvidence) -> SafetyGateResult:
    blockers = []
    for item in fields(evidence):
        if not item.name.endswith("_passed"):
            continue
        value = getattr(evidence, item.name)
        if value is not True:
            blockers.append(item.name.replace("_", " "))
    if not evidence.source_digest:
        blockers.append("missing source artifact digest")
    if not evidence.reviewer:
        blockers.append("missing independent reviewer")
    return SafetyGateResult(
        eligible=not blockers,
        status="passed-independent-review" if not blockers else "blocked",
        blockers=blockers,
    )

