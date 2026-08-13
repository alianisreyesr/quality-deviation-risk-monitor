# Changelog

All notable changes to this project are documented in this file.

This project follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) conventions
and uses [Semantic Versioning](https://semver.org/).

> **Scope note:** This is a portfolio learning artifact using synthetic data.
> It is not validated software and must not be used for regulated quality decisions.

---

## [Unreleased]

### Planned
- Async database driver (`aiosqlite`) for concurrent request handling
- CORS whitelist configuration for deployment hardening

---

## [1.3.0] — 2026-08-13

Implements Issue #5 (Phase 3): data quality and governance controls.

### Added

#### Rule Versioning
- `SCORING_RULE_VERSION = "1.0.0"` constant in `app/scoring.py` — incremented whenever any rule weight, threshold, or tier boundary changes
- All `GET /deviations` and `GET /deviations/{id}` responses now include `scoring_rule_version` field, enabling full traceability from score to rule set
- `scoring_rule_version` added to `DeviationResponse` Pydantic model

#### Data Quality Endpoint
- `GET /data-quality` — returns per-field null counts, invalid value counts, null/invalid rates, issue_rate, and up to 5 sample invalid values per field; computed on-demand against live DB; rate-limited to 30/minute
- `app/data_quality.py` — field validation helper with `FIELD_SPECS` config covering all 9 deviation fields; validates allowed categorical values, date formats, boolean formats, and required field presence
- `app/data_quality_router.py` — FastAPI router registering the endpoint
- `DataQualityResponse` and `FieldQualityReport` Pydantic models added to `app/models.py`
- `investigation_owner` correctly treated as nullable (nulls not counted as issues)

#### Documentation
- `docs/data-dictionary.md` — full field reference for all 9 dataset fields plus 4 derived API fields; includes type, required status, allowed values, examples, and scoring impact; aligned with ALCOA+ *Complete* and *Accurate* criteria
- `docs/rule-change-template.md` — structured template for proposed changes, rationale, impact assessment, test evidence, approval placeholder, and implementation reference; mirrors a lightweight change-control process

#### Tests (`tests/test_data_quality.py` — 15 new tests)
- `GET /data-quality` response shape: top-level keys, field list, per-field keys, count/rate types
- All 9 expected fields present in report
- `issue_rate` mathematically consistent with `records_with_any_issue / total_records`
- `build_data_quality_report` unit tests with injected records: empty dataset, invalid severity, missing required field, clean record
- `scoring_rule_version` present and correct on list and detail responses

### Changed
- `app/main.py` — registers `data_quality_router`; app version bumped to `1.3.0`
- `app/scoring.py` — added `SCORING_RULE_VERSION` constant and `scoring_rule_version` key to returned dict; scoring logic unchanged (no rule version bump needed)

---

## [1.2.0] — 2026-08-13

Implements Issue #4: full reviewer workflow with state-transition validation, a per-deviation audit trail endpoint, and 20 new targeted tests.

### Added

#### State Transition Validation
- `ALLOWED_TRANSITIONS` map in `audit_router.py`
- HTTP **409 Conflict** with structured error body
- `TransitionRejectedResponse` Pydantic model

#### New Endpoint
- `GET /deviations/{deviation_id}/audit-trail`
- `AuditTrailResponse` Pydantic model

#### Tests (`tests/test_review_workflow.py` — 20 tests)

### Changed
- `audit_router.py` — transition validation before write
- `audit_db.py` — added `fetch_deviation_current_status`

---

## [1.0.0] — 2026-08-12

Initial public release.

### Added
- `GET /health`, `GET /deviations`, `GET /deviations/{id}`, `GET /summary`
- `POST /deviations/{id}/review`, `GET /audit-log`
- `POST /cache/invalidate`
- Immutable append-only audit trail (21 CFR Part 11 / ALCOA+)
- Rule-based risk scoring with explainable reasons
- 57 automated tests, GitHub Actions CI
- React reviewer dashboard
- Docker + docker-compose
- Full documentation suite

### Technical Stack

| Layer | Technology |
|-------|------------|
| API framework | FastAPI 0.115.6 |
| Validation | Pydantic 2.10.3 |
| Database | SQLite (synthetic data only) |
| Rate limiting | slowapi 0.1.9 |
| Testing | pytest 8.3.4 + httpx 0.28.1 |
| Frontend | Vite + React |
| CI | GitHub Actions |

---

## Version Policy

- `MAJOR` — breaking API changes
- `MINOR` — new backward-compatible features
- `PATCH` — bug fixes and documentation

[Unreleased]: https://github.com/alianisreyesr/quality-deviation-risk-monitor/compare/v1.3.0...HEAD
[1.3.0]: https://github.com/alianisreyesr/quality-deviation-risk-monitor/compare/v1.2.0...v1.3.0
[1.2.0]: https://github.com/alianisreyesr/quality-deviation-risk-monitor/compare/v1.0.0...v1.2.0
[1.0.0]: https://github.com/alianisreyesr/quality-deviation-risk-monitor/releases/tag/v1.0.0
