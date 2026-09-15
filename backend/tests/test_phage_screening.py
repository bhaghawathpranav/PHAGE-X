import pytest

from app.phage_screening import evidence_status, genome_qc, registry_status


def test_real_genome_qc_is_traceable_but_not_safety_clearance():
    result = genome_qc("A1a")
    assert result["length_bp"] > 10_000
    assert len(result["sequence_sha256"]) == 64
    assert "not biological safety clearance" in result["interpretation"]


def test_empty_review_registry_fails_closed():
    result = evidence_status("A1a")
    assert result["evidence_status"] == "not-reviewed"
    assert result["cocktail_eligible"] is False
    assert len(result["required_screens"]) == 6
    assert registry_status()["cocktail_eligible_records"] == 0


def test_unknown_phage_is_rejected():
    with pytest.raises(KeyError):
        genome_qc("not-in-catalog")
