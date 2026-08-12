# Risk Rules and Review Controls

## Purpose

This portfolio prototype prioritizes synthetic deviation records for reviewer attention. It is advisory only: it does not approve, close, or make regulated quality decisions.

## Rule set

| Signal | Points | Rationale |
| --- | ---: | --- |
| High severity | 3 | Requires prompt visibility |
| Medium severity | 1 | Requires routine prioritization |
| Past due date | 3 | Indicates a timeliness concern |
| No owner assigned | 2 | Indicates accountability gap |
| Repeat occurrence | 2 | Indicates recurrence signal |
| Incomplete record | 2 | Indicates data-quality concern |

Scores of 5 or more are **High**, 2–4 are **Medium**, and 0–1 are **Low**. Every result returns its contributing reasons.

## Control evidence

- Synthetic source data is version controlled.
- Database constraints restrict severity and review-status values.
- Automated tests cover scoring, API response behavior, and missing records.
- GitHub Actions runs tests on pushes and pull requests.

## Limitations

Rules are intentionally simplified. Risk weights, thresholds, data sources, access controls, audit trails, and validation deliverables would require formal governance before production use.
