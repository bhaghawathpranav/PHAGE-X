# PHAGE-X compatibility model card

## Current research artifact

The reproducible training pipeline uses the public PhageHostLearn release (Zenodo DOI `10.5281/zenodo.11061100`, CC BY 4.0). It aligns observed interaction labels with the release's 1,280-dimensional ESM-2 K-locus and receptor-binding-protein embeddings.

The runtime bundle contains only fixed seed-41 test-host embeddings, aggregate phage embeddings, RBP counts, the model, and calibrator. Artifact hashes are verified before deserialization. The benchmark API refuses identifiers outside that held-out host list and blocks cocktail generation.

Multiple RBP embeddings per phage are mean-pooled. Eleven pairwise features capture cosine similarity, distances, element-wise products, embedding norms, and RBP count. A class-balanced histogram gradient-boosting model is fitted, then its probabilities are calibrated on a separate validation-host split.

Hosts—not individual rows—are divided across train, validation, and test sets. This prevents the same bacterial isolate appearing in both training and test pairs. The generated `backend/artifacts/model_card.json` records exact source hashes, split counts, runtime versions, metrics, feature importance, host-bootstrap confidence intervals, calibration bins, threshold error counts, and abstention coverage.

## Latest local benchmark

- 10,006 labeled host–phage pairs
- 200 bacterial hosts and 105 phages with matching embeddings
- 333 positive labels
- Host-disjoint 70/15/15 train/validation/test split
- Test AUROC: 0.906
- Test average precision: 0.354
- Test Brier score: 0.025
- Top-3 host recall: 0.789
- Top-5 host recall: 0.895

These are development results from one deterministic split, not publication-quality or clinical-validation results. The positive class is sparse, missing observations may not be true negatives, and the compact feature model does not reproduce the paper's full multi-instance method.

The 500-repeat host bootstrap gives 95% intervals of 0.842–0.955 for AUROC, 0.197–0.579 for average precision, and 0.014–0.037 for Brier score. Ten-bin expected calibration error is 0.017. These are internal uncertainty estimates, not external validation.

Across five additional host-disjoint holdouts, mean AUROC was 0.755 (range 0.680–0.826), mean average precision was 0.277 (range 0.190–0.368), mean top-3 recall was 0.679, and mean top-5 recall was 0.719. This variance is why the generated artifact is explicitly marked `release_decision.approved: false` despite the stronger fixed-split result.

## Required before model release

- Repeated grouped cross-validation and an untouched external dataset
- Prespecified acceptance thresholds approved before external evaluation
- Subgroup analysis by K-locus, sequence type, source study, and novelty
- Negative-label sensitivity analysis
- Calibration and abstention thresholds selected without test-set tuning
- Comparison against prevalence, receptor-match, linear, and full PhageHostLearn baselines
- Independent biological review of explanations and failure cases
