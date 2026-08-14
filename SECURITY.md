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
- The current version uses a simplified actor model for portfolio demonstration purposes.
- A production deployment of a system like this would require:
  - Individual user authentication (e.g., OAuth 2.0 / SAML)
  - Role-based access control (RBAC) with documented access matrix
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
- Dependencies are pinned in `requirements.txt` and `requirements-dev.txt`.
- Contributors should run `pip audit` before submitting PRs that add or update dependencies.
- CI runs on every push; dependency vulnerabilities flagged by GitHub Dependabot will be treated as high priority.

---

## Known Limitations (Portfolio Context)

This project is a **portfolio demonstration** and does not implement the full security controls required for a production GxP system. Specifically:

- No real authentication layer (no user accounts or sessions)
- No encryption at rest for the SQLite database
- No penetration testing has been performed

These limitations are intentional for scope management and are documented here for transparency. A real deployment would require a formal **Security Risk Assessment (SRA)** and inclusion in the system's **Validation Master Plan (VMP)**.

---

## Acknowledgments

Security researchers who responsibly disclose valid vulnerabilities will be acknowledged in `CHANGELOG.md` unless they request otherwise.
