# PHAGE-X production roadmap

Production means more than putting the current demo on a server. Each milestone below has an explicit exit gate; downstream work must not erase the research-only boundary or imply clinical validation.

## M0 — Product scope and safety contract

**Outcome:** Intended use, exclusions, users, claims, risks, and evidence expectations are frozen.

**Exit gate:** Every surface says research prioritization and laboratory validation only; no dosing, prescribing, patient-specific treatment, or clinical-success claims. Threat and misuse scenarios have named owners.

**Status:** MVP language is in place. A formal risk register and stakeholder sign-off remain.

## M1 — Reproducible deployment foundation

**Outcome:** The app can be built, tested, configured, observed, and deployed consistently.

**Exit gate:** Pinned dependencies, production containers, non-root processes, health/readiness endpoints, environment validation, security headers, CI, and a deployment runbook all pass.

**Status:** Implementation completed in the repository. Backend tests, production API startup, frontend build, and configuration validation pass. The container build awaits a Docker-enabled runner, and a public environment awaits a hosting target and accountable owner.

## M2 — Versioned data and provenance pipeline

**Outcome:** Replace synthetic catalog records with licensed, traceable host–phage observations.

**Exit gate:** Dataset cards, source/license records, immutable versions, schema validation, deduplication, leakage analysis, organism/taxonomy normalization, and train/validation/test splits by isolate are reproducible.

**Status:** Core pipeline implemented against checksum-pinned PhageHostLearn data with license/citation metadata, ID alignment, 1,280-dimension schema validation, and host-disjoint splits. Independent label review and a second external dataset remain.

## M3 — Real sequence and embedding pipeline

**Outcome:** Replace FASTA hashing and synthetic embeddings with validated bioinformatics features.

**Exit gate:** Sequence QC, species confirmation, MLST/K-locus calling, receptor/RBP features, cached ESM-2 embeddings, provenance, deterministic processing, and failure handling pass on a reference set.

**Status:** Real released ESM-2 embeddings are supported for model development. Multi-contig upload QC checks size, alphabet, ambiguity, GC, total length, N50, and digest. Kaptive and ESM-2 providers, capability reporting, and a sequence-free vector cache are implemented and fail closed. Canonical and isolate-derived K-locus proteins can be extracted, completeness-validated, provenance-fingerprinted, and handed to the 1,280-dimensional ESM-2 contract. A genome-sized KL107 fixture passes with 100% identity/coverage and 16 proteins. Species confirmation, the local ESM-2 runtime, broader reference-set validation, and receptor/RBP extraction remain blocking; demo uploads still say placeholder explicitly.

## M4 — Trained compatibility model

**Outcome:** Train and compare XGBoost and simple baselines using leakage-safe evaluation.

**Exit gate:** Locked test-set AUROC/AUPRC plus top-k retrieval, calibration, subgroup performance, uncertainty, confidence intervals, ablations, and error analysis meet predeclared thresholds. SHAP explanations are checked for stability and biological plausibility.

**Status:** A calibrated histogram gradient-boosting baseline is trained on 10,006 real labeled pairs with host-disjoint testing, permutation importance, abstention, and five repeated holdouts. Release remains explicitly blocked pending external validation, confidence intervals, subgroup analysis, and independent review.

## M5 — Cocktail optimizer validation

**Outcome:** Turn individual rankings into a constrained, auditable multi-phage shortlist.

**Exit gate:** Compatibility, receptor/family diversity, redundancy, uncertainty, catalog safety, and constraint sensitivity are evaluated against historical or laboratory-tested combinations. The system can abstain when evidence is weak.

**Status:** The demo exhaustively compares combinations, enforces minimum family and receptor diversity, and records passed constraints. Historical/laboratory combination validation and uncertainty-aware abstention remain.

## M6 — Genomic safety-screening gate

**Outcome:** Exclude unsuitable phages before ranking or cocktail construction.

**Exit gate:** Validated screens cover lysogeny, toxins, virulence, AMR genes, contamination, assembly quality, and required metadata. Failures are blocking and auditable; nothing is called “safe” solely from software output.

**Status:** A fail-closed policy gate and tests cover every required result plus source digest and independent reviewer. Validated external screening tools and reviewed evidence have not been connected, so demo candidates remain `demo-unverified`.

## M7 — Product security and privacy

**Outcome:** Protect uploaded sequences, accounts, and results.

**Exit gate:** Authentication/authorization, tenant isolation, encryption, retention/deletion rules, dependency/container scanning, secrets management, rate limits, audit logs, backups, restore tests, and an independent security review pass.

**Status:** Local controls bound FASTA size, avoid sequence persistence/logging, reject patient data from lab records, restrict CORS, add security headers and request IDs, and document the threat boundary. Identity, tenant isolation, managed storage, retention, and independent testing are intentionally blocking before network deployment.

## M8 — Laboratory workflow and prospective validation

**Outcome:** Predictions are linked to controlled wet-lab evidence.

**Exit gate:** Assay protocols, provenance, blinded prospective evaluation, acceptance thresholds, discrepancy handling, and expert review are approved. Results remain research outputs unless a separate regulatory path permits more.

**Status:** A structured, append-only research observation store accepts four assay types without patient identifiers or clinical free text. Observations never retrain or promote predictions automatically. Protocol approval, blinded prospective evaluation, and expert review remain external requirements.

## M9 — MLOps and production operations

**Outcome:** Models and data can be released, monitored, rolled back, and reproduced.

**Exit gate:** Model registry, signed artifacts, data/model lineage, drift and data-quality monitoring, SLOs, alerts, incident response, rollback/canary procedures, cost limits, and disaster recovery exercises pass.

**Status:** Training emits source SHA-256 lineage, runtime versions, a model card, release decision, and a tamper-detecting artifact manifest. Signing, monitoring, rollback exercises, and operational ownership remain.

## M10 — Staged release and governance

**Outcome:** Move from internal sandbox to controlled research use.

**Exit gate:** Internal, partner, and broader research releases pass separately; each has named owners, training, support, change control, validation reports, legal/privacy review, and post-release monitoring. Clinical use is out of scope without an independent regulatory and quality-management program.
