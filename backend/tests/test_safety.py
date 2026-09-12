from app.safety import GenomicSafetyEvidence, evaluate_genomic_safety


def test_unverified_phage_is_blocked():
    result = evaluate_genomic_safety(GenomicSafetyEvidence())
    assert not result.eligible
    assert "missing independent reviewer" in result.blockers


def test_all_screens_and_review_are_required():
    result = evaluate_genomic_safety(
        GenomicSafetyEvidence(
            lysogeny_screen_passed=True,
            toxin_screen_passed=True,
            virulence_screen_passed=True,
            amr_screen_passed=True,
            contamination_screen_passed=True,
            assembly_qc_passed=True,
            source_digest="sha256:example",
            reviewer="independent-reviewer-id",
        )
    )
    assert result.eligible
    assert result.status == "passed-independent-review"

