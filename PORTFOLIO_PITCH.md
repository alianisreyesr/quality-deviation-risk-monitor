# Pharma Data Engineering Portfolio

**Alianis Reyes-Reyes** · Information Systems @ UPRM (Dec 2026) · Eli Lilly Tech@Lilly Alumni

[LinkedIn](https://www.linkedin.com/in/alianis-reyes-reyes/) · [GitHub](https://github.com/alianisreyesr)

---

> Six production-pattern repositories demonstrating GxP-relevant data engineering across the full regulated software lifecycle — validation, traceability, audit trail, explainability, and CI-enforced quality gates. All data is synthetic. No proprietary information, employer data, or regulated artifacts are included.

---

## Why This Portfolio Exists

Pharma quality and IT compliance roles ask for engineers who understand **why** traceability matters, not just how to build pipelines. These projects are built around that question: *how do you surface the right record, at the right time, with full traceability, in a regulated environment?*

Every project maps directly to skills listed in Quality Data Engineer, CSV Analyst, IT Compliance, and Data Engineering JDs — with explicit regulatory citations (FDA 21 CFR Part 11, EU GMP Annex 11, MHRA, PIC/S, GAMP 5, FDA CSA Guidance).

---

## Regulated Portfolio Ecosystem

### 1 · [Quality Deviation Risk Monitor](https://github.com/alianisreyesr/quality-deviation-risk-monitor)
**Stack:** Python · FastAPI · Pydantic v2 · SQLite · React · Vite · Docker · GitHub Actions

Full-stack deviation prioritization system with explainable risk scoring and a 21 CFR Part 11-aligned audit trail.

**Key signals for JD matching:**
- `AuditMiddleware` logs every mutating HTTP request to an append-only `audit_log` table — UTC server-generated timestamps, never client-supplied (ALCOA+ Contemporaneous)
- `contributing_reasons[]` in every API response — reviewers evaluate, not blindly accept, algorithmic output (GAMP 5 Category 4 defensibility)
- Rate limiting (SlowAPI), structured error handling, OpenAPI docs auto-generated
- **112 tests · 10 modules · CI coverage gate ≥70%**

---

### 2 · [CSV Evidence Tracker](https://github.com/alianisreyesr/csv-evidence-tracker)
**Stack:** Python · FastAPI · SQLite · React · Vite · Docker · GitHub Actions

Requirements traceability matrix with IQ/OQ/PQ test execution and a tamper-evident audit trail.

**Key signals for JD matching:**
- RTM linking system requirements → test cases → execution evidence → sign-off (CSV lifecycle end-to-end)
- IQ/OQ/PQ protocol execution with pass/fail/blocked states and deviation logging
- Every test execution appends an immutable audit row — traceability from requirement to evidence
- **CI: Backend + Frontend + Docker smoke test + CodeQL**

---

### 3 · [GxP Change Control](https://github.com/alianisreyesr/gxp-change-control)
**Stack:** Python · FastAPI · Pydantic v2 · SQLite · React · Vite · TypeScript · Docker · GitHub Actions

Controlled change lifecycle: request → impact assessment → approval workflow → implementation → closure.

**Key signals for JD matching:**
- Multi-stage approval workflow with electronic signature fields (21 CFR Part 11 alignment)
- Risk classification and impact assessment forms before change approval
- Bandit (Python SAST) + pip-audit + npm audit + TypeScript typecheck in CI — production-grade security posture
- **68 tests · CI coverage gate ≥70% · release.yml · sonar.yml**

---

### 4 · [GxP Batch Data Pipeline](https://github.com/alianisreyesr/gxp-batch-data-pipeline)
**Stack:** Python · DuckDB · dbt · GitHub Actions

Traceable batch manufacturing data pipeline: synthetic telemetry → quality gates → OOS detection → reproducible run evidence.

**Key signals for JD matching:**
- Deterministic pipeline with source SHA-256, run ID derived from hash, and machine-readable run manifest — full data lineage
- Explicit quarantine of rejected records with machine-readable reasons (data quality decision traceability)
- Rule-based OOS evaluation with rule ID, observed value, expected range, batch, phase, and timestamp
- dbt staging + mart models + 8 dbt data tests
- **CI gate ≥80% · deterministic manifest assertions in CI · CI artifact upload of run evidence**

---

### 5 · [Data Integrity Case File](https://github.com/alianisreyesr/data-integrity-case-file)
**Stack:** Python · FastAPI · SQLite · React · Vite · GitHub Actions

ALCOA+ data integrity investigation workflow with CAPA readiness and local AI-assisted triage.

**Key signals for JD matching:**
- ALCOA+ principle enforcement at schema and API layer: Attributable, Legible, Contemporaneous, Original, Accurate
- CAPA lifecycle management with root cause, corrective action, and effectiveness check
- Local AI triage (no external API calls, data boundary maintained)
- **CI: Backend + Frontend + pip-audit + npm audit + coverage gate ≥70%**

---

### 6 · [CSA Assurance Planner](https://github.com/alianisreyesr/csa-assurance-planner)
**Stack:** Python · FastAPI · SQLite · React · Vite · GitHub Actions

Risk-based software assurance planning aligned to FDA CSA Guidance (2022) and GAMP 5.

**Key signals for JD matching:**
- Assurance planning tool that maps system criticality → intended use → category → testing approach (CSA risk-proportionate framework)
- FDA CSA Guidance alignment: critical thinking over checkbox compliance
- **CI: Backend + Frontend + pip-audit + coverage gate ≥70%**

---

## Skills Matrix — JD Alignment

| Skill | Where Demonstrated |
|---|---|
| **SQL / Data pipelines** | Batch Pipeline (DuckDB + dbt), all SQLite-backed APIs |
| **Python / FastAPI** | All 6 repos — Pydantic v2, structured error handling, middleware |
| **21 CFR Part 11 / Audit Trail** | Deviation Monitor, Change Control, CSV Tracker |
| **ALCOA+ / Data Integrity** | Data Integrity Case File, Deviation Monitor |
| **CSV / IQ/OQ/PQ** | CSV Evidence Tracker |
| **GAMP 5 / CSA** | CSA Assurance Planner, Deviation Monitor |
| **Explainability / Risk scoring** | Deviation Monitor (`contributing_reasons[]`) |
| **dbt / Analytical engineering** | Batch Pipeline |
| **Docker / CI/CD** | All 6 repos — multi-job pipelines, coverage gates, SAST |
| **React / TypeScript / Vite** | Deviation Monitor, Change Control, Data Integrity Case File, CSA Planner |
| **Security (SAST)** | Change Control (Bandit + pip-audit + npm audit), all repos (CodeQL) |
| **Testing** | 200+ tests across ecosystem · coverage gates 70–80% |

---

## Target Roles

| Priority | Role | Why It Fits |
|---|---|---|
| 1 | Quality Data Engineer / CSV Analyst (Pharma) | All 6 repos built around this JD |
| 2 | Data Engineer / Analytics Engineer (Entry-level) | Batch Pipeline, FastAPI REST, dbt |
| 3 | IT Audit / Compliance / GRC | Change Control, CSA Planner, audit trail pattern |
| 4 | Business Intelligence / Power BI | SQL foundation, data quality, pipeline patterns |
| 5 | Automation Analyst | CI/CD pipelines, API automation, Docker |

**Target companies:** Eli Lilly (Indiana) · Amgen (Juncos, PR) · Pfizer · Roche · J&J · Novartis · Medtronic · Onebridge · Moser Consulting

---

## Differentiators

- **Eli Lilly alumni (Tech@Lilly / OcyonBio)** — worked inside a regulated pharma environment; understands real GxP constraints, not just the theory
- **Regulatory depth** — every project cites specific FDA, MHRA, PIC/S, EU GMP guidance; not generic "compliance-aware"
- **Full-stack + pipeline** — FastAPI backend, React frontend, dbt transformations, Docker, CI/CD; covers data engineering AND quality systems
- **CI-enforced quality** — coverage gates, SAST, dependency audits on every push; demonstrates production engineering discipline
- **December 2026 graduation** — available for full-time roles starting Jan 2027; available for co-ops / internships immediately

---

*Every iteration of this portfolio is a question: what would make this more trustworthy, more traceable, more useful in a real regulated environment? That question doesn't have a final answer — and that's exactly what keeps it interesting.*
