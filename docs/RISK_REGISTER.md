# PHAGE-X research risk register

This register governs the software-only research prototype. It does not authorize clinical use.

| Risk | Current control | Release owner / remaining gate |
|---|---|---|
| A ranking is mistaken for a treatment recommendation | Every output says laboratory validation only; no dosing or patient fields | Product and clinical-safety owners must approve intended-use language |
| An unreviewed phage enters a cocktail | Six-screen fail-closed evidence gate plus independent reviewer and source digest | Microbiology owner must supply and approve evidence |
| Uploaded sequence data leaks | No sequence persistence or body logging; strict sizes; metadata-only audit | Security owner must validate encryption, retention, deletion, and tenant isolation |
| Dataset leakage inflates model performance | Host-disjoint splits, immutable hashes, repeated holdouts | ML owner must add a second external dataset and locked acceptance criteria |
| Unknown interactions are treated as negatives | Model card and error analysis flag the label limitation | Data owner must independently review labels and run sensitivity analysis |
| Out-of-distribution isolate gets a confident rank | Species ANI, K-locus QC, embedding-envelope check, and abstention | Bioinformatics owner must approve a broader reference panel |
| Source or model artifact is tampered with | Startup hash verification for data and model artifacts | Operations owner must add managed signing and key rotation |
| Metadata is lost | Consistent SQLite backup plus digest and integrity verification | Operations owner must schedule backups and perform a documented restore drill |

No risk above may be marked closed solely because a software check passes. Independent evidence and accountable human sign-off are required where stated.
