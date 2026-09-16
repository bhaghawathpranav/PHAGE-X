# Research protocol

## Working title

Leakage-aware phage-host ranking from capsule-locus and receptor-binding-protein embeddings in *Klebsiella pneumoniae*

## Study purpose

The study will test whether compact features derived from protein-language-model embeddings can prioritize observed phage-host interactions for bacterial isolates excluded from model training. The intended use is candidate triage before laboratory screening. The study will not evaluate treatment efficacy, dosing, patient outcomes, or clinical safety.

The software prototype and the scientific study are related but distinct. A working application demonstrates feasibility. A publishable result requires a prespecified evaluation, appropriate baselines, independent data, uncertainty estimates, and a complete account of failure cases.

## Research questions

1. Does the model rank at least one observed interacting phage within the first three or five candidates for an unseen host?
2. Does the learned model improve on prevalence-only, random, similarity-only, and linear baselines?
3. How stable are ranking performance and calibration across host splits, capsule loci, and source studies?
4. Which feature groups contribute useful signal, and do those contributions remain stable under repeated splits?
5. Can an abstention rule identify host embeddings that are outside the training distribution or have unreliable scores?

## Prespecified outcomes

### Primary outcomes

- top-5 host recall on an untouched external dataset
- average precision on the same external dataset

Top-5 host recall is measured only for hosts with at least one observed positive interaction in the candidate catalog. Average precision is included because the pair labels are highly imbalanced.

### Secondary outcomes

- top-1 and top-3 host recall
- AUROC
- balanced accuracy
- precision, recall, F1, specificity, and Matthews correlation coefficient at a validation-selected threshold
- Brier score and reliability curves
- shortlist size required to recover the first observed positive interaction
- inference time and peak memory for uncached and cached uploaded-genome runs

Raw accuracy will be reported for completeness but will not be used as evidence of model quality.

## Data design

### Development dataset

The current development artifact uses the PhageHostLearn Zenodo release, DOI `10.5281/zenodo.11061100`. Source files are accepted only when their published MD5 values and repository-pinned SHA-256 values match.

The pair dataset is the intersection of the interaction matrix, host K-locus embeddings, and phage receptor-binding-protein embeddings. Missing labels are excluded. Multiple receptor-binding-protein vectors belonging to one phage are mean pooled.

### External dataset

The final study requires a separately sourced dataset that was not used for feature design, threshold selection, calibration, or model choice. Before evaluation, the team must record:

- inclusion and exclusion criteria
- host and phage identifier normalization
- assay definition and positive/negative label rules
- duplicate and near-duplicate handling
- overlap checks against development hosts and phages
- source, license, version, and immutable file digests

If a trustworthy external negative class is unavailable, ranking metrics and positive-retrieval analysis will take priority over binary classification claims.

## Leakage control

All pairs from one bacterial host must remain in the same split. If multiple assemblies represent the same strain or near-clonal isolate, they must also be grouped. A stricter analysis should group by source study and, where sample size allows, by sequence type or genomic cluster.

Preprocessing, feature selection, model selection, calibration, threshold selection, and abstention rules may use training and validation data only. The external test set remains locked until the analysis plan and software version are frozen.

## Models and baselines

The study should compare the same host-disjoint folds across:

1. random ranking with a fixed seed
2. global phage prevalence ranking
3. receptor-binding-protein count only
4. cosine similarity between host and pooled phage embeddings
5. logistic regression on the 11 pair features
6. the current calibrated XGBoost model
7. a reimplementation of the published PhageHostLearn method, if preprocessing and architecture can be reproduced faithfully

Hyperparameter tuning must be restricted to the training and validation partitions. The final paper should report the search space, selection criterion, and compute budget.

## Ablation analysis

The following ablations will be run without changing the locked test data:

- remove embedding norms
- remove receptor-binding-protein count
- similarity features only
- distance and absolute-difference features only
- elementwise-product features only
- replace mean pooling with an alternative prespecified aggregation
- uncalibrated versus calibrated probabilities
- class weighting versus unweighted training

Permutation importance and SHAP may be used for interpretation, but neither establishes a biological mechanism. Stability across splits and consistency with domain knowledge must be assessed separately.

## Statistical analysis

Confidence intervals will be calculated by resampling hosts, not individual host-phage pairs. The analysis will report 95% host-bootstrap intervals for primary outcomes. Repeated grouped holdouts will describe development variance, while the external dataset will be evaluated once after the pipeline is frozen.

Model comparisons should use paired host-level bootstrap differences. The paper will report effect sizes and confidence intervals rather than relying only on p-values. Any subgroup with insufficient sample size will be labeled exploratory.

No final acceptance threshold should be chosen after inspecting external-test results. Minimum acceptable retrieval and calibration criteria must be approved before the external set is opened.

## Error and subgroup analysis

Every false negative and high-scoring study-negative pair should be reviewed for:

- potential untested or mislabeled interactions
- capsule-locus representation quality
- receptor-binding-protein coverage
- distance from the training distribution
- strain duplication or source-study leakage
- phage identifier and taxonomy inconsistencies

Where metadata supports it, performance will be stratified by capsule locus, sequence type, source study, host novelty, phage family, and receptor-binding-protein count. Results will include denominators and confidence intervals.

## Uploaded-genome validation

The sequence pipeline requires its own validation independent of ranking performance:

- accepted *K. pneumoniae* reference panel
- near-neighbor and non-*Klebsiella* rejection panel
- contaminated and fragmented assemblies
- Kaptive calls reviewed against accepted results
- CPU and GPU embedding parity
- deterministic cache and provenance checks
- runtime, memory, cancellation, and concurrency tests

Species confirmation based on one reference is a current prototype constraint. A curated multi-reference panel and expert-reviewed rejection set are required for publication.

## Laboratory validation

A prospective study should blind laboratory investigators to model rank while assays are performed. The protocol must define the candidate catalog, assay method, replicates, controls, success criteria, discrepancy review, and missing-result handling in advance.

Software scores must not be relabeled as susceptibility. Wet-lab outcomes remain separate evidence and must not automatically retrain or promote a model artifact.

## Reproducibility package

A paper submission should archive:

- source-data citations, licenses, and immutable digests
- environment lock files and container image digests
- exact train, validation, and test identifiers
- preprocessing and feature code
- random seeds and model parameters
- calibration and threshold policy
- all primary and secondary results, including failed runs
- model card, limitations, and release decision
- a script that rebuilds every result figure and table from machine-readable outputs

## Publication readiness gates

The work is ready for submission only when:

- the external dataset and analysis plan are frozen before evaluation
- all required baselines and ablations run on identical splits
- primary outcomes include host-level confidence intervals
- leakage and overlap checks are independently reviewed
- the uploaded-genome pipeline passes a representative validation panel
- limitations and negative-label uncertainty are explicit
- no clinical or treatment claim appears in the manuscript
- code, data instructions, and result-generation scripts are reproducible by someone outside the development team

## Suggested manuscript structure

1. Introduction: narrow phage host range and the cost of exhaustive screening
2. Methods: data provenance, leakage control, representations, pair features, model, calibration, and evaluation
3. Results: baseline comparison, retrieval performance, calibration, ablations, subgroup analysis, and runtime
4. Error analysis: label uncertainty, out-of-distribution hosts, and representative failure cases
5. System implementation: uploaded-genome pipeline, provenance, privacy boundary, and abstention
6. Discussion: intended use, limitations, external validity, and prospective laboratory study
7. Data and code availability

