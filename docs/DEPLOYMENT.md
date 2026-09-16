# Deployment runbook

## Local production-shaped deployment

1. Copy `.env.example` to `.env`, replace `PHAGEX_API_KEY` with a random value of at least 24 characters, and set the public origin when it differs from localhost.
2. Run `docker compose up --build -d`.
3. Check `http://localhost:8080/healthz` and `http://localhost:8080/api/ready`.
4. Open `http://localhost:8080` and complete the held-out model-validation flow.
5. Stop with `docker compose down`.

The web container serves static assets and proxies `/api` to the private API service. It adds the internal API key at the trusted gateway, so the credential is not embedded in browser code. The API is not published directly by Compose. The default backend image contains the trained ranking artifact but not the 2.60 GB ESM-2 checkpoint or host-installed fastANI/minimap2 binaries; the complete uploaded-genome route requires a separate feature-worker image or mounted runtime with those dependencies.

## Before any public environment

- Choose an accountable owner, hosting provider, region, domain, and budget.
- Terminate TLS at the platform load balancer and set `PHAGEX_ALLOWED_ORIGINS` to the exact HTTPS origin.
- Set a secret `PHAGEX_API_KEY` of at least 24 characters; protected API calls must send it as `X-API-Key`.
- Tune `PHAGEX_RATE_LIMIT_PER_MINUTE` for the deployment capacity. The default is 60 requests per key per minute.
- Persist `PHAGEX_AUDIT_DB` on an encrypted volume. It stores request IDs, routes, status codes, and timing—not sequences or request bodies.
- Store configuration in the platform secret/config service; do not commit `.env`.
- Enable platform access logs, service metrics, alerts, container scanning, backups, and cost limits.
- Keep the deployment access-controlled until data provenance, security/privacy, and prospective validation milestones pass.
- Execute smoke tests, record image digests, and document rollback to the previous digest.

This repository is deployment-ready, not authorization to publish or use the demo for clinical decisions.

## State backup

Run `PYTHONPATH=backend .venv/bin/python scripts/backup_state.py` to create a timestamped, transactionally consistent copy of the feedback, audit, and embedding-cache databases. The command immediately verifies SQLite integrity and SHA-256 digests. A restore remains an operator-controlled action: test it in an isolated directory before replacing live state.
