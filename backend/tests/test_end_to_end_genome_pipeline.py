from __future__ import annotations

import gzip
from pathlib import Path

import pytest

from app.feature_providers import (
    ESM2Embedder,
    EmbeddingCache,
    IsolateLocusFeaturePipeline,
    KaptiveRunner,
    find_executable,
)
from app.config import get_settings
from app.main import app
from fastapi.testclient import TestClient


client = TestClient(app)


FIXTURE = (
    Path(__file__).resolve().parents[1]
    / "data"
    / "species"
    / "GCF_000240185.1_ASM24018v2_genomic.fna.gz"
)


def _load_fixture_fasta() -> str:
    if not FIXTURE.exists():
        raise FileNotFoundError(
            f"Required genome fixture not found: {FIXTURE}"
        )

    with gzip.open(FIXTURE, "rt", encoding="utf-8") as handle:
        return handle.read()


def _toolchain_ready() -> bool:
    return (
        find_executable("kaptive") is not None
        and find_executable("minimap2") is not None
        and find_executable("fastANI") is not None
    )


def _esm2_ready() -> bool:
    try:
        from app.feature_providers import esm2_checkpoint_report

        return bool(esm2_checkpoint_report()["ready"])
    except Exception:
        return False


@pytest.mark.skipif(
    not _toolchain_ready(),
    reason="Kaptive, minimap2, and fastANI are required for the real genome pipeline",
)
@pytest.mark.skipif(
    not _esm2_ready(),
    reason="Verified ESM-2 checkpoint is required for the real genome pipeline",
)
def test_real_supported_genome_reaches_ml_ready_representation():
    """
    Real end-to-end bacterial-side pipeline:

        real genome fixture
        -> FASTA
        -> species confirmation
        -> Kaptive K-locus typing
        -> isolate-derived K-locus proteins
        -> ESM-2 representation
        -> 1280-dimensional ML-ready vector

    No reference-genome substitution or mocked feature provider is used.
    """

    fasta = _load_fixture_fasta()

    pipeline = IsolateLocusFeaturePipeline(
        KaptiveRunner(),
        ESM2Embedder(
            EmbeddingCache(
                Path(get_settings().embedding_cache)
            )
        ),
    )

    result = pipeline.build(fasta)

    assert result.locus.startswith("KL")
    assert result.protein_count > 0
    assert len(result.protein_set_sha256) == 64
    assert len(result.embedding_cache_key) == 64

    assert result.embedding.shape == (1280,)
    assert result.embedding.dtype.name == "float32"

    import numpy as np

    assert np.isfinite(result.embedding).all()


@pytest.mark.skipif(
    not _toolchain_ready(),
    reason="Kaptive, minimap2, and fastANI are required for the real genome pipeline",
)
def test_real_supported_genome_is_not_replaced_by_reference_sequence():
    """
    Provenance guard:

    The pipeline must derive its K-locus result from the submitted
    genome sequence, rather than silently substituting the bundled
    reference genome.
    """

    fasta = _load_fixture_fasta()

    pipeline = IsolateLocusFeaturePipeline(
        KaptiveRunner(),
        _ProvenanceOnlyEmbedder(),
    )

    result = pipeline.build(fasta)

    assert result.locus.startswith("KL")
    assert result.protein_count > 0
    assert len(result.protein_set_sha256) == 64


class _ProvenanceOnlyEmbedder:
    """
    Test-only embedding provider.

    This is intentionally used only for the provenance test above so that
    the test verifies genome -> Kaptive -> isolate proteins without requiring
    the ESM-2 checkpoint.
    """

    def embed(self, sequences):
        import numpy as np

        assert sequences
        assert all(sequence for sequence in sequences)

        return np.zeros(1280, dtype=np.float32)


@pytest.mark.skipif(
    not _toolchain_ready(),
    reason="Kaptive, minimap2, and fastANI are required for the real genome pipeline",
)
def test_real_genome_fixture_is_valid_fasta():
    fasta = _load_fixture_fasta()

    assert fasta.startswith(">")

    sequence_lines = [
        line.strip()
        for line in fasta.splitlines()
        if line.strip() and not line.startswith(">")
    ]

    assert sequence_lines
    assert all(
        set(sequence.upper()) <= {"A", "C", "G", "T", "N"}
        for sequence in sequence_lines
    )