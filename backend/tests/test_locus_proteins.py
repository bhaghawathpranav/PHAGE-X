import numpy as np
import pytest

from app.feature_providers import (
    KaptiveRunner,
    LocusProteinSet,
    ReferenceLocusFeaturePipeline,
    find_executable,
    parse_protein_fasta,
)


def test_protein_fasta_parser_removes_terminal_stops():
    names, sequences = parse_protein_fasta(">KL1_01_gene\nMKTAY*\n>KL1_02_gene\nACDE\n")
    assert names == ["KL1_01_gene", "KL1_02_gene"]
    assert sequences == ["MKTAY", "ACDE"]


def test_protein_fasta_parser_rejects_invalid_residue():
    with pytest.raises(ValueError, match="unsupported residues"):
        parse_protein_fasta(">bad\nMKT?\n")


@pytest.mark.skipif(not find_executable("kaptive"), reason="Kaptive not installed")
def test_extracts_pinned_kl107_reference_proteins():
    result = KaptiveRunner().extract_reference_proteins("KL107")
    assert result.locus == "KL107"
    assert len(result.sequences) >= 10
    assert all(name.startswith("KL107_") for name in result.names)
    assert all("*" not in sequence for sequence in result.sequences)
    assert len(result.protein_set_sha256) == 64
    assert len(result.database_sha256) == 64


def test_rejects_unsafe_locus_filter():
    with pytest.raises(ValueError, match="K locus"):
        KaptiveRunner().extract_reference_proteins("KL107.*")


def test_reference_locus_proteins_are_handed_to_embedding_provider():
    proteins = LocusProteinSet(
        locus="KL107",
        names=["KL107_01", "KL107_02"],
        sequences=["MKTAY", "ACDE"],
        protein_set_sha256="a" * 64,
        database_sha256="b" * 64,
        kaptive_version="3.2.0",
    )

    class Extractor:
        def extract_reference_proteins(self, locus):
            assert locus == "KL107"
            return proteins

    class Embedder:
        def embed(self, sequences):
            assert sequences == proteins.sequences
            return np.arange(1280, dtype=np.float32)

    result = ReferenceLocusFeaturePipeline(Extractor(), Embedder()).build("KL107")
    assert result.locus == "KL107"
    assert result.protein_count == 2
    assert result.embedding.shape == (1280,)
    assert len(result.embedding_cache_key) == 64


def test_reference_locus_pipeline_rejects_wrong_embedding_shape():
    class Extractor:
        def extract_reference_proteins(self, locus):
            return LocusProteinSet(locus, ["one"], ["ACDE"], "a" * 64, "b" * 64, "3.2.0")

    class Embedder:
        def embed(self, sequences):
            return np.zeros(12, dtype=np.float32)

    with pytest.raises(ValueError, match="expected"):
        ReferenceLocusFeaturePipeline(Extractor(), Embedder()).build("KL107")
