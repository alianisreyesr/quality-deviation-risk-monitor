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

## CAPA rule set (`app/capa_scoring.py`, version 1.0.0)

CAPA (Corrective and Preventive Action) records use a parallel, independently
versioned rule set — `CAPA_SCORING_RULE_VERSION` — so CAPA scoring can evolve
without changing deviation scoring, and vice versa.

| Signal | Points | Rationale |
| --- | ---: | --- |
| High severity | 3 | Highest regulatory exposure |
| Medium severity | 1 | Requires routine prioritization |
| Past due date (not yet closed) | 3 | Indicates a timeliness concern |
| No CAPA owner assigned (not yet closed) | 2 | Indicates accountability gap |
| Recurring root cause | 2 | Signals a systemic, not isolated, failure |
| Missing root cause | 1 | Incomplete investigation record |
| Closed without a completed effectiveness check | 2 | A closure with unverified effectiveness is a data-integrity and compliance gap |
| Open more than 60 days | 2 | Aging signal — a stalled corrective action |
| Open more than 30 days (and ≤ 60) | 1 | Early aging signal |

Scores of 5 or more are **High**, 2–4 are **Medium**, and 0–1 are **Low** — the
same thresholds used for deviations, so risk levels are comparable across
both record types in `GET /metrics`.

### Aging

`aging_days` is returned on every CAPA response:

- While a CAPA is open, it is `today − opened_date`.
- Once a CAPA is closed, it freezes at `closure_date − opened_date` (time to
  close), so historical aging stays meaningful after closure instead of
  continuing to grow.

Aging tiers (30 / 60 days) are named constants in `app/capa_scoring.py` —
`docs/rule-change-template.md` and tests reference the same constants rather
than re-deriving the thresholds.

## Limitations

Rules are intentionally simplified. Risk weights, thresholds, data sources, access controls, audit trails, and validation deliverables would require formal governance before production use.
