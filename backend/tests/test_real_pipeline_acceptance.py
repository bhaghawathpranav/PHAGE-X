"""Opt-in acceptance test for the complete local uploaded-genome path.

Run explicitly with PHAGEX_RUN_REAL_PIPELINE=1 after installing the native
bioinformatics tools and verified ESM-2 checkpoint. It is excluded from the
fast unit suite because it processes a 5.6 MB assembly and loads ESM-2 650M.
"""

import os
from pathlib import Path

import pytest

from app.feature_providers import ESM2_DIMENSIONS, capability_report
from app.main import rank_novel_isolate
from app.pdf_report import build_novel_rank_pdf
from app.research_model import get_research_model
from app.schemas import NovelIsolateRankRequest


SAMPLE = (
    Path(__file__).resolve().parents[1]
    / "data"
    / "samples"
    / "GCF_000364385.3_ASM36438v3_genomic.fna"
)


@pytest.mark.skipif(
    os.getenv("PHAGEX_RUN_REAL_PIPELINE") != "1",
    reason="set PHAGEX_RUN_REAL_PIPELINE=1 to run the local ESM-2 acceptance path",
)
def test_verified_genome_runs_through_real_model_and_fail_closed_cocktail():
    capability = capability_report()
    assert capability["novel_isolate_pipeline_ready"], capability["blockers"]
    assert capability["embedding_dimensions"] == ESM2_DIMENSIONS
    fasta = SAMPLE.read_text(encoding="utf-8")

    result = rank_novel_isolate(NovelIsolateRankRequest(fasta=fasta, limit=105))

    assert result.species_status == "confirmed-reference-ani"
    assert result.species_ani_percent >= 95
    assert result.locus == "KL74"
    assert len(result.feature_sha256) == 64
    assert len(result.candidates) == 105
    assert len({item.compatibility for item in result.candidates}) > 1
    assert result.candidates == sorted(
        result.candidates, key=lambda item: item.compatibility, reverse=True
    )
    assert result.cocktail_status == "blocked"
    assert result.cocktail_members == []
    assert result.cocktail_objective_score is None
    assert any("reviewed" in item.lower() for item in result.cocktail_blockers)

    pdf = build_novel_rank_pdf(result, get_research_model().status())
    assert pdf.startswith(b"%PDF-")
    assert len(pdf) > 5_000
