#!/usr/bin/env python3
"""Precompute a canonical K-locus ESM-2 vector into the sequence-free cache."""

import argparse
import json
from pathlib import Path

import numpy as np

from app.config import get_settings
from app.feature_providers import (
    ESM2_DIMENSIONS,
    EmbeddingCache,
    ESM2Embedder,
    KaptiveRunner,
    ReferenceLocusFeaturePipeline,
    esm2_representation_contract,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--locus", default="KL107")
    parser.add_argument("--cache", type=Path, default=None)
    args = parser.parse_args()
    cache_path = args.cache if args.cache is not None else get_settings().embedding_cache
    result = ReferenceLocusFeaturePipeline(
        KaptiveRunner(), ESM2Embedder(EmbeddingCache(cache_path))
    ).build(args.locus)
    if result.embedding.shape != (ESM2_DIMENSIONS,) or not np.isfinite(result.embedding).all():
        raise RuntimeError("Precomputed ESM-2 representation failed its runtime contract")
    print(
        json.dumps(
            {
                "locus": result.locus,
                "protein_count": result.protein_count,
                "dimensions": int(result.embedding.shape[0]),
                "finite": bool(np.isfinite(result.embedding).all()),
                "protein_set_sha256": result.protein_set_sha256,
                "embedding_cache_key": result.embedding_cache_key,
                "cache": str(cache_path.resolve()),
                "representation_contract": esm2_representation_contract(),
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
