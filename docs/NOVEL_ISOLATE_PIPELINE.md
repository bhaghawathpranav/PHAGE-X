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
9. Kaptive 3.2 reference-locus protein extraction with protein-set and database SHA-256 provenance
10. A validated reference-locus-to-ESM-2 orchestration contract that rejects malformed vectors
11. Isolate-specific Kaptive assembly typing and translated protein extraction
12. Strict rejection of untypeable, missing, partial, truncated, duplicate, or low-coverage locus genes
13. Ephemeral sequence handling with metadata-only API responses

## Current blocking boundary

The canonical reference-locus bridge is implemented: for a strict locus identifier such as `KL107`, Kaptive extracts the curated protein set and PHAGE-X can pass those proteins into the cached ESM-2 provider. `GET /api/reference-locus/KL107` exposes counts and provenance digests without returning raw sequences.

The uploaded-isolate bridge is now implemented through Kaptive's assembly JSON output. PHAGE-X accepts only a `Typeable` call with no reported locus problems or missing genes, then validates every isolate-derived protein for completeness, translation coverage, uniqueness, amino-acid alphabet, and the ESM-2 length contract. The uploaded assembly and Kaptive's sequence-bearing JSON live only in a temporary directory; the API returns provenance and summary metadata, not sequences.

This still does not establish organism identity or phage susceptibility. The extraction endpoint returns `species_status: unconfirmed` and remains blocked before scoring pending species confirmation, local ESM-2 execution, and reference-set parity validation. PHAGE-X does not substitute whole-genome DNA or arbitrary translated frames for K-locus proteins.

The development environment has Kaptive 3.2, minimap2 2.31, and BLAST+ 2.17 installed. PyTorch and `fair-esm` remain unavailable, so `GET /api/processing-capabilities` reports those exact blockers. `POST /api/inspect-assembly` does not silently fall back to the demo hash representation.

## Installation boundary

Kaptive 3.2 is listed in `backend/requirements-sequence.txt`, while minimap2 must be provided by the execution environment for assembly typing. BLAST+ remains part of the planned broader sequence-analysis environment. PyTorch is platform-specific; install the appropriate CPU/CUDA build and `fair-esm==2.0.0` in a dedicated feature-extraction environment. The 650M ESM-2 weights are large and should be checksum-pinned and cached by deployment infrastructure rather than downloaded during an API request.

## Required validation

- Reference assemblies with accepted Kaptive results
- Exact comparison to PhageHostLearn preprocessing and pooling
- Unit fixtures for Kaptive TSV variants
- Full-genome reference fixtures across representative locus qualities
- CPU/GPU parity tolerance
- Cache concurrency and corruption tests
- Resource limits, job queue, cancellation, and timeouts
- Species confirmation before K-locus interpretation
