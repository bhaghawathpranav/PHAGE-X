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

The dataset is deliberately synthetic-compatible: it supports a reproducible product demo but must not be represented as experimentally validated observations. See [architecture notes](docs/ARCHITECTURE.md) for model details and the upgrade path.

The **Real benchmark** tab is different from the synthetic demo. It loads the hash-verified trained artifact, accepts only host IDs from the model's fixed held-out test split, and ranks 105 real dataset phage IDs using released ESM-2 embeddings. Cocktail construction remains blocked because genomic safety and normalized diversity metadata are not yet independently reviewed.

The FASTA tab also exposes **Inspect real-pipeline readiness**. It performs multi-contig assembly QC and reports missing local Kaptive/minimap2/fastANI/ESM-2 capabilities without storing the sequence or falling back silently. The API confirms species by ANI before extracting validated isolate-derived K-locus proteins, but scoring remains blocked until ESM-2 and broader reference-panel validation pass. See `docs/NOVEL_ISOLATE_PIPELINE.md`.

## Production path

The current repository includes production-shaped containers, CI, environment validation, health/readiness checks, security headers, and a deployment runbook. It is not yet a scientifically validated production model. Follow the gated [production roadmap](docs/PRODUCTION_ROADMAP.md) and [deployment runbook](docs/DEPLOYMENT.md).

```bash
docker compose up --build
# app: http://localhost:8080
# readiness: http://localhost:8080/api/ready
```

## Reproduce the research-model benchmark

The data fetch is checksum-pinned to the public PhageHostLearn Zenodo release.

```bash
.venv/bin/pip install -r backend/requirements-ml.txt
.venv/bin/python scripts/fetch_phagehostlearn.py
PYTHONPATH=backend .venv/bin/python -m ml.train \
  --data-dir work/phagehostlearn \
  --manifest data/phagehostlearn/manifest.json \
  --output-dir backend/artifacts
```

See `docs/MODEL_CARD.md`. The trained joblib artifact is intentionally ignored; the JSON model card is retained for review.
