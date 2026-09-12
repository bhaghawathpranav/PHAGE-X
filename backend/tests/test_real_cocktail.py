from app.real_cocktail import ReviewedPhageMetadata, optimize_reviewed_cocktail
from app.safety import GenomicSafetyEvidence
from app.schemas import ResearchCandidate


def candidate(phage_id, score):
    return ResearchCandidate(
        phage_id=phage_id,
        compatibility=score,
        decision="higher-priority-research-signal",
        safety_status="pending",
    )


def reviewed(phage_id, family, receptor):
    return ReviewedPhageMetadata(
        phage_id,
        family,
        receptor,
        GenomicSafetyEvidence(True, True, True, True, True, True, "sha256:evidence", "reviewer-2"),
    )


def test_real_cocktail_is_blocked_without_reviewed_evidence():
    result = optimize_reviewed_cocktail([candidate("a", 0.9), candidate("b", 0.8)], [], 2)
    assert result.status == "blocked"
    assert not result.members
    assert any("independently reviewed" in item for item in result.blockers)


def test_real_cocktail_uses_only_safe_diverse_candidates():
    candidates = [candidate("a", 0.9), candidate("b", 0.8), candidate("c", 0.75)]
    metadata = [
        reviewed("a", "family-1", "receptor-1"),
        reviewed("b", "family-2", "receptor-2"),
        reviewed("c", "family-1", "receptor-1"),
    ]
    result = optimize_reviewed_cocktail(candidates, metadata, 2)
    assert result.status == "candidate-for-laboratory-validation"
    assert result.members == ["a", "b"]
    assert result.family_diversity == 1
    assert result.receptor_diversity == 1


def test_failed_safety_screen_cannot_enter_cocktail():
    bad = ReviewedPhageMetadata("b", "family-2", "receptor-2", GenomicSafetyEvidence())
    result = optimize_reviewed_cocktail(
        [candidate("a", 0.9), candidate("b", 0.8)],
        [reviewed("a", "family-1", "receptor-1"), bad],
        2,
    )
    assert result.status == "blocked"
    assert "b" not in result.members
