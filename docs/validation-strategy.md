# Validation Strategy

## Purpose

This document defines a validation-minded approach for the Quality Deviation Risk Monitor portfolio prototype. It describes intended use, scope, verification evidence, release expectations, and limitations. It is educational and does not establish a validated state for a production GxP system.

## Intended Use

The application demonstrates how synthetic quality-deviation records can be prioritized using transparent, deterministic risk rules. It supports learning, demonstrations, code review, and portfolio evaluation.

## Scope and Boundaries

In scope: synthetic data, rule-based scoring, API behavior, dashboard workflow, automated tests, Docker-based local execution, and CI evidence.

Out of scope: real or confidential data, GMP/GxP decisions, production use, regulatory-compliance claims, electronic signatures, authentication, and production audit-trail controls.

## Risk-Based Verification

| Risk Area | Verification | Evidence |
| --- | --- | --- |
| Risk scoring | Unit tests for expected tiers and edge cases | Passing scoring tests |
| API behavior | Tests for success, invalid input, and missing records | Passing API tests |
| Synthetic data | Source-data and deterministic-reset checks | Documented procedure and test evidence |
| Reviewer experience | Manual checks for result, empty, loading, and error states | Release verification note or screenshot |
| Change control | Pull-request review and CI | Passing GitHub Actions run |

## Change Expectations

Changes to rules, data structures, API contracts, or reviewer workflow should include a documented rationale, updated tests, relevant documentation updates, a passing CI run, and known limitations.

## Release Readiness

A portfolio release is ready when automated tests pass in CI; no real, confidential, or credential-bearing data is committed; core behavior and limitations are documented; and the primary dashboard workflow has been manually reviewed.

## Known Limitations

- This is a synthetic-data portfolio prototype, not a production quality system.
- Rules are illustrative and do not represent approved quality procedures.
- SQLite is not designed here for production scale, access control, or regulated-record retention.
- Formal validation deliverables, QA approval, and production qualification are not included.

## Related Documentation

- `docs/architecture.md`
- `docs/risk-rules.md`
- `docs/implementation-plan.md`
- `docs/portfolio-case-study.md`
