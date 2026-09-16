# PHAGE-X architecture

## Runtime paths

PHAGE-X exposes three deliberately separate workflows. They share one API and
interface, but their outputs have different evidentiary meaning.

```text
Verified or uploaded Klebsiella assembly
  -> assembly QC
  -> fastANI species confirmation
  -> Kaptive K-locus typing and protein extraction
  -> local ESM-2 host representation (1,280 values)
  -> 11 host-phage pair features
  -> calibrated XGBoost model
  -> ranked 105-phage research catalog
  -> reviewed evidence gate
  -> constrained 2- or 3-member optimizer
  -> result or explicit abstention

Held-out PhageHostLearn host
  -> released host and mean-RBP ESM-2 representations
  -> the same pair-feature and XGBoost contracts
  -> ranking, evaluation labels, and local feature contributions

Small product demonstration
  -> frozen synthetic-compatible records
  -> deterministic interface walkthrough
  -> clearly separated demo result
```

The uploaded-genome route is the primary research pipeline. The held-out path
demonstrates model behavior on hosts excluded from training. The small demo path
exists only for a fast interface walkthrough and does not represent a newly
processed genome.

## Component contracts

- `backend/app/assembly.py` parses multi-record FASTA and returns assembly QC
  without persisting the submitted sequence.
- `backend/app/species.py` confirms the supported organism against a
  checksum-pinned reference using fastANI.
- `backend/app/feature_providers.py` runs Kaptive, validates the translated
  K-locus protein set, generates the 1,280-dimensional ESM-2 representation,
  and caches only vectors plus provenance digests.
- `backend/app/pair_features.py` produces the fixed 11-feature schema used at
  training and inference time.
- `backend/app/research_model.py` verifies and loads the model bundle, checks
  the feature schema, calibrates compatibility scores, ranks the catalog, and
  returns the strongest local XGBoost contributions.
- `backend/app/phage_screening.py` validates versioned independent-review
  records and applies genomic evidence gates.
- `backend/app/real_cocktail.py` searches eligible 2- or 3-member combinations,
  rewarding mean compatibility and family/receptor diversity while penalizing
  redundancy.
- `backend/app/main.py` exposes synchronous inspection routes and a bounded
  background ranking job used by the React client.

Model artifacts and the runtime phage catalog live in `backend/artifacts` and
are checked against the release manifest before use. The reviewed evidence
registry is versioned separately because model compatibility and biological
safety are different claims.

## Cocktail behavior

The optimizer is implemented and tested, but it is fail-closed. A phage is
eligible only when it has reviewed family and receptor metadata, all required
genomic screens pass, the submitter and reviewer differ, and the evidence
record carries a valid SHA-256 source digest.

The repository currently ships with no eligible reviewed records. Real FASTA
runs therefore return a ranked shortlist and an explicit evidence blocker. The
software does not generate a fictional combination to make the demonstration
look complete.

## Safety boundary

Compatibility scores prioritize laboratory work. They are not calibrated
clinical probabilities and do not establish infectivity, killing efficiency,
synergy, safety, dose, route, resistance evolution, or patient outcome.

Uploaded nucleotide and derived protein sequences remain ephemeral. The cache,
API responses, audit log, and PDF reports contain vectors, summaries, and
digests rather than the submitted sequence.

## Scaling boundary

The current job queue and request limiter are process-local, while audit and
feedback records use SQLite. That is appropriate for a single-node research
prototype. Multi-worker deployment requires a shared queue, shared rate-limit
state, managed identity, durable encrypted storage, centralized observability,
and restore testing. These gates are tracked in `docs/PRODUCTION_ROADMAP.md`.
