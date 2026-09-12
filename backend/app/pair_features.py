from typing import Tuple

import numpy as np


FEATURE_NAMES: Tuple[str, ...] = (
    "cosine_similarity",
    "euclidean_distance",
    "absolute_difference_mean",
    "absolute_difference_std",
    "absolute_difference_max",
    "element_product_mean",
    "element_product_std",
    "element_product_max",
    "host_embedding_norm",
    "phage_embedding_norm",
    "rbp_count",
)


def pair_features(host: np.ndarray, phage: np.ndarray, rbp_count: int) -> np.ndarray:
    host_norm = float(np.linalg.norm(host))
    phage_norm = float(np.linalg.norm(phage))
    cosine = float(np.dot(host, phage) / (host_norm * phage_norm)) if host_norm and phage_norm else 0.0
    absolute = np.abs(host - phage)
    product = host * phage
    return np.array(
        [
            cosine,
            np.linalg.norm(host - phage),
            absolute.mean(),
            absolute.std(),
            absolute.max(),
            product.mean(),
            product.std(),
            product.max(),
            host_norm,
            phage_norm,
            float(rbp_count),
        ],
        dtype=np.float32,
    )

