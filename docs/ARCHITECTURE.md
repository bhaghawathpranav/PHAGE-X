# PHAGE-X architecture

## Current offline path

```text
Preloaded isolate ─┐
                   ├─> isolate representation ─> compatibility baseline ─> ranked phages
Uploaded FASTA ────┘                                                      │
                                                                          └─> cocktail optimizer
                                                                                  │
                                                                                  v
                                                                       explanation + lab gate
```

1. The API accepts exactly one demo isolate ID or FASTA string.
2. Preloaded cases use fixed 8D synthetic-compatible embeddings. Uploads use a deterministic hash projection solely to exercise the offline interface.
3. Each strictly lytic phage receives an explainable logistic score from scaled embedding cosine similarity, receptor/K-locus match, target-species evidence, and evidence quality.
4. A greedy optimizer anchors on the top phage, then adds members using `0.65 compatibility + 0.25 diversity − 0.35 redundancy`.
5. The response includes feature contributions, limitations, and a mandatory laboratory-validation disclaimer.

## Safety boundary

Scores are relative ranking signals, not calibrated clinical probabilities. There is no dosing, administration, safety, synergy, resistance-evolution, or outcome prediction. Demo catalog records are synthetic and are not a substitute for genomic QC or phenotypic evidence.

## Upgrade seams

- Replace FASTA hashing with QC, species confirmation, MLST/K-locus calling, RBP features, and cached ESM-2 inference.
- Replace JSON with a versioned PhageHostLearn-derived feature store carrying provenance.
- Replace `PX-Linear` with trained/calibrated XGBoost plus SHAP and held-out-isolate evaluation.
- Extend optimization with receptor independence, phylogenetic distance, escape-mutant cross-resistance, and uncertainty.
- Add laboratory results as explicit feedback without silently converting predictions into validated claims.

