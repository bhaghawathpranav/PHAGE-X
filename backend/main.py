"""
PHAGE-X — FastAPI backend / integration layer.

Owner: Bhaghawath Pranav S (backend API / integration).

This file wires the request/response contract (schemas.py) to the
downstream pipeline:

    genome processing -> feature pipeline -> ML prediction -> cocktail optimizer

The actual implementations of genome processing, ML prediction (ESM-2 +
XGBoost), and cocktail optimization are OWNED BY OTHER TEAMMATES and live
under backend/services/. That module does not exist yet in this repo, so
this file does NOT import from it and does NOT implement any of that logic.

Instead, the three pipeline stages are represented below as clearly marked
INTEGRATION PLACEHOLDERS. Each one raises NotImplementedError with a
descriptive message. The /predict route catches that and returns an honest
"pending_integration" response instead of fabricating a prediction.

When the data/ML teammates add backend/services/*, replace the placeholder
functions below with real imports, e.g.:

    from backend.services.genome_processing import process_genome
    from backend.services.ml_prediction import predict_phage_host
    from backend.services.optimizer import select_cocktail

and delete the placeholder function bodies.
"""

import logging

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from backend.schemas import (
    PredictionRequest,
    PredictionResponse,
    PhageRecommendation,
    CocktailRecommendation,
    HealthResponse,
)

logger = logging.getLogger("phage_x")

app = FastAPI(
    title="PHAGE-X Backend API",
    description="AI-guided phage-host prediction and cocktail recommendation API.",
    version="0.1.0",
)


# ---------------------------------------------------------------------------
# INTEGRATION PLACEHOLDERS
#
# These functions define the *interface* that the genome-processing and
# ML/optimizer teammates should implement in backend/services/. They contain
# NO biological or ML logic. Do not fill these in here — this is intentional
# so nobody on this file accidentally invents fake science.
# ---------------------------------------------------------------------------

def process_genome(genome_fasta: str):
    """
    PLACEHOLDER — owned by genome-processing teammate.

    Expected to parse the input FASTA, extract K-locus proteins and
    receptor-binding proteins, and return whatever structure the ML
    prediction step needs (e.g. processed sequences / feature inputs).
    """
    raise NotImplementedError(
        "process_genome() is not implemented yet. "
        "This is owned by the genome-processing teammate "
        "(backend/services/genome_processing.py)."
    )


def predict_phage_host(processed_genome):
    """
    PLACEHOLDER — owned by ML teammate.

    Expected to take the processed genome/features, compute or look up
    ESM-2 protein embeddings, run the XGBoost model against the phage bank,
    and return a ranked list of phage-host compatibility predictions.
    """
    raise NotImplementedError(
        "predict_phage_host() is not implemented yet. "
        "This is owned by the ML teammate "
        "(backend/services/ml_prediction.py)."
    )


def select_cocktail(predictions):
    """
    PLACEHOLDER — owned by optimizer teammate.

    Expected to take the ranked phage-host predictions and select a
    2-3 phage cocktail balancing high compatibility and low redundancy.
    """
    raise NotImplementedError(
        "select_cocktail() is not implemented yet. "
        "This is owned by the optimizer teammate "
        "(backend/services/optimizer.py)."
    )


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/health", response_model=HealthResponse)
def health():
    """Basic liveness check."""
    return HealthResponse(status="ok")


@app.post("/predict", response_model=PredictionResponse)
def predict(request: PredictionRequest):
    """
    Run the PHAGE-X pipeline for a given bacterial genome.

    Conceptual flow (once services/ is implemented by teammates):

        genome = process_genome(request.genome)
        predictions = predict_phage_host(genome)
        cocktail = select_cocktail(predictions)
        return PredictionResponse(...)

    Until those services exist, this route calls the placeholder functions,
    catches the expected NotImplementedError, and returns an honest
    "pending_integration" response rather than fabricated results.
    """
    try:
        processed_genome = process_genome(request.genome)
        predictions = predict_phage_host(processed_genome)
        cocktail = select_cocktail(predictions)

        recommendations = [
            PhageRecommendation(**p) if isinstance(p, dict) else p
            for p in predictions
        ]
        cocktail_recommendations = [
            CocktailRecommendation(**c) if isinstance(c, dict) else c
            for c in cocktail
        ]

        return PredictionResponse(
            status="success",
            bacterium=request.bacterium_id,
            recommendations=recommendations,
            cocktail=cocktail_recommendations,
            message=None,
        )

    except NotImplementedError as exc:
        # Expected during development: one or more pipeline stages
        # (genome processing / ML prediction / cocktail optimizer)
        # haven't been wired in yet.
        logger.info("Prediction pipeline not fully integrated: %s", exc)
        return PredictionResponse(
            status="pending_integration",
            bacterium=request.bacterium_id,
            recommendations=[],
            cocktail=[],
            message=str(exc),
        )

    except Exception as exc:  # basic error handling
        logger.exception("Unexpected error while processing /predict request")
        return JSONResponse(
            status_code=500,
            content=PredictionResponse(
                status="error",
                bacterium=request.bacterium_id,
                recommendations=[],
                cocktail=[],
                message=f"Internal error: {exc}",
            ).model_dump(),
        )