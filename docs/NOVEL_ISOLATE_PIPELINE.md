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
14. Checksum-pinned offline fastANI confirmation against NCBI RefSeq `GCF_000240185.1`
15. Fail-closed 95% ANI and 65% aligned-fragment gates before K-locus extraction
16. Checksum-pinned ESM-2 model and contact-regression manifests
17. Strictly local checkpoint loading with PyTorch 2.6+ safe-global compatibility
18. End-to-end isolate feature endpoint returning vector provenance, never the raw vector
19. Embedding-distribution envelope check against runtime reference hosts
20. Calibrated ranking against 105 released mean-RBP phage embeddings with per-candidate feature evidence

## Current blocking boundary

The canonical reference-locus bridge is implemented: for a strict locus identifier such as `KL107`, Kaptive extracts the curated protein set and PHAGE-X can pass those proteins into the cached ESM-2 provider. `GET /api/reference-locus/KL107` exposes counts and provenance digests without returning raw sequences.

The uploaded-isolate bridge is now implemented through Kaptive's assembly JSON output. PHAGE-X accepts only a `Typeable` call with no reported locus problems or missing genes, then validates every isolate-derived protein for completeness, translation coverage, uniqueness, amino-acid alphabet, and the ESM-2 length contract. The uploaded assembly and Kaptive's sequence-bearing JSON live only in a temporary directory; the API returns provenance and summary metadata, not sequences.

Species confirmation now runs before K-locus extraction. The extraction endpoint reports the reference accession, ANI, aligned fraction, reference digest, and fastANI version. A checksum-pinned complete HS11286 genome confirms at 100% ANI and 99.84% aligned fragments; an unrelated genome-sized sequence is rejected.

One reference and a conventional ANI cutoff are not sufficient validation across the full _K. pneumoniae_ species complex. A curated multi-reference panel, near-neighbor rejection set, contaminated/mixed assembly tests, and taxonomic expert review remain required. This gate establishes software evidence only and does not establish phage susceptibility.

The development environment has Kaptive 3.2, minimap2 2.31, fastANI 1.33, BLAST+ 2.17, PyTorch 2.8, and `fair-esm` 2.0. The official 650M checkpoint and contact-regression sidecar are locally cached and SHA-256 verified. `GET /api/processing-capabilities` reports the complete runtime ready. `POST /api/rank-novel-isolate` performs QC, species confirmation, isolate K-locus translation, ESM-2 inference, distribution checking, and real-catalog ranking. It returns only digests, scores, and summary evidence.

## Installation boundary

Kaptive 3.2 is listed in `backend/requirements-sequence.txt`, while minimap2 and fastANI must be provided by the execution environment. BLAST+ remains part of the planned broader sequence-analysis environment. The validated CPU runtime is pinned in `backend/requirements-embedding.txt`. `scripts/fetch_esm2_checkpoint.py` downloads both official files atomically and verifies their manifest digests; runtime requests never download weights.

On the development Apple Silicon CPU, verified local inference took 3.74 seconds for one short protein and 29.89 seconds for the 16-protein KL107 set. A complete RefSeq assembly took 39.84 seconds through QC, ANI, Kaptive, and the 21-protein KL103 embedding; the identical cached API request returned the same vector digest in 2.42 seconds. The isolated vector-cache lookup took 1.3 milliseconds. These are development observations, not deployment SLOs; concurrent production extraction still requires a bounded worker queue.

## Required validation

- Reference assemblies with accepted Kaptive results
- Exact comparison to PhageHostLearn preprocessing and pooling
- Unit fixtures for Kaptive TSV variants
- Full-genome reference fixtures across representative locus qualities
- CPU/GPU parity tolerance
- Cache concurrency and corruption tests
- Resource limits, job queue, cancellation, and timeouts
- Curated multi-reference species panel and near-neighbor validation
