from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
from typing import Dict, List, Sequence

from .safety import GenomicSafetyEvidence, evaluate_genomic_safety
from .schemas import ResearchCandidate


@dataclass(frozen=True)
class ReviewedPhageMetadata:
    phage_id: str
    family: str
    receptor: str
    safety: GenomicSafetyEvidence


@dataclass(frozen=True)
class RealCocktailResult:
    status: str
    members: List[str]
    objective_score: float | None
    mean_compatibility: float | None
    family_diversity: float | None
    receptor_diversity: float | None
    redundancy: float | None
    blockers: List[str]


def optimize_reviewed_cocktail(
    candidates: Sequence[ResearchCandidate],
    metadata: Sequence[ReviewedPhageMetadata],
    size: int = 3,
) -> RealCocktailResult:
    if size not in {2, 3}:
        raise ValueError("Cocktail size must be 2 or 3")
    by_id: Dict[str, ReviewedPhageMetadata] = {item.phage_id: item for item in metadata}
    eligible = []
    missing_metadata = []
    unsafe = []
    for candidate in candidates:
        record = by_id.get(candidate.phage_id)
        if record is None or not record.family or not record.receptor:
            missing_metadata.append(candidate.phage_id)
            continue
        if not evaluate_genomic_safety(record.safety).eligible:
            unsafe.append(candidate.phage_id)
            continue
        eligible.append((candidate, record))
    if len(eligible) < size:
        blockers = []
        if missing_metadata:
            blockers.append(f"Missing reviewed family/receptor metadata for {len(missing_metadata)} ranked phages")
        if unsafe:
            blockers.append(f"Genomic safety gate blocked {len(unsafe)} ranked phages")
        blockers.append(f"Only {len(eligible)} independently reviewed candidates are eligible; {size} required")
        return RealCocktailResult("blocked", [], None, None, None, None, None, blockers)

    scored = []
    for group in combinations(eligible, size):
        families = {record.family for _, record in group}
        receptors = {record.receptor for _, record in group}
        if len(families) < 2 or len(receptors) < 2:
            continue
        compatibility = sum(candidate.compatibility for candidate, _ in group) / size
        family_diversity = len(families) / size
        receptor_diversity = len(receptors) / size
        redundant_pairs = sum(
            left.family == right.family or left.receptor == right.receptor
            for (_, left), (_, right) in combinations(group, 2)
        )
        pair_count = size * (size - 1) / 2
        redundancy = redundant_pairs / pair_count
        objective = compatibility + 0.15 * family_diversity + 0.15 * receptor_diversity - 0.1 * redundancy
        scored.append((objective, compatibility, family_diversity, receptor_diversity, redundancy, group))
    if not scored:
        return RealCocktailResult(
            "blocked", [], None, None, None, None, None,
            ["No reviewed combination satisfies minimum family and receptor diversity"],
        )
    objective, compatibility, families, receptors, redundancy, group = max(scored, key=lambda item: item[0])
    return RealCocktailResult(
        status="candidate-for-laboratory-validation",
        members=[candidate.phage_id for candidate, _ in group],
        objective_score=round(objective, 6),
        mean_compatibility=round(compatibility, 6),
        family_diversity=round(families, 6),
        receptor_diversity=round(receptors, 6),
        redundancy=round(redundancy, 6),
        blockers=[],
    )
