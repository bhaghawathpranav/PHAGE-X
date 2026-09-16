from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, Field, model_validator

from .limits import ASSEMBLY_FASTA_MAX_BYTES, DEMO_FASTA_MAX_BYTES


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
    fasta: Optional[str] = Field(default=None, max_length=DEMO_FASTA_MAX_BYTES)
    isolate_name: Optional[str] = Field(default=None, max_length=100)
    demo_fasta: bool = False
    cocktail_size: int = Field(default=3, ge=2, le=3)

    @model_validator(mode="after")
    def require_one_input(self):
        if bool(self.isolate_id) == bool(self.fasta):
            raise ValueError("Provide exactly one of isolate_id or fasta")
        if self.demo_fasta and not self.fasta:
            raise ValueError("demo_fasta is valid only with an explicit FASTA demonstration input")
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


class ResearchRankRequest(BaseModel):
    host_id: str = Field(min_length=1, max_length=100)
    limit: int = Field(default=20, ge=1, le=105)


class FeatureAttribution(BaseModel):
    feature: str
    contribution: float
    direction: str


class ResearchCandidate(BaseModel):
    phage_id: str
    compatibility: float
    decision: str
    safety_status: str
    rationale: List[str] = Field(default_factory=list)
    attributions: List[FeatureAttribution] = Field(default_factory=list)


class ResearchRankResponse(BaseModel):
    host_id: str
    split_role: str
    model_version: str
    feature_source: str
    candidates: List[ResearchCandidate]
    cocktail_status: str
    cocktail_blockers: List[str]
    disclaimer: str


class AssemblyInspectRequest(BaseModel):
    fasta: str = Field(min_length=100, max_length=ASSEMBLY_FASTA_MAX_BYTES)


class AssemblyInspectResponse(BaseModel):
    assembly_sha256: str
    contig_count: int
    total_length_bp: int
    n50_bp: int
    gc_fraction: float
    ambiguous_fraction: float
    qc_status: str
    warnings: List[str]
    pipeline_status: str
    completed_stages: List[str]
    blockers: List[str]
    sequence_persisted: bool


class LocusProteinResponse(BaseModel):
    locus: str
    protein_count: int
    total_residues: int
    longest_protein: int
    protein_names: List[str]
    protein_set_sha256: str
    database_sha256: str
    kaptive_version: str
    esm2_status: str
    raw_sequences_returned: bool
    disclaimer: str


class IsolateLocusRequest(BaseModel):
    fasta: str = Field(min_length=100, max_length=ASSEMBLY_FASTA_MAX_BYTES)


class IsolateLocusResponse(BaseModel):
    assembly_sha256: str
    locus: str
    confidence: str
    percent_identity: float
    percent_coverage: float
    protein_count: int
    total_residues: int
    protein_names: List[str]
    protein_set_sha256: str
    missing_genes: List[str]
    problems: str
    kaptive_version: str
    species_status: str
    species_reference_accession: str
    species_ani_percent: float
    species_alignment_fraction: float
    species_reference_sha256: str
    fastani_version: str
    pipeline_status: str
    raw_sequences_returned: bool
    sequence_persisted: bool
    disclaimer: str


class IsolateEmbeddingResponse(BaseModel):
    assembly_sha256: str
    locus: str
    species_status: str
    species_ani_percent: float
    species_alignment_fraction: float
    protein_count: int
    protein_set_sha256: str
    model: str
    dimensions: int
    embedding_cache_key: str
    embedding_sha256: str
    pipeline_status: str
    raw_embedding_returned: bool
    sequence_persisted: bool
    disclaimer: str


class NovelIsolateRankRequest(BaseModel):
    fasta: str = Field(min_length=100, max_length=ASSEMBLY_FASTA_MAX_BYTES)
    limit: int = Field(default=20, ge=1, le=105)


class NovelIsolateRankResponse(BaseModel):
    assembly_sha256: str
    locus: str
    species_status: str
    species_ani_percent: float
    model_version: str
    feature_source: str
    feature_sha256: str
    distribution_status: str
    nearest_reference_cosine: float
    candidates: List[ResearchCandidate]
    cocktail_status: str
    cocktail_members: List[str]
    cocktail_objective_score: Optional[float] = None
    cocktail_mean_compatibility: Optional[float] = None
    cocktail_family_diversity: Optional[float] = None
    cocktail_receptor_diversity: Optional[float] = None
    cocktail_redundancy: Optional[float] = None
    cocktail_blockers: List[str]
    disclaimer: str


class JobResponse(BaseModel):
    job_id: str
    status: str
    created_at: str
    updated_at: str
    result: Optional[Dict[str, object]] = None
    error: Optional[str] = None
    cancel_requested: bool
