import hashlib
import logging
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .config import get_settings
from .assembly import parse_assembly_fasta
from .data import load_demo_data
from .feedback import LabObservationStore
from .feature_providers import (
    ESM2_MODEL,
    ESM2Embedder,
    EmbeddingCache,
    IsolateLocusFeaturePipeline,
    KaptiveRunner,
    capability_report,
)
from .inference import analyze, isolate_from_fasta
from .jobs import BoundedJobManager, serialize_job
from .observability import RequestContextMiddleware
from .security import ProductionSecurityMiddleware
from .phage_catalog import validate_phage_catalog
from .phage_screening import evidence_status, load_reviewed_metadata, registry_status
from .research_model import get_research_model
from .real_cocktail import optimize_reviewed_cocktail
from .species import FastANIRunner
from .schemas import (
    AnalysisResponse,
    AnalyzeRequest,
    AssemblyInspectRequest,
    AssemblyInspectResponse,
    IsolateSummary,
    IsolateLocusRequest,
    IsolateLocusResponse,
    IsolateEmbeddingResponse,
    LabObservationRequest,
    LabObservationResponse,
    JobResponse,
    LocusProteinResponse,
    NovelIsolateRankRequest,
    NovelIsolateRankResponse,
    ResearchRankRequest,
    ResearchRankResponse,
)


settings = get_settings()
novel_rank_jobs = BoundedJobManager(max_workers=1, max_queued=2, retention_minutes=60)
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
app.add_middleware(RequestContextMiddleware, audit_db=settings.audit_db)
app.add_middleware(
    ProductionSecurityMiddleware,
    production=settings.is_production,
    api_key=settings.api_key,
    requests_per_minute=settings.rate_limit_per_minute,
)


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
    try:
        validate_phage_catalog()
    except RuntimeError as error:
        raise HTTPException(status_code=503, detail="Real phage catalog failed integrity validation") from error
    return {
        "status": "ready",
        "isolates": len(data["isolates"]),
        "phages": len(data["phages"]),
    }


@app.get("/api/operations")
def operations():
    return {
        "feature_jobs": novel_rank_jobs.stats(),
        "worker_limit": 1,
        "queue_limit": 2,
        "retention_minutes": 60,
        "durability": "in-process-research-runtime",
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


@app.get("/api/phage-catalog")
def phage_catalog_status():
    return validate_phage_catalog()


@app.get("/api/phage-evidence")
def phage_evidence_registry():
    return registry_status()


@app.get("/api/phage-evidence/{phage_id}")
def phage_evidence(phage_id: str):
    try:
        return evidence_status(phage_id)
    except KeyError as error:
        raise HTTPException(status_code=404, detail="Phage not found in verified catalog") from error


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


@app.get("/api/reference-locus/{locus}", response_model=LocusProteinResponse)
def reference_locus_proteins(locus: str):
    try:
        proteins = KaptiveRunner().extract_reference_proteins(locus.upper())
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except RuntimeError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    capabilities = capability_report()
    return LocusProteinResponse(
        locus=proteins.locus,
        protein_count=len(proteins.sequences),
        total_residues=sum(map(len, proteins.sequences)),
        longest_protein=max(map(len, proteins.sequences)),
        protein_names=proteins.names,
        protein_set_sha256=proteins.protein_set_sha256,
        database_sha256=proteins.database_sha256,
        kaptive_version=proteins.kaptive_version,
        esm2_status="ready" if capabilities["tools"]["torch"] and capabilities["tools"]["esm"] else "blocked-missing-local-runtime",
        raw_sequences_returned=False,
        disclaimer="Reference features for research use only; not evidence of isolate identity or phage susceptibility.",
    )


@app.post("/api/extract-isolate-locus", response_model=IsolateLocusResponse)
def extract_isolate_locus(request: IsolateLocusRequest):
    try:
        _, qc = parse_assembly_fasta(request.fasta)
        if qc.status != "pass":
            raise ValueError("Assembly QC requires review before K-locus extraction")
        species = FastANIRunner().confirm_klebsiella_pneumoniae(request.fasta)
        proteins = KaptiveRunner().type_and_extract_assembly(request.fasta)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    except RuntimeError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    return IsolateLocusResponse(
        assembly_sha256=qc.assembly_sha256,
        locus=proteins.locus,
        confidence=proteins.confidence,
        percent_identity=proteins.percent_identity,
        percent_coverage=proteins.percent_coverage,
        protein_count=len(proteins.sequences),
        total_residues=sum(map(len, proteins.sequences)),
        protein_names=proteins.names,
        protein_set_sha256=proteins.protein_set_sha256,
        missing_genes=proteins.missing_genes,
        problems=proteins.problems,
        kaptive_version=proteins.kaptive_version,
        species_status=species.status,
        species_reference_accession=species.reference_accession,
        species_ani_percent=species.ani_percent,
        species_alignment_fraction=species.alignment_fraction,
        species_reference_sha256=species.reference_sha256,
        fastani_version=species.fastani_version,
        pipeline_status="blocked-pending-esm2",
        raw_sequences_returned=False,
        sequence_persisted=False,
        disclaimer="Isolate-derived research features for laboratory validation only; not a susceptibility or treatment result.",
    )


@app.post("/api/embed-isolate-locus", response_model=IsolateEmbeddingResponse)
def embed_isolate_locus(request: IsolateLocusRequest):
    try:
        _, qc = parse_assembly_fasta(request.fasta)
        if qc.status != "pass":
            raise ValueError("Assembly QC requires review before feature extraction")
        species = FastANIRunner().confirm_klebsiella_pneumoniae(request.fasta)
        result = IsolateLocusFeaturePipeline(
            KaptiveRunner(), ESM2Embedder(EmbeddingCache(Path(settings.embedding_cache)))
        ).build(request.fasta)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    except RuntimeError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    return IsolateEmbeddingResponse(
        assembly_sha256=qc.assembly_sha256,
        locus=result.locus,
        species_status=species.status,
        species_ani_percent=species.ani_percent,
        species_alignment_fraction=species.alignment_fraction,
        protein_count=result.protein_count,
        protein_set_sha256=result.protein_set_sha256,
        model=ESM2_MODEL,
        dimensions=int(result.embedding.shape[0]),
        embedding_cache_key=result.embedding_cache_key,
        embedding_sha256=hashlib.sha256(result.embedding.tobytes()).hexdigest(),
        pipeline_status="feature-vector-ready-for-research-ranking",
        raw_embedding_returned=False,
        sequence_persisted=False,
        disclaimer="ESM-2 research feature for laboratory validation only; not a susceptibility or treatment result.",
    )


@app.post("/api/rank-novel-isolate", response_model=NovelIsolateRankResponse)
def rank_novel_isolate(request: NovelIsolateRankRequest):
    try:
        _, qc = parse_assembly_fasta(request.fasta)
        if qc.status != "pass":
            raise ValueError("Assembly QC requires review before real-catalog ranking")
        species = FastANIRunner().confirm_klebsiella_pneumoniae(request.fasta)
        features = IsolateLocusFeaturePipeline(
            KaptiveRunner(), ESM2Embedder(EmbeddingCache(Path(settings.embedding_cache)))
        ).build(request.fasta)
        model = get_research_model()
        distribution = model.distribution_check(features.embedding)
        candidates = model.rank_vector(features.embedding, request.limit)
        cocktail = optimize_reviewed_cocktail(candidates, load_reviewed_metadata(), 3)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    except RuntimeError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    return NovelIsolateRankResponse(
        assembly_sha256=qc.assembly_sha256,
        locus=features.locus,
        species_status=species.status,
        species_ani_percent=species.ani_percent,
        model_version=model.card["artifact_version"],
        feature_source="isolate K-locus ESM-2 + released PhageHostLearn mean-RBP ESM-2",
        feature_sha256=hashlib.sha256(features.embedding.tobytes()).hexdigest(),
        distribution_status=distribution["status"],
        nearest_reference_cosine=distribution["nearest_reference_cosine"],
        candidates=candidates,
        cocktail_status=cocktail.status,
        cocktail_blockers=cocktail.blockers + ["Novel-isolate predictions require laboratory confirmation"],
        disclaimer="For laboratory validation only — novel-isolate research ranking, not treatment selection.",
    )


@app.post("/api/jobs/novel-rank", response_model=JobResponse, status_code=202)
def submit_novel_rank_job(request: NovelIsolateRankRequest):
    try:
        record = novel_rank_jobs.submit(lambda: rank_novel_isolate(request).model_dump())
    except RuntimeError as error:
        raise HTTPException(status_code=429, detail=str(error)) from error
    return serialize_job(record)


@app.get("/api/jobs/{job_id}", response_model=JobResponse)
def get_novel_rank_job(job_id: str):
    try:
        return serialize_job(novel_rank_jobs.get(job_id))
    except KeyError as error:
        raise HTTPException(status_code=404, detail="Job not found or expired") from error


@app.post("/api/jobs/{job_id}/cancel", response_model=JobResponse)
def cancel_novel_rank_job(job_id: str):
    try:
        return serialize_job(novel_rank_jobs.cancel(job_id))
    except KeyError as error:
        raise HTTPException(status_code=404, detail="Job not found or expired") from error
