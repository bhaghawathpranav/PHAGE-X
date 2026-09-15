from fastapi.testclient import TestClient
import importlib

import numpy as np

from app.main import app
from app.feature_providers import IsolateLocusProteinSet
from app.species import SpeciesConfirmation


client = TestClient(app)


def test_health():
    response = client.get("/api/health")

    assert response.json()["status"] == "ok"
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-request-id"]


def test_readiness_checks_catalog():
    result = client.get("/api/ready").json()

    assert result == {"status": "ready", "isolates": 2, "phages": 6}


def test_preloaded_case_complete_path():
    response = client.post(
        "/api/analyze",
        json={
            "isolate_id": "kp-mdr-001",
            "cocktail_size": 3,
        },
    )

    assert response.status_code == 200

    result = response.json()

    assert result["isolate"]["organism"] == "Klebsiella pneumoniae"
    assert len(result["ranked_phages"]) >= 5
    assert len(result["cocktail"]["members"]) == 3
    assert (
        result["ranked_phages"][0]["compatibility"]
        >= result["ranked_phages"][1]["compatibility"]
    )
    assert "laboratory validation only" in result["disclaimer"]

    selected = {
        item["phage_id"]
        for item in result["cocktail"]["members"]
    }

    phages = {
        item["id"]: item
        for item in result["ranked_phages"]
    }

    assert len({phages[item]["family"] for item in selected}) >= 2
    assert len({phages[item]["receptor"] for item in selected}) >= 2


def test_uploaded_fasta_path_is_deterministic():
    fasta = ">demo\n" + "ACGT" * 40

    first = client.post(
        "/api/analyze",
        json={
            "fasta": fasta,
            "demo_fasta": True,
            "cocktail_size": 2,
        },
    )

    second = client.post(
        "/api/analyze",
        json={
            "fasta": fasta,
            "demo_fasta": True,
            "cocktail_size": 2,
        },
    )

    assert first.status_code == 200
    assert first.json()["isolate"]["id"] == second.json()["isolate"]["id"]
    assert len(first.json()["cocktail"]["members"]) == 2
    assert first.json()["sequence_qc"]["status"] == "pass"
    assert first.json()["feature_source"] == "deterministic-placeholder"


def test_rejects_short_fasta():
    response = client.post(
        "/api/analyze",
        json={
            "fasta": ">short\nACGT",
            "demo_fasta": True,
            "cocktail_size": 2,
        },
    )

    assert response.status_code == 422


def test_rejects_multiple_fasta_records():
    fasta = (
        ">one\n"
        + "ACGT" * 30
        + "\n>two\n"
        + "ACGT" * 30
    )

    response = client.post(
        "/api/analyze",
        json={
            "fasta": fasta,
            "demo_fasta": True,
            "cocktail_size": 2,
        },
    )

    assert response.status_code == 422
    assert "exactly one" in response.json()["detail"]


def test_flags_ambiguous_sequence_for_review():
    fasta = ">ambiguous\n" + "N" * 20 + "ACGT" * 30

    response = client.post(
        "/api/analyze",
        json={
            "fasta": fasta,
            "demo_fasta": True,
            "cocktail_size": 2,
        },
    )

    assert response.status_code == 200
    assert response.json()["sequence_qc"]["status"] == "review"


def test_arbitrary_fasta_cannot_silently_use_demo_model():
    fasta = ">new-isolate\n" + "ACGT" * 40

    response = client.post(
        "/api/analyze",
        json={
            "fasta": fasta,
            "cocktail_size": 2,
        },
    )

    assert response.status_code == 422
    assert "/api/jobs/novel-rank" in response.json()["detail"]


def test_assembly_inspection_is_fail_closed_without_toolchain():
    fasta = (
        ">contig-one\n"
        + "ACGT" * 40
        + "\n>contig-two\n"
        + "GGCC" * 30
    )

    response = client.post(
        "/api/inspect-assembly",
        json={"fasta": fasta},
    )

    assert response.status_code == 200

    result = response.json()

    assert result["contig_count"] == 2
    assert result["sequence_persisted"] is False
    assert result["pipeline_status"] in {
        "blocked",
        "ready-for-local-feature-extraction",
    }
    assert "digest-provenance" in result["completed_stages"]


def test_reference_locus_metadata_does_not_return_sequences():
    response = client.get("/api/reference-locus/KL107")

    assert response.status_code == 200

    result = response.json()

    assert result["locus"] == "KL107"
    assert result["protein_count"] >= 10
    assert result["raw_sequences_returned"] is False
    assert len(result["protein_set_sha256"]) == 64
    assert len(result["database_sha256"]) == 64
    assert "sequences" not in result


def test_isolate_locus_endpoint_returns_only_provenance_metadata(
    monkeypatch,
):
    main_module = importlib.import_module("app.main")

    submitted_fasta = ">chromosome\n" + "ACGT" * 1_000_000
    captured = {}

    class Runner:
        def type_and_extract_assembly(self, fasta):
            captured["fasta"] = fasta

            return IsolateLocusProteinSet(
                locus="KL107",
                confidence="Typeable",
                percent_identity=100,
                percent_coverage=100,
                names=["KL107_01", "KL107_02"],
                sequences=["ACDE", "MKTAY"],
                protein_set_sha256="a" * 64,
                missing_genes=[],
                problems="",
                kaptive_version="3.2.0",
            )

    class SpeciesRunner:
        def confirm_klebsiella_pneumoniae(self, fasta):
            return SpeciesConfirmation(
                organism="Klebsiella pneumoniae",
                reference_accession="GCF_000240185.1",
                ani_percent=99.2,
                alignment_fraction=0.98,
                mapped_fragments=100,
                total_fragments=102,
                status="confirmed-reference-ani",
                reference_sha256="b" * 64,
                fastani_version="version 1.33",
            )

    class Embedder:
        def __init__(self, cache):
            pass

        def embed(self, sequences):
            return np.ones(1280, dtype=np.float32)

    monkeypatch.setattr(
        main_module,
        "KaptiveRunner",
        Runner,
    )

    monkeypatch.setattr(
        main_module,
        "FastANIRunner",
        SpeciesRunner,
    )

    monkeypatch.setattr(
        main_module,
        "ESM2Embedder",
        Embedder,
    )

    response = client.post(
        "/api/extract-isolate-locus",
        json={"fasta": submitted_fasta},
    )

    assert response.status_code == 200

    # Critical Task 2 provenance guarantee:
    # the exact FASTA submitted by the user reaches the Kaptive runner.
    assert captured["fasta"] == submitted_fasta

    result = response.json()

    assert result["locus"] == "KL107"
    assert result["protein_count"] == 2
    assert result["species_status"] == "confirmed-reference-ani"
    assert result["species_ani_percent"] == 99.2
    assert (
        result["species_reference_accession"]
        == "GCF_000240185.1"
    )
    assert result["pipeline_status"].startswith("blocked")
    assert result["raw_sequences_returned"] is False
    assert result["sequence_persisted"] is False
    assert "sequences" not in result

    embedding_response = client.post(
        "/api/embed-isolate-locus",
        json={"fasta": submitted_fasta},
    )

    assert embedding_response.status_code == 200

    embedding = embedding_response.json()

    assert embedding["dimensions"] == 1280
    assert embedding["model"] == "esm2_t33_650M_UR50D"
    assert embedding["raw_embedding_returned"] is False
    assert embedding["sequence_persisted"] is False
    assert len(embedding["embedding_sha256"]) == 64


def test_rank_novel_isolate_returns_rankings_and_cocktail(
    monkeypatch,
):
    main_module = importlib.import_module("app.main")

    submitted_fasta = ">chromosome\n" + "ACGT" * 1_000_000

    class SpeciesRunner:
        def confirm_klebsiella_pneumoniae(self, fasta):
            assert fasta == submitted_fasta

            return SpeciesConfirmation(
                organism="Klebsiella pneumoniae",
                reference_accession="GCF_000240185.1",
                ani_percent=99.2,
                alignment_fraction=0.98,
                mapped_fragments=100,
                total_fragments=102,
                status="confirmed-reference-ani",
                reference_sha256="b" * 64,
                fastani_version="version 1.33",
            )

    class KaptiveRunnerStub:
        def type_and_extract_assembly(self, fasta):
            assert fasta == submitted_fasta

            return IsolateLocusProteinSet(
                locus="KL107",
                confidence="Typeable",
                percent_identity=100,
                percent_coverage=100,
                names=["KL107_01", "KL107_02"],
                sequences=["ACDE", "MKTAY"],
                protein_set_sha256="a" * 64,
                missing_genes=[],
                problems="",
                kaptive_version="3.2.0",
            )

    class Embedder:
        def __init__(self, cache):
            pass

        def embed(self, sequences):
            assert sequences == ["ACDE", "MKTAY"]

            model = main_module.get_research_model()

            return np.asarray(
                model.host_vectors[0],
                dtype=np.float32,
            )

    monkeypatch.setattr(
        main_module,
        "FastANIRunner",
        SpeciesRunner,
    )

    monkeypatch.setattr(
        main_module,
        "KaptiveRunner",
        KaptiveRunnerStub,
    )

    monkeypatch.setattr(
        main_module,
        "ESM2Embedder",
        Embedder,
    )

    response = client.post(
        "/api/rank-novel-isolate",
        json={
            "fasta": submitted_fasta,
            "limit": 5,
        },
    )

    assert response.status_code == 200, response.text

    result = response.json()

    assert result["locus"] == "KL107"
    assert result["species_status"] == "confirmed-reference-ani"
    assert result["model_version"]
    assert result["feature_source"]
    assert len(result["feature_sha256"]) == 64
    assert result["distribution_status"]
    assert result["cocktail_status"] in {
        "ready",
        "blocked",
        "insufficient-reviewed-metadata",
    }
    assert (
        "Novel-isolate predictions require laboratory confirmation"
        in result["cocktail_blockers"]
    )
    assert isinstance(result["candidates"], list)
    assert len(result["candidates"]) <= 5
    assert isinstance(result["cocktail_members"], list)