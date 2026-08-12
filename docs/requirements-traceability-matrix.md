# Requirements Traceability Matrix

## Purpose

This matrix connects the Quality Deviation Risk Monitor prototype’s intended requirements to planned verification and evidence. It is a portfolio-oriented artifact that demonstrates traceability-minded engineering. It does not constitute a formal validated-system traceability matrix.

## Traceability Matrix

| ID | Requirement | Risk if Unmet | Verification Method | Expected Evidence | Status |
| --- | --- | --- | --- | --- | --- |
| UR-001 | The application shall use synthetic deviation data only. | Confidential or regulated data could be exposed. | Data and repository review. | `data/` source files, documentation, and repository review. | Implemented / ongoing control |
| UR-002 | The application shall calculate a deterministic risk result from defined input rules. | Review priorities could be inconsistent or unexplained. | Unit testing and rule review. | Scoring tests and `docs/risk-rules.md`. | Implemented |
| UR-003 | The application shall expose deviation and risk information through an API. | The dashboard cannot access structured review data. | API testing. | API test results in `tests/`. | Implemented |
| UR-004 | The application shall provide a reviewer-oriented dashboard for the synthetic queue. | Users cannot efficiently inspect prototype results. | Manual UI verification. | Dashboard source, screenshot, or release verification note. | Implemented / manual evidence pending |
| UR-005 | The application shall persist prototype data locally. | The demonstration cannot reproduce an operational data flow. | Integration/API testing. | SQLite implementation and test results. | Implemented |
| UR-006 | The scoring approach shall be explainable. | A reviewer cannot understand why a record is prioritized. | Documentation and unit-test review. | `docs/risk-rules.md`, scoring tests, and UI/API evidence. | Implemented / enhancement ongoing |
| UR-007 | Core application behavior shall have automated test coverage. | Regressions may be introduced without detection. | Test-suite execution. | `tests/` and passing `pytest` output. | Implemented |
| UR-008 | Automated tests shall run on repository changes. | Changes may be merged without repeatable verification. | CI workflow review. | GitHub Actions workflow and successful runs. | Implemented |
| UR-009 | The project shall support consistent local execution. | Contributors may be unable to reproduce the demo environment. | Local/Docker verification. | `Dockerfile`, `docker-compose.yml`, and setup documentation. | Partially implemented |
| UR-010 | Synthetic demonstration data shall be reproducibly reset. | Demo results could vary across environments. | Reset test or documented verification procedure. | Reset command/script, test evidence, and setup guide. | Planned — Issue #3 |
| UR-011 | The project shall document intended use, scope, and limitations. | The prototype could be misrepresented as production-ready. | Documentation review. | `docs/validation-strategy.md` and `docs/portfolio-case-study.md`. | Implemented |
| UR-012 | Changes to critical behavior shall include rationale, tests, and documentation updates. | Rule and interface changes may lack traceability. | Pull-request and CI review. | Commit/PR history, test output, and documentation updates. | Ongoing control |

## Evidence Conventions

- **Implemented:** Evidence is expected to exist in the current repository and should be confirmed during release review.
- **Partially implemented:** A component exists, but acceptance evidence or supporting documentation remains incomplete.
- **Planned:** The requirement is approved for future implementation and linked to a tracked issue.
- **Ongoing control:** The requirement applies to every relevant change.

## Release Review Checklist

Before a portfolio release, verify that:

- Each implemented requirement has current evidence.
- Planned or partial items are clearly marked as limitations.
- Automated tests pass in GitHub Actions.
- Documentation matches the released behavior.
- No real, confidential, or credential-bearing data is present.

## Related Documentation

- `docs/implementation-plan.md`
- `docs/validation-strategy.md`
- `docs/risk-rules.md`
- `docs/architecture.md`
- `docs/portfolio-case-study.md`
