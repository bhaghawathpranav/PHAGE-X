# PHAGE-X

**AI-guided, explainable phage candidate prioritization for multidrug-resistant _Klebsiella pneumoniae_.**

PHAGE-X is a software-only 24-hour hackathon MVP. It turns a preloaded isolate or uploaded FASTA into an explainable phage ranking and a complementary 2–3 member cocktail candidate. The demo runs locally without external APIs.

> **For laboratory validation only.** This research prototype does not diagnose, prescribe treatment, recommend dosing, establish safety, or predict clinical success.

## What works

- Two offline _K. pneumoniae_ demo isolates, including an ST258 / KL107 multidrug-resistant case
- FASTA validation and deterministic placeholder embeddings
- Frozen, explainable logistic compatibility baseline
- Ranked strictly lytic demo phages with feature contributions
- Greedy cocktail construction using compatibility + diversity − redundancy
- Responsive React UI, FastAPI schema/docs, and API tests
- Separate real-model benchmark mode restricted to held-out PhageHostLearn isolates
- Kaptive-backed KL reference-protein extraction and a cached ESM-2 feature interface
- Fail-closed isolate-derived K-locus protein extraction with ephemeral sequence handling
- Offline fastANI species confirmation against a checksum-pinned NCBI RefSeq genome
- Verified local ESM-2 650M inference with a sequence-free persistent vector cache
- Novel-isolate ranking against all 105 released PhageHostLearn RBP profiles
- One-click checksum-verified ATCC BAA-2146 FASTA example for the complete uploaded-genome pipeline
- In-app model-evidence summary focused on top-5 recall, AUROC, PR-AUC, class imbalance, and appropriate interpretation
- Bounded background feature jobs and a fail-closed reviewed-evidence cocktail optimizer
- Offline source genomes and 274 author-identified RBP sequences for all 105 catalog phages
- Per-phage sequence QC plus a fail-closed reviewed-evidence registry; sequence quality is never treated as biological safety clearance

## Run locally

Prerequisites: Python 3.9+ and Node 18+.

```bash
python3 -m venv .venv
.venv/bin/pip install -r backend/requirements-test.txt
cd frontend && npm install && cd ..
./scripts/demo.sh
```

Open [http://localhost:5173](http://localhost:5173). API documentation is at [http://localhost:8000/docs](http://localhost:8000/docs).

## Verify

```bash
cd backend && ../.venv/bin/pytest -q
cd frontend && npm run build
```

## Demo walkthrough

1. Keep featured `KPN-HX01` selected and choose three phages.
2. Run candidate discovery and explain the top candidate using its contributions.
3. Show how the cocktail rewards diverse families/receptors and penalizes overlapping host-range tags.
4. Expand a ranked candidate and point out the limitations and lab-validation gate.
5. Return to the input and switch to FASTA to show the future-facing interface.
6. Choose **Load verified example** to run the public ATCC BAA-2146 assembly through QC, species confirmation, KL74 extraction, ESM-2 features, and catalog ranking.

The dataset is deliberately synthetic-compatible: it supports a reproducible product demo but must not be represented as experimentally validated observations. See [architecture notes](docs/ARCHITECTURE.md) for model details and the upgrade path.

For the problem framing, competitive positioning, validation strategy, and ready-to-deliver scripts, see the [pitch report](docs/PITCH_REPORT.md).

The **Real benchmark** tab is different from the synthetic demo. It loads the hash-verified trained artifact, accepts only host IDs from the model's fixed held-out test split, and ranks 105 real dataset phage IDs using released ESM-2 embeddings. Each real phage has traceable genome QC through `/api/phage-evidence/{phage_id}`. Cocktail construction remains blocked because genomic safety and normalized diversity metadata are not yet independently reviewed.

The FASTA tab also exposes **Inspect real-pipeline readiness**. It performs multi-contig assembly QC and reports missing local Kaptive/minimap2/fastANI/ESM-2 capabilities without storing the sequence or falling back silently. With the complete local toolchain, an uploaded assembly is species-confirmed, K-locus typed, embedded, distribution-checked, and ranked against 105 released phage RBP profiles. Real cocktail construction remains blocked until independent phage safety and diversity metadata are available. See `docs/NOVEL_ISOLATE_PIPELINE.md`.

The legacy synthetic single-record FASTA route is intentionally capped at 5 MB; the real multi-contig assembly pipeline accepts up to 15 MB. Reviewed phage evidence is validated against a strict versioned schema. Use `scripts/migrate_reviewed_evidence.py SOURCE OUTPUT` to create a validated migrated copy without overwriting the source registry.

To enable offline ESM-2 extraction, install `backend/requirements-embedding.txt`, run `scripts/fetch_esm2_checkpoint.py` once, and use `scripts/precompute_esm2.py` to warm canonical locus vectors. The 2.60 GB checkpoint is kept in the local Torch cache and verified against `backend/data/esm2/manifest.json`; it is not stored in Git.

## Production path

The current repository includes CI, environment validation, health/readiness checks, security headers, production API-key enforcement, request throttling, metadata-only audit records, verified state backups, and a deployment runbook. Local development remains key-free. Production requires `PHAGEX_API_KEY` with at least 24 characters and accepts it in the `X-API-Key` header. It is not yet a scientifically validated production model. Follow the gated [production roadmap](docs/PRODUCTION_ROADMAP.md), [risk register](docs/RISK_REGISTER.md), and [deployment runbook](docs/DEPLOYMENT.md).

```bash
docker compose up --build
# app: http://localhost:8080
# readiness: http://localhost:8080/api/ready
```

## Reproduce the research-model benchmark

The data fetch is checksum-pinned to the public PhageHostLearn Zenodo release.

Run the complete download, training, calibration, and evaluation workflow:

```bash
./scripts/train_and_evaluate.sh
```

The untouched host-disjoint test set reports ROC-AUC, average precision (PR-AUC), Brier score, accuracy, balanced accuracy, precision, recall, specificity, F1, Matthews correlation, the complete confusion matrix, and top-3/top-5 per-host recall. The classification threshold is chosen from validation data only. Host-bootstrap confidence intervals and repeated host-group holdouts are written to `backend/artifacts/model_card.json`.

The equivalent manual commands are:

```bash
.venv/bin/pip install -r backend/requirements-ml.txt
.venv/bin/python scripts/fetch_phagehostlearn.py
PYTHONPATH=backend .venv/bin/python -m ml.train \
  --data-dir work/phagehostlearn \
  --manifest data/phagehostlearn/manifest.json \
  --output-dir backend/artifacts
```

See `docs/MODEL_CARD.md`. The trained joblib artifact is intentionally ignored; the JSON model card is retained for review.
