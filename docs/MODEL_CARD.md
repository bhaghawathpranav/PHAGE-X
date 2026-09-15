# PHAGE-X compatibility model card

## Current research artifact

The reproducible training pipeline uses the public PhageHostLearn release (Zenodo DOI `10.5281/zenodo.11061100`, CC BY 4.0). It aligns observed interaction labels with the release's 1,280-dimensional ESM-2 K-locus and receptor-binding-protein embeddings.

The runtime bundle contains only fixed seed-41 test-host embeddings, aggregate phage embeddings, RBP counts, the model, calibrator, and validation-selected decision threshold. Artifact hashes are verified before deserialization. The benchmark API refuses identifiers outside that held-out host list and blocks cocktail generation.

Multiple RBP embeddings per phage are mean-pooled. Eleven pairwise features capture cosine similarity, distances, element-wise products, embedding norms, and RBP count. A class-weighted XGBoost classifier is fitted, then its probabilities are calibrated on a separate validation-host split.

Hosts, not individual rows, are divided across train, validation, and test sets. This prevents the same bacterial isolate appearing in both training and test pairs. The current runtime artifact was trained by the team in Kaggle with the repository's reproducible notebook code. Its original evaluation record is retained as `backend/artifacts/kaggle_metrics.json`, and both it and the model are covered by the release manifest.

## Current Kaggle-trained runtime artifact

- 10,006 labeled host–phage pairs
- 200 bacterial hosts and 105 phages with matching embeddings
- 333 positive labels
- Host-disjoint 70/15/15 train/validation/test split
- Test accuracy: 0.957
- Test balanced accuracy: 0.716
- Test AUROC: 0.885
- Test average precision: 0.314
- Test Brier score: 0.026
- Test F1: 0.407
- Top-3 host recall: 0.842
- Top-5 host recall: 0.895
- Validation-selected decision threshold: 0.1558

These are development results from one deterministic host-disjoint split, not publication-quality or clinical-validation results. Raw accuracy is inflated by the 3.33% positive prevalence, so average precision, balanced accuracy, and top-k host recall are more informative. Missing observations may not be true negatives, and the compact feature model does not reproduce the paper's full multi-instance method. The artifact remains marked `release_decision.approved: false`.

## Required before model release

- Repeated grouped cross-validation and an untouched external dataset
- Prespecified acceptance thresholds approved before external evaluation
- Subgroup analysis by K-locus, sequence type, source study, and novelty
- Negative-label sensitivity analysis
- Calibration and abstention thresholds selected without test-set tuning
- Comparison against prevalence, receptor-match, linear, and full PhageHostLearn baselines
- Independent biological review of explanations and failure cases
