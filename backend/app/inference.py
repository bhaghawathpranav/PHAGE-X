"""Deterministic, explainable baseline used by the offline PHAGE-X MVP.

This is a research-ranking demonstration, not a validated host-range predictor.
"""

from __future__ import annotations

import itertools
import math
import uuid
from typing import Any, Dict, Iterable, List, Sequence, Tuple

from .schemas import (
    AnalysisResponse,
    CocktailCandidate,
    CocktailMember,
    Contribution,
    IsolateSummary,
    RankedPhage,
    SequenceQC,
)
from .sequence import parse_single_fasta


MODEL_NAME = "PX-Linear v0.1 (frozen demo baseline)"
DISCLAIMER = "For laboratory validation only — not for clinical decision-making or treatment selection."
MAX_EXHAUSTIVE_COCKTAIL_CANDIDATES = 60


def _cosine(a: Sequence[float], b: Sequence[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm = math.sqrt(sum(x * x for x in a)) * math.sqrt(sum(y * y for y in b))
    return dot / norm if norm else 0.0


def _sigmoid(value: float) -> float:
    return 1.0 / (1.0 + math.exp(-value))


def _jaccard(a: Iterable[str], b: Iterable[str]) -> float:
    left, right = set(a), set(b)
    union = left | right
    return len(left & right) / len(union) if union else 0.0


def isolate_from_fasta(fasta: str, name: str | None = None) -> Dict[str, Any]:
    parsed = parse_single_fasta(fasta)
    digest = bytes.fromhex(parsed.sha256)
    embedding = [round((digest[i] / 255.0) * 2 - 1, 4) for i in range(8)]
    return {
        "id": f"upload-{digest.hex()[:8]}",
        "name": name or parsed.header,
        "organism": "Klebsiella pneumoniae (user-supplied; unverified)",
        "sequence_type": "Unknown",
        "k_locus": "Unknown",
        "receptor": "unknown",
        "resistance": ["Not inferred in MVP"],
        "description": "Uploaded FASTA represented by a deterministic demo embedding.",
        "embedding": embedding,
        "_sequence_qc": SequenceQC(
            sequence_sha256=parsed.sha256,
            length_bp=len(parsed.sequence),
            gc_fraction=parsed.gc_fraction,
            ambiguous_fraction=parsed.ambiguous_fraction,
            status=parsed.status,
            warnings=parsed.warnings,
        ),
    }


def _rank_phage(isolate: Dict[str, Any], phage: Dict[str, Any]) -> Tuple[RankedPhage, Dict[str, float]]:
    cosine_raw = _cosine(isolate["embedding"], phage["embedding"])
    cosine_scaled = (cosine_raw + 1) / 2
    receptor_match = 1.0 if isolate.get("receptor") == phage["receptor"] else 0.0
    known_target = 1.0 if "Klebsiella pneumoniae" in phage["host_evidence"] else 0.0
    evidence_quality = phage["evidence_quality"]

    contributions = {
        "Embedding similarity": 2.4 * cosine_scaled,
        "Receptor / K-locus match": 0.9 * receptor_match,
        "K. pneumoniae evidence": 0.35 * known_target,
        "Evidence quality": 0.3 * evidence_quality,
    }
    logit = -1.85 + sum(contributions.values())
    score = _sigmoid(logit)
    confidence = "higher" if score >= 0.78 else "moderate" if score >= 0.6 else "exploratory"

    rationale = [f"Embedding similarity: {cosine_scaled:.2f}"]
    if receptor_match:
        rationale.append(f"Receptor annotation matches {isolate.get('k_locus', 'isolate')} profile")
    elif isolate.get("receptor") == "unknown":
        rationale.append("Receptor match unavailable for uploaded sequence")
    else:
        rationale.append("No exact receptor annotation match")
    rationale.append("Strictly lytic demo catalog entry")

    ranked = RankedPhage(
        id=phage["id"],
        name=phage["name"],
        family=phage["family"],
        receptor=phage["receptor"],
        compatibility=round(score, 4),
        confidence_band=confidence,
        rationale=rationale,
        contributions=[
            Contribution(label=key, value=round(value, 3), direction="supports")
            for key, value in contributions.items()
        ],
        evidence=phage["evidence"],
        safety_status=phage.get("safety_status", "demo-unverified"),
    )
    return ranked, {"embedding_similarity": cosine_scaled}


def _pair_diversity(a: Dict[str, Any], b: Dict[str, Any]) -> float:
    family_bonus = 1.0 if a["family"] != b["family"] else 0.25
    embedding_distance = 1 - ((_cosine(a["embedding"], b["embedding"]) + 1) / 2)
    receptor_bonus = 1.0 if a["receptor"] != b["receptor"] else 0.2
    return 0.4 * family_bonus + 0.35 * embedding_distance + 0.25 * receptor_bonus


def _build_cocktail(
    ranked: List[RankedPhage], phages_by_id: Dict[str, Dict[str, Any]], size: int
) -> CocktailCandidate:
    if len(ranked) > MAX_EXHAUSTIVE_COCKTAIL_CANDIDATES:
        raise ValueError(
            f"Exhaustive cocktail search supports at most {MAX_EXHAUSTIVE_COCKTAIL_CANDIDATES} "
            "ranked phages; prefilter the catalog before combination scoring"
        )
    best = None
    for selected_tuple in itertools.combinations(ranked, size):
        families = {phages_by_id[item.id]["family"] for item in selected_tuple}
        receptors = {phages_by_id[item.id]["receptor"] for item in selected_tuple}
        if len(families) < 2 or len(receptors) < 2:
            continue
        pairs = list(itertools.combinations(selected_tuple, 2))
        diversity = sum(_pair_diversity(phages_by_id[a.id], phages_by_id[b.id]) for a, b in pairs) / len(pairs)
        redundancy = sum(
            _jaccard(phages_by_id[a.id]["host_range_tags"], phages_by_id[b.id]["host_range_tags"])
            for a, b in pairs
        ) / len(pairs)
        compatibility = sum(item.compatibility for item in selected_tuple) / len(selected_tuple)
        objective = 0.65 * compatibility + 0.25 * diversity - 0.35 * redundancy
        if best is None or objective > best[0]:
            best = (objective, list(selected_tuple), compatibility, diversity, redundancy)
    if best is None:
        raise ValueError("No cocktail satisfies the minimum family and receptor diversity constraints")
    objective, selected, compatibility, diversity, redundancy = best

    members = []
    for index, item in enumerate(selected):
        role = "Compatibility anchor" if index == 0 else "Diversity complement"
        members.append(CocktailMember(phage_id=item.id, name=item.name, role=role, compatibility=item.compatibility))

    return CocktailCandidate(
        members=members,
        compatibility=round(compatibility, 3),
        diversity=round(diversity, 3),
        redundancy=round(redundancy, 3),
        objective_score=round(objective, 3),
        rationale=[
            "All eligible combinations were compared at the requested cocktail size.",
            "Selection rewards family, receptor, and embedding diversity.",
            "Overlapping host-range tags are penalized as redundancy.",
        ],
        constraints_passed=[
            "All catalog members are marked strictly lytic in demo metadata",
            "At least two annotated phage families",
            "At least two annotated receptor targets",
            "No duplicate phage identifiers",
        ],
    )


def analyze(isolate: Dict[str, Any], phages: List[Dict[str, Any]], size: int, input_mode: str) -> AnalysisResponse:
    ranked = [_rank_phage(isolate, phage)[0] for phage in phages if phage.get("strictly_lytic")]
    ranked.sort(key=lambda item: item.compatibility, reverse=True)
    by_id = {phage["id"]: phage for phage in phages}
    cocktail = _build_cocktail(ranked, by_id, size)
    summary = IsolateSummary(**{key: isolate[key] for key in IsolateSummary.model_fields})
    return AnalysisResponse(
        analysis_id=str(uuid.uuid4()),
        isolate=summary,
        input_mode=input_mode,
        feature_source="deterministic-placeholder" if input_mode == "uploaded-fasta-demo" else "precomputed-demo",
        sequence_qc=isolate.get("_sequence_qc"),
        model=MODEL_NAME,
        ranked_phages=ranked,
        cocktail=cocktail,
        limitations=[
            "Demo embeddings are synthetic-compatible and are not substitutes for validated ESM-2 representations.",
            "Compatibility scores are relative ranking signals, not probabilities of clinical success.",
            "No wet-lab host-range, synergy, resistance evolution, dosing, or safety validation is performed.",
            "Demo phage safety status is unverified; production use must block candidates without independent genomic review.",
        ],
        disclaimer=DISCLAIMER,
    )
