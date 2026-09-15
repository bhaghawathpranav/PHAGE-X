# PHAGE-X — Pitch and Problem Report

## 1. Executive summary

**PHAGE-X is an AI-guided research platform that converts a _Klebsiella pneumoniae_ isolate into an explainable shortlist of candidate bacteriophages and a complementary 2–3 phage combination for laboratory testing.**

It addresses a practical bottleneck in personalized phage research: a phage may infect one bacterial strain but not another, so researchers must search a catalog for a match and then decide which non-redundant phages are worth testing together. PHAGE-X uses bacterial and phage protein representations, a lightweight compatibility model, and constrained combination selection to prioritize that work. It does not replace susceptibility assays, genomic safety review, manufacturing controls, or clinical judgment.

## 2. Why this problem matters

### Antimicrobial resistance is shrinking conventional options

The World Health Organization places carbapenem-resistant and third-generation-cephalosporin-resistant Enterobacterales in its 2024 critical-priority group. _K. pneumoniae_ is a major member of this group and is especially relevant because resistant hospital strains can carry multiple resistance mechanisms. This makes new antibacterial strategies and better research tools valuable.

Source: [WHO Bacterial Priority Pathogens List 2024](https://www.who.int/publications/i/item/9789240093461)

### Phages are specific, which is both their strength and their bottleneck

Bacteriophages infect bacteria. Their strain specificity can enable targeted killing, but a phage that works against one _Klebsiella_ isolate may fail against another. The bacterial capsule is particularly important: its K-locus encodes capsule structure, while phage receptor-binding proteins and depolymerases help recognize that surface. Therefore, selecting a phage is a matching problem—not simply choosing a phage labeled “for _Klebsiella_.”

Source: [PhageHostLearn, Nature Communications](https://www.nature.com/articles/s41467-024-48675-6); [Kaptive 2.0](https://pmc.ncbi.nlm.nih.gov/articles/PMC9176290/)

### Today’s matching workflow is laboratory-intensive

Researchers commonly screen a bacterial isolate against many phages using spot tests, plaque assays, or liquid growth assays. Plaque assays remain an important reference method and commonly require roughly 24–48 hours after a pure culture is available. Methods and interpretive breakpoints are not yet standardized for routine clinical use. Computational prioritization cannot prove susceptibility, but it can reduce a large catalog to a smaller, better-justified set to test first.

Source: [Determination of phage susceptibility as a clinical diagnostic tool](https://pmc.ncbi.nlm.nih.gov/articles/PMC9532704/); [Considerations for phage therapy in clinical practice](https://pmc.ncbi.nlm.nih.gov/articles/PMC8923208/)

### A single good phage may not be enough

Bacteria can develop phage resistance. Combining phages that recognize different receptors or have non-overlapping resistance profiles is a rational strategy, but simply selecting the three highest individual scores may produce a redundant combination. Combination design therefore needs both predicted activity and biological complementarity.

Source: [Blueprint for complementary phage cocktails](https://pmc.ncbi.nlm.nih.gov/articles/PMC11604943/)

## 3. The problem statement

**How might we help phage researchers rapidly prioritize compatible and complementary phages for a multidrug-resistant _K. pneumoniae_ isolate, while keeping every output explainable, reproducible, and explicitly subject to laboratory validation?**

The problem has four connected parts:

1. Represent the uploaded bacterial isolate in a biologically relevant form.
2. estimate which catalog phages are most compatible with that isolate.
3. select a small combination that adds diversity instead of duplicating the same mechanism.
4. explain the shortlist and preserve a hard boundary between prediction and evidence.

## 4. Existing approaches

### Physical phage susceptibility testing

Spot tests, double-agar plaque assays, efficiency-of-plating measurements, and liquid growth kinetics directly test phage activity. These remain necessary because they observe biological behavior. Their limitations are catalog-scale labor, turnaround time, operator and protocol variability, and incomplete standardization.

### Catalog and rule-based matching

A researcher can filter by bacterial species, capsule type, known receptor, prior host range, and phage metadata. This is interpretable but depends on complete annotations and can miss complex sequence relationships.

### Broad computational host-prediction tools

Many tools infer a likely host species or genus from whole genomes, sequence composition, CRISPR matches, or similarity. They are useful for ecological host assignment, but species-level assignment is not the same task as ranking phages for a particular strain.

### PhageHostLearn

PhageHostLearn directly addresses strain-level _Klebsiella_ matching using ESM-2 representations of bacterial K-locus proteins and phage receptor-binding proteins. Its publication reports cross-validated ROC AUC up to 81.8% and laboratory validation. This is the closest foundation to PHAGE-X and should be credited, not presented as a competitor that PHAGE-X has defeated.

Source: [Prediction of _Klebsiella_ phage-host specificity at strain level](https://pmc.ncbi.nlm.nih.gov/articles/PMC11111740/)

### Capsule/depolymerase prediction

Other related work predicts depolymerases or capsule tropism. These systems deepen understanding of one important infection layer, but they do not necessarily provide an end-to-end isolate-to-ranked-combination product workflow.

Source: [Predicting capsular type-specificity of _Klebsiella_ depolymerases](https://pmc.ncbi.nlm.nih.gov/articles/PMC12491483/)

## 5. What PHAGE-X does

The user chooses one of three input paths:

- **Try a sample:** select a prepared resistant _Klebsiella_ case for a reproducible demo.
- **Use my FASTA:** provide a bacterial genome assembly and run the available sequence-processing path.
- **Test dataset:** select a held-out PhageHostLearn isolate and evaluate the real research model.

The technical workflow is:

1. validate the bacterial assembly and confirm that it is suitable for processing;
2. identify the _Klebsiella_ capsule locus using a Kaptive-compatible path;
3. represent K-locus proteins and phage receptor-binding proteins using ESM-2 embeddings;
4. construct pairwise similarity and distance features;
5. rank phages with a calibrated, lightweight XGBoost classifier;
6. expose score bands and feature-level reasons;
7. select 2–3 members by balancing compatibility, diversity, and redundancy;
8. block real-catalog combination claims when reviewed genomic or laboratory evidence is absent.

## 6. Why PHAGE-X is different

PHAGE-X’s defensible advantage is **workflow integration**, not a claim of discovering a wholly new biological model.

- **Strain-level focus:** it is designed around a particular _K. pneumoniae_ isolate rather than species-level host assignment.
- **Candidate retrieval:** it produces an ordered, testable shortlist instead of only a binary pair prediction.
- **Combination awareness:** it does not blindly take the top three scores; it rewards complementary receptor/family evidence and penalizes redundancy.
- **Explainability:** it uses a lightweight feature model and returns the factors associated with a ranking.
- **Offline reproducibility:** the demo, data subset, artifacts, and precomputed representations run without an external API.
- **Real and demo paths are separated:** synthetic-compatible demonstration outputs are not mixed with held-out research results.
- **Fail-closed evidence gate:** missing genomic safety or validation evidence blocks a real combination rather than being silently treated as safe.
- **Upgrade-ready interfaces:** FASTA QC, K-locus extraction, ESM-2 features, catalog screening, background jobs, and evidence ingestion have explicit boundaries.

## 7. Evidence currently available

The checked-in research artifact uses the public PhageHostLearn release:

- 10,006 labeled host–phage pairs;
- 200 bacterial hosts and 105 phages;
- 333 labeled positive interactions;
- a host-disjoint 70/15/15 train, validation, and test split;
- fixed-split test AUROC 0.887;
- test average precision 0.324;
- top-3 host recall 0.789;
- top-5 host recall 0.842;
- Brier score 0.026;
- five additional host-disjoint holdouts with mean AUROC 0.768 and mean top-5 recall 0.776.

The fixed split is encouraging, while the repeated-holdout variation shows why the model is not ready for a scientific or clinical performance claim. Average precision is the more revealing metric under the strongly imbalanced label distribution; it should be shown alongside AUROC. The correct pitch is **“promising internal retrieval performance that justifies prospective laboratory evaluation,”** not “89% accurate.”

Full details are recorded in `backend/artifacts/model_card.json` and `docs/MODEL_CARD.md`.

## 8. What is genuinely innovative

The novelty claim should be narrow and credible:

> PHAGE-X combines protein-language-model representations, strain-level phage ranking, explainable retrieval, and diversity-aware combination design in one offline _Klebsiella_-focused research workflow with explicit evidence gates.

Individual ingredients already exist: ESM-2, Kaptive, XGBoost, PhageHostLearn, and the concept of receptor-complementary cocktails. The hackathon contribution is their productization into a usable decision-support workflow and its safety-conscious architecture.

## 9. Limitations and risks

- Prediction does not establish infectivity, killing efficiency, synergy, safety, or clinical outcome.
- Many dataset “negative” pairs may be unobserved or study-negative rather than confirmed resistant pairs.
- The positive class is sparse, so performance can change across host splits.
- Capsule and RBP interaction is only an early infection layer; intracellular bacterial defense systems and environmental conditions also matter.
- A compatible phage still requires lifecycle, toxin, virulence, antimicrobial-resistance-gene, purity, sterility, endotoxin, stability, and manufacturing review.
- Combination quality requires experimental testing for antagonism, synergy, escape resistance, and growth suppression.
- The uploaded-isolate path requires exact preprocessing parity and external validation before research release.
- No result should be used to choose treatment, dose, route, or patient management.

## 10. Validation plan

### Immediate technical validation

- reproduce training from checksum-pinned source data;
- compare XGBoost with prevalence, cosine-similarity, capsule-match, and linear baselines;
- report AUROC, average precision, top-k recall, calibration, and confidence intervals;
- test host-disjoint splits and subgroup performance by K-locus novelty;
- review feature explanations with a phage biologist.

### Prospective laboratory validation

- freeze the model and shortlist policy before testing;
- assemble a diverse, blinded _Klebsiella_ isolate panel;
- compare top-k predictions with plaque assay, efficiency of plating, and liquid growth kinetics;
- measure hit rate at k, enrichment over random/catalog rules, and time/tests saved;
- test individual phages and proposed combinations;
- measure bacterial suppression, regrowth, resistance frequency, complementarity, and antagonism;
- document every discrepancy and recalibrate only in a separately governed cycle.

### Product success metrics

The most persuasive practical metrics are:

- percentage of isolates with at least one laboratory-active phage in the top 3 or top 5;
- reduction in phages that must be screened before finding an active candidate;
- laboratory hours and consumables saved per isolate;
- calibration of ranking scores;
- performance on unseen hospitals, K-loci, and phage collections;
- percentage of low-evidence cases where the system correctly abstains.

## 11. Business and impact framing

The initial user is a phage bank, microbiology research laboratory, hospital research program, or biotech team—not a patient. PHAGE-X can sit before wet-lab screening as a prioritization layer. A realistic value proposition is faster catalog triage, more reproducible selection, better experiment traceability, and an accumulating dataset connecting predictions with laboratory outcomes.

A plausible path is:

1. free research prototype and reproducible benchmark;
2. pilot with one phage laboratory and its internal catalog;
3. catalog integration, assay-result tracking, and controlled model evaluation;
4. multi-site research validation;
5. only then, if intended, a separately funded regulatory and quality-management pathway.

## 12. Thirty-second pitch

> Drug-resistant _Klebsiella pneumoniae_ is a critical-priority pathogen, but finding a bacteriophage that matches a particular strain can require screening a large catalog in the lab. PHAGE-X turns a bacterial genome into an explainable shortlist of phages and proposes a complementary two- or three-phage combination for testing. It combines capsule and receptor-binding-protein representations with a lightweight compatibility model, then rewards diversity instead of simply choosing the top three similar candidates. The result is not a treatment recommendation—it is a faster, reproducible way to decide what the laboratory should test first.

## 13. Two-minute pitch

> Antibiotic resistance is making some _Klebsiella pneumoniae_ infections increasingly difficult to address, and the WHO places resistant Enterobacterales in its critical-priority group. Bacteriophages offer a promising targeted approach, but their greatest strength is also a bottleneck: they are often highly strain-specific. A phage labeled for _Klebsiella_ may still fail against the isolate in front of you.
>
> Today, matching usually depends on screening many phages using plaque or liquid-growth assays. Those assays remain essential, but catalog-scale screening costs time and laboratory capacity. PHAGE-X is a research prioritization layer placed before that work.
>
> A user selects a prepared case, uploads a bacterial FASTA assembly, or chooses a held-out benchmark isolate. PHAGE-X represents the bacterial capsule locus and phage receptor-binding proteins using precomputed protein embeddings. A calibrated, explainable classifier ranks 105 catalog phages. It then proposes a small combination that balances predicted compatibility with biological diversity and penalizes redundancy.
>
> What makes our project different is the end-to-end workflow: strain-level matching, ranked retrieval, combination design, explanations, offline reproducibility, and a fail-closed evidence gate in one product. Our internal host-disjoint benchmark reaches a top-5 recall of 84% on the fixed test split, while repeated holdouts average 78%, which is promising but also tells us exactly what must be validated next.
>
> PHAGE-X never claims to replace the lab. Its job is to help researchers test fewer, better-justified candidates first—and to learn from those controlled results over time.

## 14. Likely judge questions

### “Is this just PhageHostLearn with a UI?”

PhageHostLearn is the scientific foundation and is explicitly credited. PHAGE-X adds a usable isolate-to-catalog workflow, reproducible offline artifacts, FASTA-processing interfaces, explainable ranking, constrained multi-phage selection, evidence tracking, abstention, and deployment-oriented engineering. The next scientific contribution must come from prospective combination validation, not from UI alone.

### “Why use ESM-2?”

Protein language models map variable-length protein sequences into fixed-size representations that capture learned sequence patterns. This lets the system compare bacterial K-locus proteins with phage receptor-binding proteins without training a large protein model during the hackathon. PHAGE-X consumes precomputed embeddings and trains only a lightweight downstream classifier.

### “Why XGBoost?”

The dataset is small and imbalanced relative to deep-learning standards. XGBoost trains quickly, handles nonlinear interactions between compact pair features, works offline, and can be inspected. It is also easy to compare with simpler baselines. The model choice is pragmatic, not a claim that XGBoost is biologically optimal.

### “Why cocktails?”

Different phages may cover different host variants or target different receptors. A complementary combination may reduce the chance that one receptor change defeats the entire set. However, the actual combination must be tested for activity, antagonism, and resistance behavior.

### “What does the score mean?”

It is a relative prioritization signal derived from the training labels, not a probability of cure or clinical success. It helps order experiments.

### “What is the moat?”

The long-term moat is not the generic classifier. It is a growing, well-governed mapping between diverse isolate genomes, catalog phages, receptor/capsule features, standardized laboratory measurements, combination outcomes, and failure cases—plus integration into laboratory workflow.

### “What would you do next?”

Freeze the current model, partner with a phage lab, blind a diverse _Klebsiella_ panel, measure top-k enrichment and tests saved, experimentally test the proposed combinations, and use the result to decide whether the approach deserves further research investment.

## 15. One-sentence close

**PHAGE-X does not replace phage susceptibility testing; it makes the first round of testing smaller, faster, explainable, and more strategically diverse.**
