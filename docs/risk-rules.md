# Risk Rules — Explainability Document

## Purpose

This document describes each scoring rule applied by the Quality Deviation Risk Monitor. The design follows the principle that risk prioritization in regulated environments must be **explainable, auditable, and reviewer-accountable**. No rule produces a hidden or statistical result.

## Scoring model overview

The score is additive. Each rule contributes independently. The final risk level is derived from a threshold, not a black-box model.

| Condition | Points added | Reason tag returned |
|---|---|---|
| Severity = High | +3 | `High severity` |
| Severity = Medium | +1 | `Medium severity` |
| `due_date` is before today | +3 | `Past due date` |
| `investigation_owner` is empty or null | +2 | `No investigation owner assigned` |
| `repeat_occurrence` = True | +2 | `Repeat occurrence` |
| `record_complete` = False | +2 | `Required data is incomplete` |

## Risk level thresholds

| Score range | Risk level |
|---|---|
| 0 – 1 | Low |
| 2 – 4 | Medium |
| 5 or more | High |

## Design rationale

**Why rule-based, not ML-based?**  
In regulated quality contexts (GxP, 21 CFR Part 11), a qualified person must be able to trace *exactly* why a record was flagged. A machine learning model trained on historical records would produce scores that are difficult to validate, re-qualify after updates, or defend in an audit. Rule-based scoring is transparent, version-controllable, and maps directly to the ALCOA+ principle of *attributable* data.

**Why is the score advisory?**  
This prototype assigns a score and surface reasons — it does not close, escalate, or modify records. A human reviewer retains full accountability for all quality decisions. This reflects the human-in-the-loop control philosophy in validated systems.

**Why is `due_date` overdue weighted the same as High severity (+3)?**  
An unresolved High-severity deviation is operationally urgent. A record that is past its committed due date — regardless of severity — signals a control breakdown in the investigation timeline, which is equally critical from a regulatory posture standpoint.

## Future enhancements

- Field-level completeness checks (rather than a single `record_complete` flag)
- Days-overdue weighting (linear escalation beyond threshold)
- Recurrence window (flag only if recurred within N days)
- Audit-log of score snapshots for trending
