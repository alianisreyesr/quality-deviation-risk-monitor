# Portfolio Case Study: Quality Deviation Risk Monitor

## Executive Summary

Quality Deviation Risk Monitor is a portfolio-safe prototype that helps quality reviewers prioritize synthetic deviation records using transparent, rule-based risk scoring. The project demonstrates how data engineering, software development, and validation-minded controls can support a structured quality-review workflow in regulated environments.

The solution is intentionally designed as a prototype: it uses only synthetic data and is not a validated production system. It must not be used to make GMP/GxP decisions or to process real product, patient, batch, or proprietary quality records.

## The Problem

Quality teams may need to review a growing queue of deviation records while ensuring that higher-risk signals receive attention first. A simple chronological queue can hide the relative importance of issues involving product impact, recurrence, severity, missing investigations, or overdue actions.

This project explores a practical solution: transform structured deviation inputs into an explainable priority signal that supports—not replaces—human review.

## Intended User and Workflow

**Primary user:** A quality reviewer or quality-data analyst who needs to triage a synthetic deviation queue.

The intended workflow is:

1. Load a synthetic deviation dataset.
2. Apply deterministic risk rules to each record.
3. Present a score, risk tier, and explanation of the contributing factors.
4. Review and filter the queue to focus attention on higher-priority records.
5. Capture a reviewer decision and preserve traceable review evidence as the prototype evolves.

## Solution Architecture

The repository separates responsibilities across the following components:

| Component | Responsibility |
| --- | --- |
| React frontend | Provides a reviewer-oriented dashboard for viewing the risk queue. |
| FastAPI service | Exposes application data and risk results through an API. |
| SQLite | Stores prototype data locally for a lightweight, reproducible demo. |
| Scoring layer | Applies deterministic, explainable rules to calculate risk priorities. |
| Synthetic CSV dataset | Supplies portfolio-safe deviation scenarios without exposing confidential data. |
| Pytest and GitHub Actions | Automate regression testing on pushes and pull requests. |
| Docker / Docker Compose | Supports consistent local execution. |

## Risk-Scoring Approach

The project deliberately uses deterministic rules rather than an opaque predictive model. This choice makes the prioritization logic easier to inspect, test, and explain. A reviewer should be able to understand which input characteristics contributed to a risk tier without reading application source code.

This approach supports the following design goals:

- **Traceability:** connect a result to its input fields and applicable rules.
- **Explainability:** communicate why a record was prioritized.
- **Testability:** verify known scenarios and edge cases with automated tests.
- **Governance readiness:** create a foundation for documenting rule versions and controlled changes.

## Quality and Control Mindset

The prototype applies a quality-oriented engineering mindset:

- Synthetic data only; no real or confidential quality records.
- Clear separation between data access, models, scoring logic, API behavior, and user interface.
- Automated tests for key business logic and API behavior.
- Continuous integration that runs tests on repository changes.
- Documented architecture and risk-rule rationale.
- A phased implementation plan that defines acceptance criteria, validation-oriented evidence, and release readiness.

## Skills Demonstrated

| Area | Evidence in the Project |
| --- | --- |
| Backend engineering | FastAPI service, structured models, API design, SQLite integration. |
| Data engineering | Synthetic dataset management, structured data handling, risk prioritization logic. |
| Frontend development | React reviewer dashboard for operational decision support. |
| Testing and automation | Pytest coverage and GitHub Actions CI workflow. |
| DevOps fundamentals | Docker and Docker Compose configuration for consistent local execution. |
| Quality systems awareness | Explainable rules, traceability-oriented design, synthetic data controls, and validation-minded documentation. |
| Documentation | Architecture, risk-rule documentation, implementation roadmap, and this case study. |

## What This Project Does Not Claim

This repository does not claim GxP validation, production readiness, regulatory approval, or clinical/manufacturing decision authority. It is an educational and portfolio artifact designed to demonstrate thoughtful engineering practices relevant to quality-data and regulated-system roles.

## Roadmap

The next milestones are documented in `docs/implementation-plan.md` and focus on:

1. Reproducible local setup and deterministic synthetic-database reset.
2. Explainable reviewer workflow, queue filtering, and traceable review actions.
3. Data-quality controls, data dictionary, and risk-rule versioning.
4. Requirements traceability, validation strategy, and evidence-oriented testing.
5. Portfolio visuals, release checklist, and a tagged v1.0.0 release.

## Why It Matters

This project connects full-stack development with quality-data engineering: it turns synthetic operational data into an explainable, testable reviewer experience while acknowledging the controls and documentation expected in regulated settings. It is particularly relevant to entry-level roles involving Quality Data Engineering, Computer System Validation, data analytics, IT compliance, and automation in life sciences.

## Repository Guide

- `README.md` — project overview and run instructions.
- `docs/architecture.md` — technical architecture.
- `docs/risk-rules.md` — explanation of risk rules.
- `docs/implementation-plan.md` — phased roadmap and definition of done.
- `data/` — synthetic source data only.
- `tests/` — automated test coverage.
