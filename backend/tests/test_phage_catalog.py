from app.phage_catalog import validate_phage_catalog
from app.research_model import get_research_model


def test_raw_phage_genomes_and_rbps_align_with_runtime_catalog():
    report = validate_phage_catalog()
    model = get_research_model()
    assert report["status"] == "verified"
    assert report["phage_genomes"] == 105
    assert report["rbp_proteins"] == 274
    assert set(report["phage_ids"]) == set(model.phage_ids)
    assert report["raw_sequences_returned"] is False
