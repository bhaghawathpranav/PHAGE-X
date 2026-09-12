from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List

import joblib
import numpy as np

from ml.registry import verify_release_manifest

from .pair_features import FEATURE_NAMES, pair_features
from .schemas import ResearchCandidate, ResearchRankResponse


ARTIFACT_DIR = Path(__file__).parent.parent / "artifacts"
DISCLAIMER = "For laboratory validation only — research benchmark output, not a treatment recommendation."


class ResearchModel:
    def __init__(self, artifact_dir: Path = ARTIFACT_DIR):
        verify_release_manifest(artifact_dir, artifact_dir / "release_manifest.json")
        bundle = joblib.load(artifact_dir / "model.joblib")
        if tuple(bundle["feature_names"]) != FEATURE_NAMES:
            raise ValueError("Runtime feature schema does not match the trained model")
        catalog = np.load(artifact_dir / "runtime_catalog.npz", allow_pickle=False)
        self.model = bundle["model"]
        self.calibrator = bundle["calibrator"]
        self.host_ids = catalog["host_ids"]
        self.host_vectors = catalog["host_vectors"]
        self.phage_ids = catalog["phage_ids"]
        self.phage_vectors = catalog["phage_vectors"]
        self.rbp_counts = catalog["rbp_counts"]
        self.card: Dict[str, Any] = json.loads((artifact_dir / "model_card.json").read_text(encoding="utf-8"))

    def status(self) -> Dict[str, Any]:
        return {
            "artifact_version": self.card["artifact_version"],
            "release_approved": self.card["release_decision"]["approved"],
            "release_reason": self.card["release_decision"]["reason"],
            "test_metrics": self.card["metrics"],
            "benchmark_hosts": len(self.host_ids),
            "candidate_phages": len(self.phage_ids),
            "dataset_doi": self.card["dataset_doi"],
        }

    def rank(self, host_id: str, limit: int) -> ResearchRankResponse:
        matches = np.flatnonzero(self.host_ids == host_id)
        if not len(matches):
            raise KeyError(host_id)
        host = self.host_vectors[int(matches[0])]
        features = np.vstack(
            [pair_features(host, phage, int(count)) for phage, count in zip(self.phage_vectors, self.rbp_counts)]
        )
        raw = self.model.predict_proba(features)[:, 1]
        probabilities = self.calibrator.predict_proba(raw.reshape(-1, 1))[:, 1]
        order = np.argsort(probabilities)[::-1][:limit]
        candidates: List[ResearchCandidate] = []
        for index in order:
            probability = float(probabilities[index])
            decision = (
                "higher-priority-research-signal"
                if probability >= 0.65
                else "lower-priority-research-signal"
                if probability <= 0.35
                else "abstain-uncertain"
            )
            candidates.append(
                ResearchCandidate(
                    phage_id=str(self.phage_ids[index]),
                    compatibility=round(probability, 6),
                    decision=decision,
                    safety_status="blocked-unreviewed-catalog-metadata",
                )
            )
        return ResearchRankResponse(
            host_id=host_id,
            split_role="held-out-test-host",
            model_version=self.card["artifact_version"],
            feature_source="PhageHostLearn released ESM-2 embeddings",
            candidates=candidates,
            cocktail_status="blocked",
            cocktail_blockers=[
                "No independently reviewed genomic safety evidence",
                "No normalized receptor/family diversity metadata in runtime catalog",
                "No prospective laboratory confirmation for this ranking",
            ],
            disclaimer=DISCLAIMER,
        )


@lru_cache
def get_research_model() -> ResearchModel:
    return ResearchModel()

