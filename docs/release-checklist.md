# Portfolio Release Checklist

Use this checklist before publishing a portfolio release or creating a version tag. This checklist supports repeatable engineering practice; it does not establish a validated production release.

## 1. Scope and Version

- [ ] Release purpose and intended audience are documented.
- [ ] Version number and release date are selected.
- [ ] Completed work, known limitations, and deferred work are recorded.
- [ ] The release does not claim production readiness, GxP validation, or regulatory approval.

## 2. Code and Tests

- [ ] The automated test suite passes locally or in the approved CI workflow.
- [ ] GitHub Actions shows a successful run for the release commit.
- [ ] Core scoring behavior and API behavior have relevant automated test coverage.
- [ ] New or changed functionality includes failure-path tests where applicable.
- [ ] No unresolved merge conflicts, debug-only changes, or unused experimental files remain.

## 3. Data and Security

- [ ] All committed records are synthetic and portfolio-safe.
- [ ] No patient, product, batch, proprietary, or confidential quality data is present.
- [ ] No passwords, tokens, API keys, private connection strings, or other secrets are committed.
- [ ] `.gitignore` appropriately excludes local databases, environment files, and generated artifacts.
- [ ] Dependencies and container configuration are reviewed for obvious issues.

## 4. Documentation

- [ ] README accurately describes the current application and setup.
- [ ] Architecture and risk-rule documents match implemented behavior.
- [ ] `docs/implementation-plan.md` reflects completed and planned work.
- [ ] `docs/validation-strategy.md` states intended use, boundaries, and limitations.
- [ ] `docs/requirements-traceability-matrix.md` is updated with current evidence status.
- [ ] `docs/portfolio-case-study.md` clearly explains the project’s value and skills demonstrated.

## 5. Reviewer Experience

- [ ] The primary reviewer workflow has been manually checked.
- [ ] Dashboard result, loading, empty, and error states have been reviewed.
- [ ] Screenshots or a short demo artifact use synthetic data only.
- [ ] Key risk results are understandable without reading source code.

## 6. Release Decision

- [ ] All blocking items are complete or formally deferred.
- [ ] Known limitations are visible in the release notes or documentation.
- [ ] A release tag is created only after this checklist is complete.
- [ ] Release notes summarize functionality, evidence, and limitations.

## Release Record

| Field | Value |
| --- | --- |
| Version |  |
| Release date |  |
| Release owner |  |
| CI run / evidence |  |
| Key changes |  |
| Known limitations |  |
| Approval / review note |  |
