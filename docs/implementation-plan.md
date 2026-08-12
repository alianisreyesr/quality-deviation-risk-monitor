# Quality Deviation Risk Monitor — Implementation Plan

## 1. Purpose

This repository is a portfolio-safe prototype for prioritizing synthetic quality-deviation records through transparent, rule-based risk scoring. It demonstrates an engineering approach suitable for regulated quality environments: traceable inputs, explainable decisions, validation-oriented testing, and reviewer-facing workflows.

**Important:** This application is not a validated production system, does not process real patient, product, batch, or proprietary quality data, and must not be used to make GMP/GxP decisions.

## 2. Current Baseline

The current baseline includes:

- FastAPI service with SQLite persistence and Pydantic models
- Synthetic deviation dataset and rule-based risk scoring
- React reviewer dashboard
- Docker and Docker Compose configuration
- Pytest coverage and GitHub Actions execution on pushes and pull requests
- Architecture and risk-rule documentation

## 3. Product Goal

Enable a quality reviewer to ingest or inspect synthetic deviations, understand why each record receives a risk score, filter the review queue, and record a review decision with a traceable audit event.

## 4. Delivery Principles

- Keep all datasets synthetic and portfolio-safe.
- Prefer deterministic, explainable rules over opaque predictions.
- Preserve provenance: each score must show its contributing rules and input values.
- Treat validation evidence, test results, and documentation as first-class deliverables.
- Make small, reviewable pull requests with clear acceptance criteria.

## 5. Phased Roadmap

### Phase 1 — Stabilize the Current MVP

**Objective:** Confirm that the existing API, dashboard, scoring behavior, and container setup work consistently.

**Work items:**

1. Document local setup, Docker setup, environment variables, and test commands in the README.
2. Add a health endpoint and a lightweight smoke test for the API.
3. Verify API error responses for invalid payloads, missing records, and unsupported query parameters.
4. Ensure the dashboard handles empty, loading, and API-error states.
5. Add a reproducible seed/reset command for the synthetic SQLite database.

**Acceptance criteria:**

- A new contributor can run the application and tests from documented commands.
- CI passes on a clean clone.
- The API returns structured errors and the UI does not fail silently.
- The demo dataset can be reset deterministically.

### Phase 2 — Explainable Risk Review Workflow

**Objective:** Make every prioritization decision auditable and understandable to a reviewer.

**Work items:**

1. Expose per-rule score contributions, risk tier, and human-readable rationale in the API.
2. Add a deviation-detail view showing source fields, scoring evidence, and recommended review priority.
3. Add queue filters for risk tier, status, site, product, and date range.
4. Add reviewer actions: acknowledge, investigate, close, and add a decision comment.
5. Store each action as an immutable audit-event record containing timestamp, actor label, action, record ID, and before/after status.

**Acceptance criteria:**

- A reviewer can explain a score without reading source code.
- Filtered queue results match API results.
- Review actions create traceable audit events.
- Tests cover high-, medium-, and low-risk scenarios plus invalid state transitions.

### Phase 3 — Data Quality and Governance Controls

**Objective:** Demonstrate disciplined handling of data quality and rule governance.

**Work items:**

1. Define a synthetic data dictionary: field names, definitions, allowed values, and example values.
2. Add input validation rules for required fields, dates, categories, and numeric ranges.
3. Add a data-quality summary endpoint for missing values, invalid records, and dataset totals.
4. Version risk-rule configurations and include the version used for every score.
5. Document rule-change review: proposed change, rationale, test evidence, approval placeholder, and implementation reference.

**Acceptance criteria:**

- Every dataset field is documented.
- Invalid records are rejected or clearly flagged.
- A score can be traced to a rule version.
- Rule changes have a documented review template.

### Phase 4 — Validation-Oriented Evidence

**Objective:** Package the project as a credible quality-data engineering portfolio artifact.

**Work items:**

1. Add a requirements traceability matrix linking user needs, functional requirements, tests, and evidence.
2. Create a concise validation strategy covering intended use, scope, risk assessment, testing, and limitations.
3. Add API contract tests and end-to-end tests for the main reviewer flow.
4. Capture test evidence in CI artifacts or a documented test-results template.
5. Add a release checklist covering version, tests, documentation, dependency review, and known limitations.

**Acceptance criteria:**

- Each core requirement maps to at least one test.
- The repository states what has and has not been validated.
- A reviewer can follow evidence from requirement to test outcome.

### Phase 5 — Portfolio Presentation

**Objective:** Make the project easy for recruiters and hiring managers to evaluate quickly.

**Work items:**

1. Add screenshots or a short GIF of the reviewer dashboard using synthetic data.
2. Create a one-page architecture diagram showing frontend, API, database, scoring layer, and CI.
3. Add a short business case: the quality-review problem, system workflow, controls, and measured demo outcomes.
4. Publish a tagged `v1.0.0` release after Phases 1–4 acceptance criteria are met.
5. Prepare a LinkedIn/GitHub portfolio description focused on Quality Data Engineering, CSV, GxP awareness, FastAPI, SQL, and automated testing.

**Acceptance criteria:**

- A visitor understands the project’s value in under two minutes.
- The repository contains clear visuals, an architecture overview, and limitations.
- The release is reproducible and tagged.

## 6. Suggested Issue Sequence

Create one issue per work item and use the following order:

1. Document setup and reproducible database reset.
2. Add API health check, smoke test, and error-handling tests.
3. Implement score explanations and deviation detail view.
4. Implement filters and review-status workflow.
5. Add immutable audit events and tests.
6. Add data dictionary, validation, and data-quality summary.
7. Add rule versioning and change-control template.
8. Add traceability matrix and validation strategy.
9. Add contract/end-to-end tests and release checklist.
10. Add portfolio visuals and create `v1.0.0`.

## 7. Definition of Done

A feature is complete only when:

- The intended behavior and acceptance criteria are documented.
- Automated tests cover the normal path and relevant failure paths.
- Documentation is updated when behavior, data, rules, or interfaces change.
- CI passes.
- No real or confidential data, secrets, or regulated operational records are committed.
- The pull request clearly states the purpose, tests run, and any limitations.

## 8. Immediate Next Step

Start with **Phase 1, Work Item 1: document local/Docker setup and a deterministic synthetic database reset**. This creates a reliable foundation before expanding workflow functionality or validation evidence.
