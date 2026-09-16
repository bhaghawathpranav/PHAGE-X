# PHAGE-X integration audit

Date: 2026-09-16  
Branch: `integration/final-integration`  
Safety ref: `safety/pre-integration-20260916`

## Decision

The current integration branch already contains the complete executable research
pipeline and is ahead of the incoming teammate branches in API contracts,
feature validation, local XAI, export handling, and fail-closed safety checks.
No teammate branch was merged wholesale.

The reviewed-evidence artifact from `team/backend-cocktail-shiva` was not
integrated. Its 105 records use empty family and receptor fields, all safety
flags are false, and `source_digest` is the literal value `pending-review`
rather than a SHA-256 digest. Loading it under the current strict schema fails
correctly. Treating those records as reviewed would create unsupported biological
claims, so the cocktail result remains blocked until genuine independent review
records are supplied.

The Sanjay branch has no merge base with the current main lineage and was used
as a reference only. The current branch already has the same real FASTA to
Kaptive to ESM-2 path, with stricter dimension, cache, and model-contract checks.
The old backend-data and backend-api branches contain superseded service and
placeholder API implementations; neither was needed.

## Executable dependency map

| Stage | Input and output contract | IDs, dimensions, paths | Verification |
| --- | --- | --- | --- |
| FASTA to QC | `NovelIsolateRankRequest.fasta` to `AssemblyQC` | DNA assembly; sample at `backend/data/samples/GCF_000364385.3_ASM36438v3_genomic.fna` | `test_assembly.py`, real acceptance |
| QC to species | passing `AssemblyQC` to `SpeciesResult` | FastANI against `backend/data/references/GCF_000240185.1.fna`; ANI and alignment fraction | `test_species.py`, real acceptance |
| Species to Kaptive | accepted Klebsiella assembly to `KaptiveResult` | K-locus ID, confidence, identity, coverage | `test_locus_proteins.py`, real acceptance |
| K-locus to proteins | K-locus result to ordered protein sequences | protein IDs are normalized Kaptive locus IDs | `test_locus_proteins.py`, real acceptance |
| Proteins to host vector | protein sequences to pooled ESM-2 vector | 1,280 finite `float32` values; SQLite cache key is sequence hash | `test_feature_providers.py`, real acceptance |
| Phage/RBP vector | released mean-RBP ESM-2 catalog to vectors | 105 phage IDs; catalog and embedding manifest under `backend/data/phages` and `backend/artifacts` | `test_phage_catalog.py`, real acceptance |
| Host plus phage to features | two 1,280-vectors plus RBP count to pair vector | 11 ordered features in `backend/app/pair_features.py` | `test_research_model.py`, `test_ml_dataset.py` |
| Features to XGBoost | 11-feature matrix to calibrated probabilities | artifact `backend/artifacts/model.joblib`; runtime schema is checked against the model card | `test_research_model.py`, real acceptance |
| Scores to ranking | host vector to sorted candidate list | compatibility scores, candidate IDs, rationales, local XGBoost contribution attributions | API test, real acceptance |
| Ranking to eligibility | candidates plus reviewed registry to cocktail decision | family, receptor, six genomic safety screens, independent reviewer, SHA-256 evidence digest | `test_real_cocktail.py`, `test_phage_screening.py` |
| Eligibility to cocktail | eligible candidates to 2 or 3 members | exhaustive search guard at 60 eligible candidates; diversity and redundancy are explicit objective terms | `test_real_cocktail.py`, real acceptance |
| Cocktail to explanation | optimizer result to status and blockers | fail-closed `blocked` status when evidence is absent | API test, real acceptance |
| API to frontend | typed FastAPI response to React state | `/api/rank-novel-isolate`, `/api/jobs/novel-rank`, PDF export route | backend suite and frontend production build |

## Real acceptance run

The verified ATCC BAA-2146 Klebsiella assembly was executed through the local
pipeline with the real ESM-2 checkpoint and released XGBoost artifact.

- Assembly accepted by QC.
- Species confirmed by reference ANI: 99.6154 percent.
- K-locus identified as KL74.
- Host representation produced as a 1,280-dimensional ESM-2 K-locus vector.
- XGBoost ranking executed against the 105-phage catalog.
- Top candidates included K65PH164 (0.319743), K34PH164 (0.256478), and S8b (0.239367).
- Local XGBoost feature contributions were generated for ranked candidates.
- Cocktail optimizer executed, then returned `blocked` because the current
  reviewed registry contains zero eligible records.
- The API response includes the blockers and the laboratory-validation disclaimer.

Command:

```text
PHAGEX_RUN_REAL_PIPELINE=1 PYTHONPATH=backend .venv/bin/pytest -q backend/tests/test_real_pipeline_acceptance.py -vv
```

Result: `1 passed in 4.25s`.

The normal backend suite passes `69 passed, 1 skipped`, and the frontend
production build completes successfully.

## Remaining external dependency

The only missing input for a real 2 to 3 phage cocktail is genuine reviewed
metadata for candidate phages. The application deliberately does not invent
family, receptor, safety-screen, reviewer, or evidence-digest values. Once a
qualified review process supplies valid records, the existing optimizer and
frontend contract can consume them without a model or schema rewrite.
