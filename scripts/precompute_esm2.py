#!/usr/bin/env python3
"""Precompute a canonical K-locus ESM-2 vector into the sequence-free cache."""

import argparse
import json
from pathlib import Path

import numpy as np

from app.feature_providers import (
    ESM2_DIMENSIONS,
    ESM2Embedder,
    EmbeddingCache,
    KaptiveRunner,
    ReferenceLocusFeaturePipeline,
    esm2_representation_contract,
)
from app.config import get_settings


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--locus", default="KL107")
    parser.add_argument(
        "--cache",
        type=Path,
        default=None,
        help="Embedding cache path. Defaults to the shared runtime cache.",
    )
    args = parser.parse_args()

    settings = get_settings()
    cache_path = args.cache if args.cache is not None else Path(settings.embedding_cache)

    result = ReferenceLocusFeaturePipeline(
        KaptiveRunner(),
        ESM2Embedder(EmbeddingCache(cache_path)),
    ).build(args.locus)

    contract = esm2_representation_contract()

    if result.embedding.shape != (ESM2_DIMENSIONS,):
        raise RuntimeError(
            f"Unexpected ESM-2 embedding shape: {result.embedding.shape}; "
            f"expected {(ESM2_DIMENSIONS,)}"
        )

    if not np.isfinite(result.embedding).all():
        raise RuntimeError("Precomputed ESM-2 embedding contains non-finite values")

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
                "representation_contract": contract,
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()