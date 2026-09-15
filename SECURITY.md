# PHAGE-X security policy

PHAGE-X is currently a local research prototype, not a public or clinical service.

## Current controls

- Uploaded FASTA is validated, bounded to 5 MB, processed in memory, and not written or included in request logs.
- Analysis responses carry non-identifying UUIDs and mandatory research-only language.
- Laboratory observations reject patient data by schema and contain no free-text field.
- Production configuration rejects wildcard CORS.
- API responses include request IDs, no-store caching, clickjacking protection, MIME-sniffing protection, and no-referrer policy.
- Model releases carry source lineage and tamper-detecting SHA-256 manifests.
- Dependency and container builds are defined in CI.

## Blocking controls before network deployment

- Authentication, role-based authorization, and tenant isolation
- Managed secrets, TLS, encryption at rest, and key rotation
- Distributed rate limits and abuse detection
- Central audit storage without sequence or patient content
- Retention, export, and deletion procedures
- Dependency, SAST, container, and infrastructure scanning
- Independent threat modeling and penetration testing
- Incident response, backup/restore tests, and named security ownership

Do not report a security vulnerability by putting private sequence or patient information into an issue. Use the private contact process established by the eventual project owner.

