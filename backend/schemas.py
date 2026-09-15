"""
PHAGE-X — Pydantic schemas.

These models define the contract between the frontend, the FastAPI routes
(main.py), and the downstream services (genome processing, ML prediction,
cocktail optimizer) that are owned by other teammates.

No biological or ML computation happens here — this file only defines
data shapes.
"""

from typing import List, Optional
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Request models
# ---------------------------------------------------------------------------

class PredictionRequest(BaseModel):
    """Request body for POST /predict."""

    genome: str = Field(
        ...,
        description="Bacterial genome in FASTA format (header + sequence).",
        min_length=1,
    )
    bacterium_id: Optional[str] = Field(
        default=None,
        description="Optional caller-supplied identifier/label for this genome, "
        "if the frontend already knows it (e.g. from a sample sheet). "
        "If not provided, an identifier may later be derived from the FASTA "
        "header by the genome processing service.",
    )


# ---------------------------------------------------------------------------
# Response sub-models
# ---------------------------------------------------------------------------

class PhageRecommendation(BaseModel):
    """A single ranked phage-host pair produced by the ML prediction step."""

    phage_id: str = Field(..., description="Identifier of the phage from the phage bank.")
    compatibility_score: float = Field(
        ..., description="Predicted phage-host compatibility score."
    )
    reason: Optional[str] = Field(
        default=None,
        description="Optional supporting evidence/explanation for this score "
        "(e.g. from an explanation service), if available.",
    )


class CocktailRecommendation(BaseModel):
    """A proposed phage cocktail (2-3 complementary phages) from the optimizer."""

    phage_ids: List[str] = Field(
        ..., description="Phage identifiers making up this cocktail (typically 2-3)."
    )
    reason: Optional[str] = Field(
        default=None,
        description="Optional rationale for why these phages were combined "
        "(e.g. high compatibility + low redundancy), if available.",
    )


# ---------------------------------------------------------------------------
# Response model
# ---------------------------------------------------------------------------

class PredictionResponse(BaseModel):
    """Response body for POST /predict."""

    status: str = Field(..., description="'success' or 'error'.")
    bacterium: Optional[str] = Field(
        default=None, description="Identifier of the input genome, if determined."
    )
    recommendations: List[PhageRecommendation] = Field(
        default_factory=list,
        description="Ranked list of phage-host recommendations.",
    )
    cocktail: List[CocktailRecommendation] = Field(
        default_factory=list,
        description="Proposed cocktail(s) of 2-3 complementary phages.",
    )
    message: Optional[str] = Field(
        default=None,
        description="Human-readable status/error message, if applicable.",
    )


class HealthResponse(BaseModel):
    """Response body for GET /health."""

    status: str = Field(default="ok", description="Service health status.")