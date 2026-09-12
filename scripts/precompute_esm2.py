#!/usr/bin/env python3
"""Precompute a canonical K-locus ESM-2 vector into the sequence-free cache."""

import argparse
import json
from pathlib import Path

import numpy as np

from app.feature_providers import EmbeddingCache, ESM2Embedder, KaptiveRunner, ReferenceLocusFeaturePipeline


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--locus", default="KL107")
    parser.add_argument("--cache", type=Path, default=Path("work/embeddings/esm2.sqlite3"))
    args = parser.parse_args()
    result = ReferenceLocusFeaturePipeline(
        KaptiveRunner(), ESM2Embedder(EmbeddingCache(args.cache))
    ).build(args.locus)
    print(
        json.dumps(
            {
                "locus": result.locus,
                "protein_count": result.protein_count,
                "dimensions": int(result.embedding.shape[0]),
                "finite": bool(np.isfinite(result.embedding).all()),
                "protein_set_sha256": result.protein_set_sha256,
                "embedding_cache_key": result.embedding_cache_key,
                "cache": str(args.cache),
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
