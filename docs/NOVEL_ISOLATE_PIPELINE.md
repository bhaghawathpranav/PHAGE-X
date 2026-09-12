# Novel-isolate processing

## Implemented stages

1. Multi-contig FASTA parsing with a 15 MB limit
2. Deterministic assembly digest without persistence
3. Contig count, total length, N50, GC, ambiguity, and broad assembly-range checks
4. Runtime capability reporting for Kaptive, BLAST+, PyTorch, and `fair-esm`
5. Safe, argument-list-based Kaptive 3 runner using the `kpsc_k` database keyword
6. Lazy ESM-2 `esm2_t33_650M_UR50D` provider producing 1,280-dimensional mean-pooled protein embeddings
7. Digest-keyed SQLite embedding cache that stores vectors and provenance, never raw protein sequence
8. Fail-closed API/UI status when any required dependency or evidence stage is missing

## Current blocking boundary

Kaptive typing and ESM-2 embedding are implemented as separate providers, but the biological bridge between them remains deliberately open. A production pipeline must extract the K-locus coding sequences selected by Kaptive, translate them with the correct genetic code, validate gene completeness, and pass those proteins to ESM-2. PHAGE-X does not currently substitute whole-genome DNA or arbitrary translated frames for K-locus proteins.

The machine used for this milestone does not have Kaptive, BLAST+, PyTorch, or `fair-esm`. `GET /api/processing-capabilities` reports those exact blockers. `POST /api/inspect-assembly` still performs safe local QC and returns `pipeline_status: blocked`; it does not silently fall back to the demo hash representation.

## Installation boundary

Kaptive 3.2 is listed in `backend/requirements-sequence.txt`, while BLAST+ must be provided by the execution environment. PyTorch is platform-specific; install the appropriate CPU/CUDA build and `fair-esm==2.0.0` in a dedicated feature-extraction environment. The 650M ESM-2 weights are large and should be checksum-pinned and cached by deployment infrastructure rather than downloaded during an API request.

## Required validation

- Reference assemblies with accepted Kaptive results
- Exact comparison to PhageHostLearn preprocessing and pooling
- Unit fixtures for Kaptive TSV variants
- Protein extraction and translation validation
- CPU/GPU parity tolerance
- Cache concurrency and corruption tests
- Resource limits, job queue, cancellation, and timeouts
- Species confirmation before K-locus interpretation

