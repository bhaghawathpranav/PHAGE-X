# Contributing to PHAGE-X

PHAGE-X is a research codebase in a safety-sensitive biological domain. A change is complete only when its behavior, evidence boundary, and reproducibility are clear.

## Development setup

```bash
python3 -m venv .venv
.venv/bin/pip install -r backend/requirements-test.txt
cd frontend
npm ci
```

Run the checks before opening a pull request:

```bash
cd backend
../.venv/bin/pytest -q

cd ../frontend
npm run build
```

## Engineering rules

- Keep API request and response models explicit. Do not return unversioned dictionaries when a schema is appropriate.
- Reject malformed or unsupported biological inputs. Do not substitute demo data after a real pipeline stage fails.
- Do not write uploaded nucleotide or protein sequences to logs, audit records, or persistent caches.
- Keep external commands argument based. Do not construct shell commands from user input.
- Bound file size, execution time, queue length, and combinatorial searches.
- Preserve deterministic seeds and immutable artifact digests where reproducibility matters.
- Add a focused regression test for every bug fix.
- Keep user-facing errors distinct from transport status codes and internal exceptions.

## Model and data changes

A model change must include:

- source dataset version, license, and checksums
- leakage-safe grouping policy
- preprocessing and feature schema changes
- model parameters and random seeds
- validation-only threshold and calibration policy
- complete test metrics, confusion counts, and uncertainty estimates
- comparison with the currently released artifact
- a model-card update and explicit release decision

Do not overwrite a model artifact without updating its version and release manifest. Do not tune against the test split.

A data change must document identifier normalization, duplicate handling, label semantics, exclusions, and overlap with existing train, validation, and test groups.

## Safety and evidence changes

Sequence quality, model compatibility, genomic screening, wet-lab susceptibility, and clinical suitability are different claims. Code and interface text must not collapse them into one status.

The reviewed-evidence registry is fail closed. A contributor may not mark a phage as reviewed by inserting unsupported booleans. The evidence source, digest, reviewer identity, and independent-review rule must remain auditable.

## API compatibility

When changing an endpoint:

- update its Pydantic schema
- add or update API tests
- update the React type and request wrapper
- preserve structured error handling
- update OpenAPI-facing documentation and the README when behavior changes

## Pull request checklist

- the backend test suite passes
- the frontend production build passes
- new behavior has tests
- no raw sequence, secret, local database, model checkpoint, or generated archive is added unintentionally
- model and data artifacts have provenance and integrity metadata
- safety and research limitations remain accurate
- documentation describes what the code does now, not a planned capability

