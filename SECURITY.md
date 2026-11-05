# Security Policy

This document outlines the security policy for the **Quality Deviation Risk Monitor** project, including supported versions, how to report vulnerabilities, and security considerations specific to its GxP/CSV regulatory context.

---

## Supported Versions

| Version | Supported |
|---------|-----------|
| `main` (latest) | ✅ Active |
| Any tagged release | ✅ Patch support for 90 days post-release |
| Older branches | ❌ No support |

---

## Reporting a Vulnerability

**Please do not report security vulnerabilities through public GitHub Issues.**

If you discover a security vulnerability, follow responsible disclosure:

1. **Email the maintainer** directly via the contact listed on the [GitHub profile](https://github.com/alianisreyesr).
2. Include in your report:
   - A clear description of the vulnerability
   - Steps to reproduce (proof of concept if applicable)
   - Potential impact assessment
   - Any suggested mitigation or fix
3. You will receive an acknowledgment within **72 hours**.
4. A fix will be targeted within **14 days** for critical/high severity issues.
5. You will be credited in the `CHANGELOG.md` entry for the fix (unless you prefer anonymity).

---

## Security Considerations for GxP / CSV Context

This system is designed to simulate a **computer system in a GxP-regulated environment** subject to **21 CFR Part 11**, **GAMP 5**, and **ALCOA+** data integrity principles. The following security areas are treated as in-scope for this project:

### Audit Trail Integrity
- All review actions (`acknowledge`, `investigate`, `close`) are recorded in the audit trail with actor, timestamp, and status transition.
- Audit records must be **tamper-evident** — no DELETE or UPDATE operations are permitted on audit log entries.
- Any contribution that weakens audit trail immutability will be rejected.

### Authentication & Authorization
- **Mutating endpoints require a JWT** (`POST /auth/token`, HS256, lifetime `JWT_EXPIRES_MINUTES`). The audit-trail `actor` is the verified token subject; a body `actor` must match it (otherwise 403) and the `X-Actor` header is ignored.
- **Roles:** `reviewer` (acknowledge, investigate, CAPA start/submit), `quality_manager` (also `close`), `admin` (everything, including `POST /cache/invalidate`). Closing is reserved for quality management.
- **Secret handling:** with `ENVIRONMENT=production|prod|staging` the API refuses to start unless `JWT_SECRET_KEY` is set to 32+ characters. In development an ephemeral secret is generated (with a warning). `render.yaml` generates the secret on deploy.
- **Read endpoints are intentionally public** (`/deviations`, `/summary`, `/capas`, `/audit-log`, `/metrics`, ...): the dataset is synthetic. A real deployment would also authenticate reads.
- **Rate limiting:** `slowapi` per client IP, process-local (100/min for reads, 30/min for review actions, 10/min for login and cache invalidation). Behind a proxy, configure forwarded-IP handling or limit at the proxy.
- Login attempts are not logged to `audit_log`, and `/auth/token` is excluded from the audit middleware so credentials can never be persisted.
- A production deployment of a system like this would still require:
  - An identity provider (OAuth 2.0 / SAML, MFA) instead of three hard-coded demo accounts
  - A documented access matrix, user lifecycle and periodic access reviews
  - Electronic signature controls per 21 CFR Part 11 §11.50

### Data Integrity (ALCOA+)
Contributions must preserve the following attributes of all records:

| Attribute | Meaning | Implementation |
|-----------|---------|----------------|
| **Attributable** | Who created/modified the record | `actor` field required on all audit events |
| **Legible** | Permanently readable | ISO 8601 timestamps; no ambiguous formats |
| **Contemporaneous** | Recorded at time of action | `created_at` set server-side, not client-supplied |
| **Original** | First capture preserved | Audit records are append-only |
| **Accurate** | Reflects what happened | Status transitions validated against allowed state machine |

### API Security
- No real credentials, PII, or proprietary data should ever be committed to this repository.
- Sample/seed data must use clearly fictional identifiers (e.g., `DEV-001`, `analyst-1`).
- Environment variables (database URLs, secret keys) must use `.env` files excluded via `.gitignore` — never hardcoded.

### Dependency Security
- Runtime dependencies are pinned in `requirements-prod.txt` (`requirements.txt` includes it); tooling is pinned in `requirements-dev.txt`.
- CI runs `ruff`, `mypy` (blocking), Bandit, `pip-audit`, `npm audit` and the test suite (85% coverage gate) with least-privilege workflow permissions.
- Contributors should run `pip-audit -r requirements-prod.txt` before submitting PRs that add or update dependencies.
- CI runs on every push; dependency vulnerabilities flagged by GitHub Dependabot will be treated as high priority.

---

## Known Limitations (Portfolio Context)

This project is a **portfolio demonstration** and does not implement the full security controls required for a production GxP system. Specifically:

- Authentication is a JWT demo with three synthetic accounts (PBKDF2 hashes in code); there is no user store, MFA, token revocation or account lockout beyond the per-IP rate limit
- No encryption at rest for the SQLite database
- No penetration testing has been performed

These limitations are intentional for scope management and are documented here for transparency. A real deployment would require a formal **Security Risk Assessment (SRA)** and inclusion in the system's **Validation Master Plan (VMP)**.

---

## Acknowledgments

Security researchers who responsibly disclose valid vulnerabilities will be acknowledged in `CHANGELOG.md` unless they request otherwise.
