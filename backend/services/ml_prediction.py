"""
PHAGE-X — ML prediction service.

Owner: Bhaghawath Pranav S (backend API / ML integration).

STATUS: architecture/interface only. There is currently no trained XGBoost
model, no precomputed ESM-2 embeddings, and no ML dataset in this repo.
Nothing in this file fabricates scores, phage IDs, or biological features.

This module defines:
  1. The *input contract* this service expects from the genome/feature
     pipeline (backend/services/genome.py, owned by a teammate — not yet
     producing this structure).
  2. The *output contract* this service must return to main.py's
     predict() route (compatible with schemas.PhageRecommendation).
  3. A model-loading abstraction (`XGBoostModelLoader`) that will load a
     real XGBoost artifact once one exists, and fails loudly and clearly
     if it doesn't — rather than silently returning placeholder numbers.
  4. `predict_phage_host()`, the function main.py already expects to call.
     It currently always raises `ModelNotAvailableError` (a subclass of
     `NotImplementedError`), because there is no model to run yet. This is
     intentional, not a bug — see explanation below.

Nothing here should be treated as final. Field names inside
`ProcessedGenomeInput` / `PhageCandidateFeatures` are best-effort scaffolding
based on the PPT architecture (K-locus proteins, RBPs, ESM-2 embeddings) and
are expected to change once the genome/feature-pipeline teammate defines the
real output of `process_genome()`.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger("phage_x.ml_prediction")


# ---------------------------------------------------------------------------
# Input contract
#
# This describes what `processed_genome` (the output of the genome/feature
# pipeline) is expected to contain. The exact shape of `k_locus_features`,
# `rbp_features`, and `esm2_embedding` is intentionally left generic
# (`Any`) — we do NOT know the real embedding dimensionality, feature
# ordering, or representation yet, since no dataset/model artifact exists.
# Do not assume a fixed vector length or ordering anywhere downstream.
# ---------------------------------------------------------------------------

@dataclass
class PhageCandidateFeatures:
    """
    Feature bundle for a single candidate phage from the phage bank,
    as it would need to exist for scoring against the host genome.

    phage_id:
        Real identifier from the phage bank. Never fabricated here.
    rbp_features:
        Receptor-binding protein features for this phage. Shape/type TBD —
        depends on how the genome/feature-pipeline teammate extracts RBPs.
    esm2_embedding:
        Precomputed ESM-2 embedding for this phage's relevant protein(s).
        Shape/type TBD — depends on the ESM-2 pipeline that hasn't been
        run yet. Do not assume a fixed dimensionality.
    """

    phage_id: str
    rbp_features: Any = None
    esm2_embedding: Any = None


@dataclass
class ProcessedGenomeInput:
    """
    Expected output of genome/services process_genome(), and the input to
    predict_phage_host() below.

    bacterium_id:
        Identifier for the host genome, if known.
    k_locus_features:
        K-locus protein features extracted from the bacterial genome.
        Shape/type TBD — owned by the genome/feature-pipeline teammate.
    candidate_phages:
        The set of phages (from the phage bank) to be scored against this
        host, each with their own feature bundle.
    """

    bacterium_id: Optional[str] = None
    k_locus_features: Any = None
    candidate_phages: List[PhageCandidateFeatures] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Output contract
#
# main.py wraps whatever predict_phage_host() returns into
# schemas.PhageRecommendation. To keep this service decoupled from FastAPI/
# Pydantic, we return plain dicts with exactly the fields
# PhageRecommendation expects: phage_id, compatibility_score, reason.
# ---------------------------------------------------------------------------

PhageHostPrediction = Dict[str, Any]  # {"phage_id": str, "compatibility_score": float, "reason": Optional[str]}


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------

class ModelNotAvailableError(NotImplementedError):
    """
    Raised when real model inference cannot be performed because a required
    artifact (trained XGBoost model, embeddings, etc.) is missing.

    Deliberately subclasses NotImplementedError: main.py's /predict route
    already catches NotImplementedError from the pipeline stages and
    returns an honest "pending_integration" response instead of a fake
    success. Subclassing lets this plug into that existing behavior without
    touching main.py.
    """


class InvalidProcessedGenomeError(ValueError):
    """Raised when `processed_genome` doesn't structurally match the input contract."""


# ---------------------------------------------------------------------------
# Model-loading abstraction
#
# No model artifact exists yet. This loader's job, for now, is to fail
# clearly and explain what's missing — not to produce a placeholder model.
# `xgboost` is imported lazily inside `load()` so this module doesn't force
# an ML dependency onto the rest of the backend before it's actually needed.
# ---------------------------------------------------------------------------

DEFAULT_MODEL_PATH = os.environ.get(
    "PHAGE_X_XGBOOST_MODEL_PATH",
    os.path.join(os.path.dirname(__file__), "models", "phage_host_xgboost.json"),
)


class XGBoostModelLoader:
    """
    Loads the trained XGBoost phage-host compatibility model from disk.

    Usage (once a real model artifact exists):
        loader = XGBoostModelLoader(model_path="path/to/model.json")
        model = loader.load()   # cached after first successful load

    Until then, `load()` raises ModelNotAvailableError with a clear
    explanation, rather than returning a stub object.
    """

    def __init__(self, model_path: str = DEFAULT_MODEL_PATH):
        self.model_path = model_path
        self._model: Optional[Any] = None

    def load(self) -> Any:
        if self._model is not None:
            return self._model

        if not os.path.isfile(self.model_path):
            raise ModelNotAvailableError(
                "No trained XGBoost model artifact found at "
                f"'{self.model_path}'. Real predictions cannot be made "
                "until: (1) a labeled phage-host dataset exists, "
                "(2) ESM-2 embeddings are precomputed for phages/host "
                "proteins, and (3) an XGBoost model is trained on those "
                "features and exported to this path."
            )

        try:
            import xgboost as xgb  # lazy import: not a dependency until a model exists
        except ImportError as exc:
            raise ModelNotAvailableError(
                "A model artifact was found at "
                f"'{self.model_path}' but the 'xgboost' package is not "
                "installed. Add it to requirements.txt once real training "
                "is ready."
            ) from exc

        model = xgb.Booster()
        model.load_model(self.model_path)
        self._model = model
        logger.info("Loaded XGBoost model from %s", self.model_path)
        return self._model


_default_loader: Optional[XGBoostModelLoader] = None


def get_model_loader() -> XGBoostModelLoader:
    """Returns a process-wide singleton XGBoostModelLoader."""
    global _default_loader
    if _default_loader is None:
        _default_loader = XGBoostModelLoader()
    return _default_loader


# ---------------------------------------------------------------------------
# Structural validation
#
# This checks *shape*, not biology: e.g. that candidate phages were
# provided at all. It does not validate K-locus/RBP correctness, since that
# is genome-processing's responsibility, not this service's.
# ---------------------------------------------------------------------------

def _validate_processed_genome(processed_genome: ProcessedGenomeInput) -> None:
    if not isinstance(processed_genome, ProcessedGenomeInput):
        raise InvalidProcessedGenomeError(
            "predict_phage_host() expects a ProcessedGenomeInput instance. "
            f"Got {type(processed_genome).__name__}."
        )
    if not processed_genome.candidate_phages:
        raise InvalidProcessedGenomeError(
            "processed_genome.candidate_phages is empty — no phages to score."
        )


# ---------------------------------------------------------------------------
# Public entry point — this is what main.py's placeholder is meant to call.
# ---------------------------------------------------------------------------

def predict_phage_host(processed_genome: ProcessedGenomeInput) -> List[PhageHostPrediction]:
    """
    Score each candidate phage against the host genome for compatibility.

    Input contract:
        processed_genome: ProcessedGenomeInput
            See the dataclass docstring above. This is expected to come
            from the genome/feature-pipeline teammate's process_genome().

    Output contract:
        List[dict], each shaped like:
            {
                "phage_id": str,
                "compatibility_score": float,
                "reason": Optional[str],
            }
        This is compatible with schemas.PhageRecommendation and with what
        rank_phages() / select_cocktail() (owned by the optimizer teammate)
        are expected to consume next.

    Current behavior:
        Always raises ModelNotAvailableError. There is no trained model,
        no embeddings, and no dataset yet, so there is nothing valid to
        return. This is intentional — see module docstring.

    Once real artifacts exist, replace the body below (after validation
    and model loading) with actual inference:
        1. Build the real feature matrix from
           processed_genome.k_locus_features + each candidate's
           rbp_features / esm2_embedding, in whatever format the trained
           model expects (TBD — depends on how it was trained).
        2. Run `model.predict(...)` to get a compatibility score per
           candidate phage.
        3. Optionally call explain_candidate() (owned by the explanation
           teammate) to populate `reason`.
        4. Return the list of dicts described above.
    """
    _validate_processed_genome(processed_genome)

    loader = get_model_loader()
    model = loader.load()  # raises ModelNotAvailableError today — expected.

    # --- Real inference goes here once model/embeddings/dataset exist. ---
    # This code is intentionally NOT written yet — writing it now would
    # mean guessing at feature ordering / embedding shape that isn't
    # defined, which is exactly what we were told not to do.
    #
    # predictions: List[PhageHostPrediction] = []
    # for candidate in processed_genome.candidate_phages:
    #     feature_vector = _build_feature_vector(processed_genome, candidate)  # TBD
    #     score = model.predict(feature_vector)  # TBD: real inference call
    #     predictions.append({
    #         "phage_id": candidate.phage_id,
    #         "compatibility_score": float(score),
    #         "reason": None,  # optionally filled by explain_candidate()
    #     })
    # return predictions

    raise ModelNotAvailableError(  # pragma: no cover - unreachable while loader.load() raises first
        "Model loaded but inference logic is not implemented yet — "
        "pending finalized feature format."
    )