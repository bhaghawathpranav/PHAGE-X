from typing import List, Literal, Optional

from pydantic import BaseModel, Field, model_validator


class IsolateSummary(BaseModel):
    id: str
    name: str
    organism: str
    sequence_type: str
    k_locus: str
    resistance: List[str]
    description: str


class SequenceQC(BaseModel):
    sequence_sha256: str
    length_bp: int
    gc_fraction: float
    ambiguous_fraction: float
    status: str
    warnings: List[str]


class AnalyzeRequest(BaseModel):
    isolate_id: Optional[str] = None
    fasta: Optional[str] = Field(default=None, max_length=5_000_000)
    isolate_name: Optional[str] = Field(default=None, max_length=100)
    cocktail_size: int = Field(default=3, ge=2, le=3)

    @model_validator(mode="after")
    def require_one_input(self):
        if bool(self.isolate_id) == bool(self.fasta):
            raise ValueError("Provide exactly one of isolate_id or fasta")
        return self


class Contribution(BaseModel):
    label: str
    value: float
    direction: str


class RankedPhage(BaseModel):
    id: str
    name: str
    family: str
    receptor: str
    compatibility: float
    confidence_band: str
    rationale: List[str]
    contributions: List[Contribution]
    evidence: str
    safety_status: str


class CocktailMember(BaseModel):
    phage_id: str
    name: str
    role: str
    compatibility: float


class CocktailCandidate(BaseModel):
    members: List[CocktailMember]
    compatibility: float
    diversity: float
    redundancy: float
    objective_score: float
    rationale: List[str]
    constraints_passed: List[str]


class AnalysisResponse(BaseModel):
    analysis_id: str
    isolate: IsolateSummary
    input_mode: str
    feature_source: str
    sequence_qc: Optional[SequenceQC] = None
    model: str
    ranked_phages: List[RankedPhage]
    cocktail: CocktailCandidate
    limitations: List[str]
    disclaimer: str


class LabObservationRequest(BaseModel):
    analysis_id: str = Field(min_length=8, max_length=100)
    phage_id: str = Field(min_length=1, max_length=100)
    assay_type: Literal["spot_test", "plaque_assay", "efficiency_of_plating", "liquid_culture"]
    outcome: Literal["susceptible", "intermediate", "resistant", "inconclusive"]
    measured_value: Optional[float] = None
    units: Optional[str] = Field(default=None, max_length=30)
    contains_patient_data: Literal[False] = False


class LabObservationResponse(BaseModel):
    observation_id: str
    created_at: str
    status: str
