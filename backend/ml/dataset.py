from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, Tuple

import numpy as np
import pandas as pd
from sklearn.model_selection import GroupShuffleSplit


FEATURE_NAMES = (
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


@dataclass(frozen=True)
class PairDataset:
    X: np.ndarray
    y: np.ndarray
    hosts: np.ndarray
    phages: np.ndarray
    feature_names: Tuple[str, ...] = FEATURE_NAMES


def _sha256(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def validate_source_files(data_dir: Path, manifest_path: Path) -> Dict[str, str]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    observed = {}
    for record in manifest["files"]:
        path = data_dir / record["name"]
        if not path.exists():
            raise FileNotFoundError(f"Missing source file: {path}")
        if path.stat().st_size != record["bytes"]:
            raise ValueError(f"Unexpected byte size for {path.name}")
        md5 = hashlib.md5(path.read_bytes()).hexdigest()  # nosec B324: source-published checksum
        if md5 != record["md5"]:
            raise ValueError(f"Checksum mismatch for {path.name}")
        observed[path.name] = _sha256(path)
    return observed


def _features(host: np.ndarray, phage: np.ndarray, rbp_count: int) -> np.ndarray:
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


def load_pair_dataset(data_dir: Path) -> PairDataset:
    interactions = pd.read_csv(data_dir / "phage_host_interactions.csv", index_col=0)
    loci = pd.read_csv(data_dir / "esm2_embeddings_loci.csv", index_col="accession")
    rbps = pd.read_csv(data_dir / "esm2_embeddings_rbp.csv")
    embedding_columns = [str(index) for index in range(1280)]
    if list(loci.columns) != embedding_columns:
        raise ValueError("Locus embeddings must contain exactly 1,280 ordered ESM-2 dimensions")
    if list(rbps.columns[2:]) != embedding_columns:
        raise ValueError("RBP embeddings must contain exactly 1,280 ordered ESM-2 dimensions")

    rbp_counts = rbps.groupby("phage_ID").size().to_dict()
    phage_embeddings = rbps.groupby("phage_ID")[embedding_columns].mean()
    common_hosts = sorted(set(interactions.index) & set(loci.index))
    common_phages = sorted(set(interactions.columns) & set(phage_embeddings.index))
    if not common_hosts or not common_phages:
        raise ValueError("No overlapping interaction and embedding identifiers")

    features, labels, host_ids, phage_ids = [], [], [], []
    for host_id in common_hosts:
        host_vector = loci.loc[host_id].to_numpy(dtype=np.float32)
        for phage_id in common_phages:
            label = interactions.at[host_id, phage_id]
            if pd.isna(label):
                continue
            features.append(
                _features(
                    host_vector,
                    phage_embeddings.loc[phage_id].to_numpy(dtype=np.float32),
                    rbp_counts[phage_id],
                )
            )
            labels.append(int(label))
            host_ids.append(host_id)
            phage_ids.append(phage_id)
    result = PairDataset(
        X=np.vstack(features),
        y=np.asarray(labels, dtype=np.int8),
        hosts=np.asarray(host_ids),
        phages=np.asarray(phage_ids),
    )
    if set(np.unique(result.y)) != {0, 1}:
        raise ValueError("Interaction labels must contain both classes")
    return result


def grouped_three_way_split(
    dataset: PairDataset, random_state: int = 41
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    outer = GroupShuffleSplit(n_splits=1, test_size=0.15, random_state=random_state)
    train_val, test = next(outer.split(dataset.X, dataset.y, groups=dataset.hosts))
    inner = GroupShuffleSplit(n_splits=1, test_size=0.1765, random_state=random_state + 1)
    train_rel, validation_rel = next(
        inner.split(dataset.X[train_val], dataset.y[train_val], groups=dataset.hosts[train_val])
    )
    train, validation = train_val[train_rel], train_val[validation_rel]
    group_sets = [set(dataset.hosts[index]) for index in (train, validation, test)]
    if group_sets[0] & group_sets[1] or group_sets[0] & group_sets[2] or group_sets[1] & group_sets[2]:
        raise AssertionError("Host leakage detected across splits")
    return train, validation, test


def top_k_recall(y: np.ndarray, probabilities: np.ndarray, hosts: Iterable[str], k: int) -> float:
    frame = pd.DataFrame({"host": list(hosts), "label": y, "probability": probabilities})
    eligible = 0
    hits = 0
    for _, group in frame.groupby("host"):
        if not group["label"].any():
            continue
        eligible += 1
        hits += int(group.nlargest(k, "probability")["label"].any())
    return hits / eligible if eligible else 0.0

