import gzip

import pytest

from app.species import FastANIRunner, REFERENCE_PATH, fastani_available


@pytest.mark.skipif(not fastani_available(), reason="fastANI not installed")
def test_pinned_reference_confirms_itself_with_high_coverage():
    with gzip.open(REFERENCE_PATH, "rt", encoding="utf-8") as handle:
        result = FastANIRunner(timeout_seconds=60).confirm_klebsiella_pneumoniae(handle.read())
    assert result.status == "confirmed-reference-ani"
    assert result.reference_accession == "GCF_000240185.1"
    assert result.ani_percent == 100
    assert result.alignment_fraction > 0.99
    assert len(result.reference_sha256) == 64


@pytest.mark.skipif(not fastani_available(), reason="fastANI not installed")
def test_unrelated_synthetic_assembly_is_not_species_confirmed():
    fasta = ">unrelated\n" + "ACGT" * 1_000_000
    with pytest.raises(ValueError, match="No trustworthy ANI match"):
        FastANIRunner(timeout_seconds=60).confirm_klebsiella_pneumoniae(fasta)
