# Deployment runbook

## Local production-shaped deployment

1. Copy `.env.example` to `.env` and set the public origin when it differs from localhost.
2. Run `docker compose up --build -d`.
3. Check `http://localhost:8080/healthz` and `http://localhost:8080/api/ready`.
4. Open `http://localhost:8080` and complete both the preloaded and FASTA demo flows.
5. Stop with `docker compose down`.

The web container serves static assets and proxies `/api` to the private API service. The API is not published directly by Compose.

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
