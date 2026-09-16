# PHAGE-X

PHAGE-X is a research prototype for prioritizing bacteriophages against multidrug-resistant *Klebsiella pneumoniae*. It accepts a known isolate or a bacterial genome assembly, constructs a host representation, ranks a fixed phage catalog with a calibrated XGBoost model, and produces an evidence-backed shortlist for laboratory follow-up.

The project is designed around a practical question: can protein-language-model representations reduce the number of phages that must be screened for a previously unseen bacterial isolate?

PHAGE-X does not determine susceptibility, prescribe a cocktail, or support treatment decisions. Its output is a ranking for research use. Plaque assays, genomic review, and independent biological interpretation remain necessary.

## Project status

This repository contains a working genome-to-ranking prototype and a reproducible model benchmark. The combination optimizer is implemented and tested, but the shipped catalog has no phages with complete independently reviewed family, receptor, and genomic-safety evidence. Real runs therefore stop after ranking and report the evidence blocker instead of issuing a combination. The system is not clinically validated and the model artifact is deliberately marked as not approved for release.

Implemented:

- whole-genome FASTA parsing and assembly quality checks
- checksum-pinned fastANI species confirmation
- Kaptive capsule-locus typing and protein extraction
- local ESM-2 `esm2_t33_650M_UR50D` inference with a sequence-free cache
- calibrated XGBoost ranking against 105 phages
- host-disjoint model evaluation on held-out bacterial isolates
- per-candidate XGBoost feature contributions and downloadable PDF reports
- fail-closed cocktail and genomic-evidence gates
- FastAPI service, React interface, CI, containers, audit metadata, and tests

Still required before scientific or operational release:

- evaluation on an independent external host-phage dataset
- stronger negative-label curation and sensitivity analysis
- comparison with additional biological and statistical baselines
- subgroup analysis across capsule loci, sequence types, and source studies
- independent review of genomic safety evidence
- reviewed family and receptor metadata for enough catalog phages to construct a diverse combination
- prospective wet-lab validation
- identity, tenant isolation, managed secrets, monitoring, and an external security review

## Research contribution

The current work is a systems and evaluation contribution, not a claim of a new state-of-the-art biological model. It combines a leakage-aware compatibility benchmark with a complete path from an uploaded assembly to a ranked catalog.

The central research question is:

> For bacterial hosts excluded from training, how reliably can compact pairwise features derived from host K-locus and phage receptor-binding-protein embeddings retrieve at least one observed interacting phage within a small laboratory shortlist?

The primary product-aligned measure is top-k host recall. AUROC, average precision, calibration, balanced accuracy, and thresholded error counts are reported as supporting measures. Raw accuracy is not used as the headline result because positive interactions represent only 3.33% of evaluated pairs.

The proposed publication study, baselines, ablations, statistical analysis, and external-validation gates are defined in [docs/RESEARCH_PROTOCOL.md](docs/RESEARCH_PROTOCOL.md).

## System workflow

```text
Genome assembly
    |
    v
Assembly QC -> species confirmation -> K-locus typing
    |
    v
K-locus proteins -> ESM-2 host embedding
    |
    +-------------------------------+
                                    |
Phage RBP embeddings ---------------+-> pair features -> calibrated XGBoost
                                                            |
                                                            v
                                             ranked research shortlist
                                                            |
                                                            v
                                           evidence and laboratory gates
```

An uploaded assembly is processed locally and is not stored. The persistent feature cache contains vectors and provenance digests, not raw nucleotide or protein sequences.

### Input validation

The uploaded-genome route accepts multi-record FASTA assemblies up to 15 MB. A sequence must pass basic assembly checks and match the pinned *K. pneumoniae* reference at a minimum of 95% ANI and 65% aligned fragments. Inputs outside this range are rejected before feature extraction.

The repository includes a checksum-verified *K. pneumoniae* ATCC BAA-2146 assembly for demonstration. In the validated local environment it produces 99.6154% ANI, 91.1% alignment coverage, and a Typeable KL74 call.

### Host and phage representations

Host features are derived from proteins in the Kaptive-called capsule locus. Phage features use the released ESM-2 receptor-binding-protein embeddings from PhageHostLearn. Multiple receptor-binding proteins for one phage are mean pooled.

Each host-phage pair is represented by 11 compact features:

- cosine similarity and Euclidean distance
- mean, standard deviation, and maximum absolute difference
- mean, standard deviation, and maximum elementwise product
- host and phage embedding norms
- receptor-binding-protein count

### Ranking model

The classifier is XGBoost with class weighting for the imbalanced interaction labels. Raw model scores are calibrated by logistic regression on validation hosts. The binary decision threshold is selected on the validation split only. Runtime artifacts and source data are verified against SHA-256 manifests before use.

Each ranked candidate also includes its three largest local XGBoost feature contributions. These values explain the direction and magnitude of features in the raw tree-model score. They do not explain the downstream logistic calibration or establish a biological mechanism.

## Data and evaluation

The training workflow uses the public [PhageHostLearn dataset](https://doi.org/10.5281/zenodo.11061100), distributed under CC BY 4.0.

Aligned data used by the current artifact:

- 200 bacterial hosts
- 105 phages
- 10,006 labeled host-phage pairs
- 333 observed positive pairs
- 3.33% positive prevalence
- 1,280-dimensional host and phage embeddings

Hosts, rather than individual pairs, are split into training, validation, and test groups. The fixed seed-41 split contains 139 training hosts, 31 validation hosts, and 30 test hosts. No host appears in more than one split.

### Current held-out results

- ROC-AUC: 0.885
- average precision, or PR-AUC: 0.314
- balanced accuracy: 0.716
- positive recall: 0.458
- precision: 0.367
- F1: 0.407
- Matthews correlation coefficient: 0.388
- Brier score: 0.026
- top-3 host recall: 0.842
- top-5 host recall: 0.895
- confusion matrix: 1,398 TN, 38 FP, 26 FN, 22 TP

Top-5 host recall means that, among eligible held-out hosts with at least one observed positive interaction, 89.5% had an observed interacting phage within the model's first five candidates. It does not mean that every top-five phage will infect a new isolate.

These results come from an internal host-disjoint split of one source dataset. They are suitable for evaluating the prototype and motivating a larger study, but not for a biological or clinical performance claim. See [docs/MODEL_CARD.md](docs/MODEL_CARD.md) and the machine-readable [backend/artifacts/model_card.json](backend/artifacts/model_card.json).

## Run the application

### Core application and model-validation mode

Requirements:

- Python 3.9 or later
- Node.js 18 or later

```bash
python3 -m venv .venv
.venv/bin/pip install -r backend/requirements-test.txt
cd frontend
npm ci
cd ..
./scripts/demo.sh
```

Open `http://127.0.0.1:5173`. The OpenAPI interface is available at `http://127.0.0.1:8000/docs`.

### Complete uploaded-genome pipeline

The full FASTA route also needs the local sequence and embedding toolchain:

```bash
.venv/bin/pip install -r backend/requirements-embedding.txt
.venv/bin/python scripts/fetch_esm2_checkpoint.py
```

Install `minimap2` and `fastANI` through the operating system. Kaptive is included in `backend/requirements-sequence.txt`. Runtime requests never download model weights or call an external API. Read [docs/NOVEL_ISOLATE_PIPELINE.md](docs/NOVEL_ISOLATE_PIPELINE.md) for the validated tool versions and failure rules.

### Interface modes

`XGBoost sample` runs the trained model on a prepared held-out isolate with released embeddings.

`Use my FASTA` runs assembly QC, species confirmation, capsule typing, ESM-2 feature generation, distribution checking, and catalog ranking. Use the verified KL74 example to exercise the complete path.

`Model validation` evaluates the trained artifact on isolates excluded from training. It exists to inspect ranking behavior and evaluation evidence, not to analyze a new genome.

## Reproduce model training

The training script verifies the published source checksums before constructing the pair dataset.

```bash
./scripts/train_and_evaluate.sh
```

Equivalent manual steps:

```bash
.venv/bin/pip install -r backend/requirements-ml.txt
.venv/bin/python scripts/fetch_phagehostlearn.py
PYTHONPATH=backend .venv/bin/python -m ml.train \
  --data-dir work/phagehostlearn \
  --manifest data/phagehostlearn/manifest.json \
  --output-dir backend/artifacts
```

The run writes the trained bundle, runtime catalog, model card, source lineage, calibration report, repeated host-group holdouts, bootstrap intervals, permutation importance, and release manifest.

## Verification

Run the standard backend suite and frontend production build with one command:

```bash
./scripts/verify.sh
```

The equivalent individual commands are:

```bash
cd backend
../.venv/bin/pytest -q

cd ../frontend
npm run build
```

GitHub Actions repeats the backend tests, frontend production build, and container build for every push and pull request.

The heavier local acceptance test uses the bundled verified genome and the installed native/ESM-2 toolchain:

```bash
PHAGEX_RUN_REAL_PIPELINE=1 ./scripts/verify.sh
```

It verifies assembly parsing, fastANI species confirmation, Kaptive KL74 extraction, a finite 1,280-dimensional ESM-2 representation, calibrated ranking of all 105 phages, the reviewed-evidence gate, and PDF creation. With the repository's current evidence registry, the expected combination state is `blocked`; a selected 2–3 phage result would be dishonest until real reviewed metadata is added.

## Repository structure

```text
backend/app/          API, sequence pipeline, inference, security, and reporting
backend/ml/           dataset construction, training, calibration, and evaluation
backend/artifacts/    versioned model card, model, catalog, and release manifest
backend/tests/        API, ML, security, data, and pipeline tests
frontend/src/         React application
data/                 checksum-pinned public-data manifests
docs/                 architecture, model, research, risk, and deployment records
scripts/              reproducible setup, training, migration, and backup commands
```

## Production engineering boundary

The repository includes production-shaped controls: non-root containers, strict configuration validation, exact CORS origins, API-key enforcement in production, request throttling, request IDs, security headers, health and readiness checks, bounded background work, artifact integrity checks, metadata-only audit logging, and verified SQLite backups.

That does not make the system production-ready. The current rate limiter and job queue are process-local. SQLite is appropriate for this single-node prototype but not for horizontally scaled request and job coordination. A public deployment also needs managed identity, role-based access control, tenant separation, encrypted durable storage, centralized observability, signed releases, restore drills, and an independent security assessment.

The required engineering and evidence gates are tracked in [docs/PRODUCTION_ROADMAP.md](docs/PRODUCTION_ROADMAP.md), [docs/RISK_REGISTER.md](docs/RISK_REGISTER.md), [SECURITY.md](SECURITY.md), and [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md).

## Contributing

Changes should preserve host-disjoint evaluation, fail-closed biological evidence gates, sequence non-persistence, and reproducible artifact lineage. Read [CONTRIBUTING.md](CONTRIBUTING.md) before modifying the model, data pipeline, API schemas, or safety behavior.

## Citation and licensing

The source dataset must be cited as PhageHostLearn, Zenodo DOI `10.5281/zenodo.11061100`, under its CC BY 4.0 terms.

The repository does not currently declare a software license. Until the project owners add one, the source should not be assumed to grant redistribution or commercial-use rights.
