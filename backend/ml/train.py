from __future__ import annotations

import argparse
import json
import platform
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
import sklearn
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.inspection import permutation_importance
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, brier_score_loss, roc_auc_score
from .dataset import (
    grouped_three_way_split,
    load_pair_dataset,
    top_k_recall,
    validate_source_files,
    write_runtime_catalog,
)
from .registry import write_release_manifest


def _new_model() -> HistGradientBoostingClassifier:
    return HistGradientBoostingClassifier(
        max_iter=350,
        max_leaf_nodes=15,
        learning_rate=0.04,
        l2_regularization=2.0,
        class_weight="balanced",
        random_state=41,
    )


def _fit_and_score(dataset, train, validation, test):
    model = _new_model()
    model.fit(dataset.X[train], dataset.y[train])
    validation_raw = model.predict_proba(dataset.X[validation])[:, 1]
    calibrator = LogisticRegression(random_state=41, solver="liblinear").fit(
        validation_raw.reshape(-1, 1), dataset.y[validation]
    )
    raw = model.predict_proba(dataset.X[test])[:, 1]
    probabilities = calibrator.predict_proba(raw.reshape(-1, 1))[:, 1]
    metrics = {
        "roc_auc": float(roc_auc_score(dataset.y[test], probabilities)),
        "average_precision": float(average_precision_score(dataset.y[test], probabilities)),
        "brier_score": float(brier_score_loss(dataset.y[test], probabilities)),
        "top_3_host_recall": float(top_k_recall(dataset.y[test], probabilities, dataset.hosts[test], 3)),
        "top_5_host_recall": float(top_k_recall(dataset.y[test], probabilities, dataset.hosts[test], 5)),
    }
    return model, calibrator, probabilities, metrics


def _host_bootstrap_intervals(labels, probabilities, hosts, repeats: int = 500):
    unique_hosts = np.unique(hosts)
    rng = np.random.default_rng(41)
    samples = {"roc_auc": [], "average_precision": [], "brier_score": []}
    for _ in range(repeats):
        selected = rng.choice(unique_hosts, size=len(unique_hosts), replace=True)
        indices = np.concatenate([np.flatnonzero(hosts == host) for host in selected])
        y = labels[indices]
        if len(np.unique(y)) < 2:
            continue
        samples["roc_auc"].append(roc_auc_score(y, probabilities[indices]))
        samples["average_precision"].append(average_precision_score(y, probabilities[indices]))
        samples["brier_score"].append(brier_score_loss(y, probabilities[indices]))
    return {
        name: {"lower_95": float(np.percentile(values, 2.5)), "upper_95": float(np.percentile(values, 97.5))}
        for name, values in samples.items()
    }


def _calibration_report(labels, probabilities):
    bins = np.linspace(0, 1, 11)
    rows = []
    weighted_error = 0.0
    for lower, upper in zip(bins[:-1], bins[1:]):
        mask = (probabilities >= lower) & (probabilities < upper if upper < 1 else probabilities <= upper)
        if not mask.any():
            continue
        predicted = float(probabilities[mask].mean())
        observed = float(labels[mask].mean())
        weighted_error += int(mask.sum()) * abs(predicted - observed)
        rows.append({"lower": float(lower), "upper": float(upper), "count": int(mask.sum()), "predicted": predicted, "observed": observed})
    return {"expected_calibration_error": weighted_error / len(labels), "bins": rows}


def main(data_dir: Path, manifest: Path, output_dir: Path, repeats: int = 5) -> None:
    source_hashes = validate_source_files(data_dir, manifest)
    dataset = load_pair_dataset(data_dir)
    train, validation, test = grouped_three_way_split(dataset)
    model, calibrator, probabilities, metrics = _fit_and_score(dataset, train, validation, test)
    repeated = []
    for offset in range(repeats):
        split = grouped_three_way_split(dataset, random_state=100 + offset)
        repeated.append(_fit_and_score(dataset, *split)[3])
    repeated_summary = {
        metric: {
            "mean": float(np.mean([item[metric] for item in repeated])),
            "std": float(np.std([item[metric] for item in repeated])),
            "min": float(np.min([item[metric] for item in repeated])),
            "max": float(np.max([item[metric] for item in repeated])),
        }
        for metric in metrics
    }
    uncertainty = np.minimum(probabilities, 1 - probabilities)
    abstain = uncertainty > 0.35
    importance = permutation_importance(
        model,
        dataset.X[validation],
        dataset.y[validation],
        scoring="average_precision",
        n_repeats=8,
        random_state=41,
    )
    feature_importance = sorted(
        (
            {"feature": name, "mean": float(mean), "std": float(std)}
            for name, mean, std in zip(dataset.feature_names, importance.importances_mean, importance.importances_std)
        ),
        key=lambda item: item["mean"],
        reverse=True,
    )
    report = {
        "artifact_version": "phagex-hgb-0.1.0",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "research_only": True,
        "dataset_doi": "10.5281/zenodo.11061100",
        "source_sha256": source_hashes,
        "feature_names": list(dataset.feature_names),
        "split_policy": "host-disjoint 70/15/15 grouped split, seed 41",
        "counts": {
            "pairs": len(dataset.y),
            "positives": int(dataset.y.sum()),
            "hosts": int(len(np.unique(dataset.hosts))),
            "phages": int(len(np.unique(dataset.phages))),
            "train_pairs": len(train),
            "validation_pairs": len(validation),
            "test_pairs": len(test),
        },
        "runtime_catalog": {
            "host_split": "fixed seed-41 test hosts only",
            "host_ids": sorted(set(dataset.hosts[test])),
            "phage_count": int(len(np.unique(dataset.phages))),
        },
        "metrics": metrics,
        "host_bootstrap_95_ci": _host_bootstrap_intervals(dataset.y[test], probabilities, dataset.hosts[test]),
        "calibration": _calibration_report(dataset.y[test], probabilities),
        "repeated_host_holdout": {
            "repeats": repeats,
            "seeds": list(range(100, 100 + repeats)),
            "summary": repeated_summary,
        },
        "release_decision": {
            "approved": False,
            "reason": "External validation, genomic safety evidence, and independent review are not complete."
        },
        "model": "sklearn.HistGradientBoostingClassifier",
        "feature_importance": feature_importance,
        "abstention": {
            "rule": "abstain when calibrated probability is between 0.35 and 0.65",
            "test_fraction": float(abstain.mean()),
            "decided_pairs": int((~abstain).sum()),
        },
        "error_analysis": {
            "false_positive_count_at_0_65": int(((probabilities >= 0.65) & (dataset.y[test] == 0)).sum()),
            "false_negative_count_at_0_35": int(((probabilities <= 0.35) & (dataset.y[test] == 1)).sum()),
            "note": "Study-negative labels may represent untested or unknown interactions, not confirmed resistance.",
        },
        "runtime": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "scikit_learn": sklearn.__version__,
        },
        "limitations": [
            "Unobserved pairs are study labels and may include unknown rather than confirmed-negative interactions.",
            "Metrics from a single deterministic split are insufficient for scientific release.",
            "The compact pair features do not reproduce the complete published multi-instance architecture.",
            "No clinical or laboratory-use claim is supported by this artifact."
        ],
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    model_path = output_dir / "model.joblib"
    model_card_path = output_dir / "model_card.json"
    catalog_path = output_dir / "runtime_catalog.npz"
    joblib.dump({"model": model, "calibrator": calibrator, "feature_names": dataset.feature_names}, model_path)
    model_card_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    write_runtime_catalog(data_dir, dataset.hosts[test], catalog_path)
    write_release_manifest(model_path, model_card_path, output_dir / "release_manifest.json", catalog_path)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--repeats", type=int, default=5)
    args = parser.parse_args()
    main(args.data_dir, args.manifest, args.output_dir, repeats=args.repeats)
