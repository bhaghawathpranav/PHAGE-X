from pathlib import Path

import hashlib
import json
import sqlite3

import numpy as np

import app.feature_providers as providers

from app.feature_providers import EmbeddingCache, capability_report


def test_embedding_cache_uses_sequence_digest_not_raw_sequence(tmp_path: Path):
    cache = EmbeddingCache(tmp_path / "embeddings.sqlite3")

    key = cache.key(["MKTAYIAK"])
    vector = np.arange(1280, dtype=np.float32)

    cache.put(key, vector, {"model": "test", "dimensions": 1280})

    observed = cache.get(key)

    assert np.array_equal(observed, vector)
    assert b"MKTAYIAK" not in cache.path.read_bytes()


def test_embedding_key_is_deterministic(tmp_path: Path):
    cache = EmbeddingCache(tmp_path / "embeddings.sqlite3")

    proteins = ["MKTAYIAK", "GATCGATC"]

    key_one = cache.key(proteins)
    key_two = cache.key(proteins)

    assert key_one == key_two


def test_embedding_key_is_independent_of_protein_order(tmp_path: Path):
    cache = EmbeddingCache(tmp_path / "embeddings.sqlite3")

    key_one = cache.key(["MKTAYIAK", "GATCGATC"])
    key_two = cache.key(["GATCGATC", "MKTAYIAK"])

    assert key_one == key_two


def test_embedding_key_changes_when_protein_sequence_changes(
    tmp_path: Path,
):
    cache = EmbeddingCache(tmp_path / "embeddings.sqlite3")

    key_one = cache.key(["MKTAYIAK"])
    key_two = cache.key(["MKTAYIAQ"])

    assert key_one != key_two


def test_embedding_key_changes_when_protein_set_changes(
    tmp_path: Path,
):
    cache = EmbeddingCache(tmp_path / "embeddings.sqlite3")

    key_one = cache.key(["MKTAYIAK"])
    key_two = cache.key(["MKTAYIAK", "GATCGATC"])

    assert key_one != key_two


def test_embedding_key_changes_when_model_changes(tmp_path: Path):
    cache = EmbeddingCache(tmp_path / "embeddings.sqlite3")

    key_one = cache.key(
        ["MKTAYIAK"],
        model_name="esm2_t33_650M_UR50D",
    )
    key_two = cache.key(
        ["MKTAYIAK"],
        model_name="different-model",
    )

    assert key_one != key_two


def test_embedding_key_changes_when_representation_contract_changes(
    tmp_path: Path,
    monkeypatch,
):
    cache = EmbeddingCache(tmp_path / "embeddings.sqlite3")

    original_contract = providers.esm2_representation_contract

    def contract_with_original_layer():
        return original_contract()

    monkeypatch.setattr(
        providers,
        "esm2_representation_contract",
        contract_with_original_layer,
    )

    key_one = cache.key(["MKTAYIAK"])

    def contract_with_different_layer():
        contract = original_contract()
        contract["layer"] = contract["layer"] + 1
        return contract

    monkeypatch.setattr(
        providers,
        "esm2_representation_contract",
        contract_with_different_layer,
    )

    key_two = cache.key(["MKTAYIAK"])

    assert key_one != key_two


def test_embedding_cache_rejects_wrong_dimensions(tmp_path: Path):
    cache = EmbeddingCache(tmp_path / "embeddings.sqlite3")

    key = cache.key(["MKTAYIAK"])

    cache.put(
        key,
        np.arange(1280, dtype=np.float32),
        {"model": "test", "dimensions": 1280},
    )

    invalid_vector = np.asarray([1.0, 2.0], dtype=np.float32)

    with sqlite3.connect(cache.path) as conn:
        conn.execute(
            "UPDATE embeddings SET vector = ? WHERE key = ?",
            (
                invalid_vector.tobytes(),
                key,
            ),
        )
        conn.commit()

    assert cache.get(key) is None


def test_embedding_cache_rejects_non_finite_vector(tmp_path: Path):
    cache = EmbeddingCache(tmp_path / "embeddings.sqlite3")

    key = cache.key(["MKTAYIAK"])

    cache.put(
        key,
        np.arange(1280, dtype=np.float32),
        {"model": "test", "dimensions": 1280},
    )

    invalid_vector = np.full(1280, np.nan, dtype=np.float32)

    with sqlite3.connect(cache.path) as conn:
        conn.execute(
            "UPDATE embeddings SET vector = ? WHERE key = ?",
            (
                invalid_vector.tobytes(),
                key,
            ),
        )
        conn.commit()

    assert cache.get(key) is None


def test_embedding_cache_put_rejects_wrong_dimensions(tmp_path: Path):
    cache = EmbeddingCache(tmp_path / "embeddings.sqlite3")

    key = cache.key(["MKTAYIAK"])

    try:
        cache.put(
            key,
            np.arange(10, dtype=np.float32),
            {"model": "test", "dimensions": 10},
        )
    except ValueError as exc:
        assert "1280" in str(exc)
    else:
        raise AssertionError(
            "Expected ValueError for incorrect embedding dimensions"
        )


def test_embedding_cache_put_rejects_non_finite_values(tmp_path: Path):
    cache = EmbeddingCache(tmp_path / "embeddings.sqlite3")

    key = cache.key(["MKTAYIAK"])
    invalid_vector = np.full(1280, np.inf, dtype=np.float32)

    try:
        cache.put(
            key,
            invalid_vector,
            {"model": "test", "dimensions": 1280},
        )
    except ValueError as exc:
        assert "finite" in str(exc).lower()
    else:
        raise AssertionError(
            "Expected ValueError for non-finite embedding"
        )


def test_capability_report_is_fail_closed():
    result = capability_report()

    assert result["novel_isolate_pipeline_ready"] == (not result["blockers"])
    assert result["embedding_dimensions"] == 1280


def test_checkpoint_report_requires_matching_digests(
    tmp_path: Path,
    monkeypatch,
):
    checkpoint = tmp_path / "model.pt"
    checkpoint.write_bytes(b"verified-model")

    manifest = tmp_path / "manifest.json"
    manifest.write_text(
        json.dumps(
            {
                "files": [
                    {
                        "filename": checkpoint.name,
                        "sha256": hashlib.sha256(
                            checkpoint.read_bytes()
                        ).hexdigest(),
                    }
                ]
            }
        )
    )

    monkeypatch.setattr(
        providers,
        "ESM2_MANIFEST",
        manifest,
    )
    monkeypatch.setenv(
        "PHAGEX_ESM2_CHECKPOINT_DIR",
        str(tmp_path),
    )

    assert providers.esm2_checkpoint_report()["ready"] is True

    checkpoint.write_bytes(b"tampered")

    result = providers.esm2_checkpoint_report()

    assert result["ready"] is False
    assert "checksum mismatch" in result["reason"]