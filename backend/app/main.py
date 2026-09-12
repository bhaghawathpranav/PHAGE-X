import logging
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .config import get_settings
from .assembly import parse_assembly_fasta
from .data import load_demo_data
from .feedback import LabObservationStore
from .feature_providers import capability_report
from .inference import analyze, isolate_from_fasta
from .observability import RequestContextMiddleware
from .research_model import get_research_model
from .schemas import (
    AnalysisResponse,
    AnalyzeRequest,
    AssemblyInspectRequest,
    AssemblyInspectResponse,
    IsolateSummary,
    LabObservationRequest,
    LabObservationResponse,
    ResearchRankRequest,
    ResearchRankResponse,
)


settings = get_settings()
logging.basicConfig(level=settings.log_level)
app = FastAPI(
    title="PHAGE-X API",
    version=settings.app_version,
    description="Offline research prototype for explainable phage candidate prioritization.",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.allowed_origins),
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
app.add_middleware(RequestContextMiddleware)


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "service": "phagex-api",
        "version": settings.app_version,
        "environment": settings.environment,
    }


@app.get("/api/ready")
def readiness():
    data = load_demo_data()
    if not data.get("isolates") or not data.get("phages"):
        raise HTTPException(status_code=503, detail="Demo catalog is unavailable")
    return {
        "status": "ready",
        "isolates": len(data["isolates"]),
        "phages": len(data["phages"]),
    }


@app.get("/api/isolates", response_model=list[IsolateSummary])
def list_isolates():
    data = load_demo_data()
    return [{key: item[key] for key in IsolateSummary.model_fields} for item in data["isolates"]]


@app.post("/api/analyze", response_model=AnalysisResponse)
def run_analysis(request: AnalyzeRequest):
    data = load_demo_data()
    if request.isolate_id:
        isolate = next((item for item in data["isolates"] if item["id"] == request.isolate_id), None)
        if isolate is None:
            raise HTTPException(status_code=404, detail="Demo isolate not found")
        input_mode = "preloaded"
    else:
        try:
            isolate = isolate_from_fasta(request.fasta or "", request.isolate_name)
        except ValueError as error:
            raise HTTPException(status_code=422, detail=str(error)) from error
        input_mode = "uploaded-fasta-demo"
    return analyze(isolate, data["phages"], request.cocktail_size, input_mode)


@app.post("/api/lab-observations", response_model=LabObservationResponse, status_code=201)
def record_lab_observation(request: LabObservationRequest):
    """Record a non-patient research assay result; never changes prediction claims automatically."""
    return LabObservationStore(Path(settings.feedback_db)).add(request)


@app.get("/api/research-model")
def research_model_status():
    return get_research_model().status()


@app.get("/api/research-isolates", response_model=list[str])
def research_isolates():
    return [str(item) for item in get_research_model().host_ids]


@app.post("/api/research-rank", response_model=ResearchRankResponse)
def research_rank(request: ResearchRankRequest):
    try:
        return get_research_model().rank(request.host_id, request.limit)
    except KeyError as error:
        raise HTTPException(status_code=404, detail="Held-out research isolate not found") from error


@app.get("/api/processing-capabilities")
def processing_capabilities():
    return capability_report()


@app.post("/api/inspect-assembly", response_model=AssemblyInspectResponse)
def inspect_assembly(request: AssemblyInspectRequest):
    try:
        _, qc = parse_assembly_fasta(request.fasta)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    capabilities = capability_report()
    blockers = list(capabilities["blockers"])
    if qc.status != "pass":
        blockers.insert(0, "assembly_qc_review_required")
    return AssemblyInspectResponse(
        assembly_sha256=qc.assembly_sha256,
        contig_count=qc.contig_count,
        total_length_bp=qc.total_length_bp,
        n50_bp=qc.n50_bp,
        gc_fraction=qc.gc_fraction,
        ambiguous_fraction=qc.ambiguous_fraction,
        qc_status=qc.status,
        warnings=qc.warnings,
        pipeline_status="blocked" if blockers else "ready-for-local-feature-extraction",
        completed_stages=["fasta-parse", "assembly-qc", "digest-provenance"],
        blockers=blockers,
        sequence_persisted=False,
    )
