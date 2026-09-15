# PHAGE-X ML and FastAPI guide

## Which paths use machine learning?

PHAGE-X intentionally keeps three paths separate:

1. **Try a sample** uses the small frozen demonstration baseline and synthetic-compatible catalog records. It exists for a fast, reliable product walkthrough.
2. **Use my FASTA** uses the real novel-isolate pipeline when a user uploads a genome. It does not silently fall back to the demo model.
3. **Model benchmark** uses released PhageHostLearn embeddings from held-out host isolates and the trained XGBoost artifact.

The included short sample FASTA is explicitly a demonstration input. A newly uploaded file is sent only to the real sequence pipeline.

## Uploaded-genome ML path

```text
FASTA assembly
  -> assembly QC
  -> fastANI species confirmation
  -> Kaptive capsule-locus typing and protein extraction
  -> local ESM-2 1,280-dimensional host embedding
  -> pair features against 105 phage RBP embeddings
  -> calibrated XGBoost probability
  -> ranked catalog candidates
  -> evidence-gated combination result
```

The API implementation is in `backend/app/main.py`. The novel isolate route begins at `/api/rank-novel-isolate`, and the frontend uses the background-job wrapper at `/api/jobs/novel-rank`.

## XGBoost code

The training implementation is in `backend/ml/train.py`:

- `_new_model()` constructs `xgboost.XGBClassifier`.
- `_fit_and_score()` fits the model, calibrates its probabilities using a validation-host split, and evaluates the untouched test-host split.
- `main()` repeats grouped holdouts, records metrics, and writes the model artifact and manifest.

Pair features are constructed in `backend/app/pair_features.py`. Runtime inference is in `backend/app/research_model.py`, especially `ResearchModel.rank_vector()`.

The current feature vector contains cosine similarity, Euclidean distance, absolute-difference summaries, element-wise-product summaries, embedding norms, and receptor-binding-protein count.

## FastAPI routes

Interactive API documentation is available locally at:

- `http://127.0.0.1:8000/docs`
- `http://127.0.0.1:8000/openapi.json`

Important routes:

- `GET /api/health`
- `GET /api/ready`
- `GET /api/processing-capabilities`
- `POST /api/inspect-assembly`
- `POST /api/extract-isolate-locus`
- `POST /api/embed-isolate-locus`
- `POST /api/jobs/novel-rank`
- `GET /api/jobs/{job_id}`
- `POST /api/research-rank`
- `GET /api/research-model`

## API keys

Local development does not require an API key. Production reads a secret from the `PHAGEX_API_KEY` environment variable and expects it in the `X-API-Key` request header. The actual secret must never be committed, displayed in the interface, or shared in documentation.

The implementation is in `backend/app/config.py` and `backend/app/security.py`. Production rejects missing keys shorter than 24 characters, compares keys using a timing-safe comparison, and rate-limits authenticated requests.
