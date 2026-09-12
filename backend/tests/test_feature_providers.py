from pathlib import Path

import numpy as np

from app.feature_providers import EmbeddingCache, capability_report


def test_embedding_cache_uses_sequence_digest_not_raw_sequence(tmp_path: Path):
    cache = EmbeddingCache(tmp_path / "embeddings.sqlite3")
    key = cache.key(["MKTAYIAK"])
    vector = np.arange(1280, dtype=np.float32)
    cache.put(key, vector, {"model": "test", "dimensions": 1280})
    observed = cache.get(key)
    assert np.array_equal(observed, vector)
    assert b"MKTAYIAK" not in cache.path.read_bytes()


def test_capability_report_is_fail_closed():
    result = capability_report()
    assert result["novel_isolate_pipeline_ready"] == (not result["blockers"])
    assert result["embedding_dimensions"] == 1280

