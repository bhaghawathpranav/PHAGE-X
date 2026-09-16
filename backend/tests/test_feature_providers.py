from pathlib import Path
import hashlib
import json

import numpy as np

import app.feature_providers as providers
from app.feature_providers import EmbeddingCache, capability_report, esm2_representation_contract


def test_embedding_cache_uses_sequence_digest_not_raw_sequence(tmp_path: Path):
    cache = EmbeddingCache(tmp_path / "embeddings.sqlite3")
    key = cache.key(["MKTAYIAK"])
    vector = np.arange(1280, dtype=np.float32)
    cache.put(key, vector, {"model": "test", "dimensions": 1280})
    observed = cache.get(key)
    assert np.array_equal(observed, vector)
    assert b"MKTAYIAK" not in cache.path.read_bytes()


def test_embedding_cache_key_tracks_contract_and_is_protein_order_invariant():
    assert EmbeddingCache.key(["AAAA", "CCCC"]) == EmbeddingCache.key(["CCCC", "AAAA"])
    contract = esm2_representation_contract()
    assert contract["dimensions"] == 1280
    assert contract["layer"] == 33
    assert "protein_mean" in str(contract["pooling"])


def test_embedding_cache_rejects_malformed_vectors(tmp_path: Path):
    cache = EmbeddingCache(tmp_path / "embeddings.sqlite3")
    with np.testing.assert_raises_regex(ValueError, "shape"):
        cache.put("bad", np.zeros(12, dtype=np.float32), {})
    with np.testing.assert_raises_regex(ValueError, "non-finite"):
        cache.put("bad", np.full(1280, np.nan, dtype=np.float32), {})


def test_capability_report_is_fail_closed():
    result = capability_report()
    assert result["novel_isolate_pipeline_ready"] == (not result["blockers"])
    assert result["embedding_dimensions"] == 1280


def test_checkpoint_report_requires_matching_digests(tmp_path: Path, monkeypatch):
    checkpoint = tmp_path / "model.pt"
    checkpoint.write_bytes(b"verified-model")
    manifest = tmp_path / "manifest.json"
    manifest.write_text(
        json.dumps(
            {
                "files": [
                    {
                        "filename": checkpoint.name,
                        "sha256": hashlib.sha256(checkpoint.read_bytes()).hexdigest(),
                    }
                ]
            }
        )
    )
    monkeypatch.setattr(providers, "ESM2_MANIFEST", manifest)
    monkeypatch.setenv("PHAGEX_ESM2_CHECKPOINT_DIR", str(tmp_path))
    assert providers.esm2_checkpoint_report()["ready"] is True
    checkpoint.write_bytes(b"tampered")
    result = providers.esm2_checkpoint_report()
    assert result["ready"] is False
    assert "checksum mismatch" in result["reason"]
