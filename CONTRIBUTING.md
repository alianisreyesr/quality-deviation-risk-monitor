# Contributing to Quality Deviation Risk Monitor

Thank you for your interest in contributing! This project simulates a **GxP-regulated quality system**, so contributions must meet a higher bar than a typical open-source project — documentation, traceability, and test coverage are non-negotiable.

---

## Table of Contents

- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Commit Convention](#commit-convention)
- [Testing Requirements](#testing-requirements)
- [Validation & GxP Considerations](#validation--gxp-considerations)
- [Pull Request Checklist](#pull-request-checklist)
- [Code of Conduct](#code-of-conduct)

---

## Getting Started

### Prerequisites

- Python 3.11+
- Docker & Docker Compose (optional but recommended)
- Node.js 18+ (for the React dashboard)

### Local Setup

```bash
# 1. Clone the repo
git clone https://github.com/alianisreyesr/quality-deviation-risk-monitor.git
cd quality-deviation-risk-monitor

# 2. Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# 4. Run the API
uvicorn app.main:app --reload

# 5. (Optional) Run with Docker
docker compose up --build
```

The API will be available at `http://127.0.0.1:8000`. Interactive docs at `/docs`.

---

## Development Workflow

1. **Fork** the repository and create a feature branch from `main`:
   ```bash
   git checkout -b feat/your-feature-name
   ```
2. Make your changes with adequate test coverage (see [Testing Requirements](#testing-requirements)).
3. Run the full test suite locally before pushing:
   ```bash
   pytest --cov=app --cov-report=term-missing
   ```
4. Open a Pull Request against `main` with a clear description.

---

## Commit Convention

This project follows [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(scope): short description

[optional body]
[optional footer]
```

| Type | When to use |
|------|-------------|
| `feat` | New feature or endpoint |
| `fix` | Bug fix |
| `docs` | Documentation only |
| `test` | Adding or updating tests |
| `refactor` | Code change with no functional impact |
| `chore` | Build, CI, or dependency updates |
| `validation` | Changes to risk rules, scoring logic, or audit trail behavior |

**Example:**
```
feat(api): add /deviations/export endpoint for CSV download

Exports filtered deviation records as CSV per ALCOA+ traceability
requirements. Includes deviation_id, risk_level, review_status,
and audit timestamps.
```

---

## Testing Requirements

- All new features must include **unit tests** in `tests/`.
- Minimum acceptable coverage for modified modules: **80%**.
- Tests must pass in CI before a PR can be merged.
- If you add or modify a **risk scoring rule**, you must also update `docs/risk-rules.md` and add a corresponding test case in `tests/test_risk_engine.py`.

Run tests:
```bash
pytest                        # run all tests
pytest tests/test_models.py   # run a specific module
pytest --cov=app              # with coverage report
```

---

## Validation & GxP Considerations

This project is designed to mirror a **CSV (Computer System Validation)** environment under **21 CFR Part 11** and **GAMP 5** principles. Contributions touching the following areas require extra care:

| Area | Requirement |
|------|-------------|
| Risk scoring rules (`app/risk_engine.py`) | Document the change rationale in `docs/risk-rules.md` and reference the GAMP 5 risk category |
| Audit trail (`app/audit_models.py`, `app/audit_logger.py`) | Preserve ALCOA+ attributes: Attributable, Legible, Contemporaneous, Original, Accurate |
| State machine (`review_status` transitions) | Update the transition table in `docs/architecture.md` if transitions change |
| API contracts | Do not introduce breaking changes to existing endpoints without a versioned route (`/v2/...`) |

If you are unsure whether a change affects the validation scope, open an Issue first and tag it `question` + `validation`.

---

## Pull Request Checklist

Before requesting review, confirm:

- [ ] Tests pass locally (`pytest`)
- [ ] No decrease in code coverage
- [ ] Relevant documentation updated (`README`, `docs/`, `CHANGELOG.md`)
- [ ] Commit messages follow the Conventional Commits format
- [ ] No hardcoded secrets, credentials, or PII in the diff
- [ ] If risk rules changed → `docs/risk-rules.md` updated
- [ ] If audit trail changed → ALCOA+ compliance verified

---

## Code of Conduct

This project follows the [Contributor Covenant Code of Conduct](https://www.contributor-covenant.org/version/2/1/code_of_conduct/). By contributing, you agree to uphold a respectful and inclusive environment.

For questions or to report issues, open a GitHub Issue or contact the maintainer via the repository profile.
