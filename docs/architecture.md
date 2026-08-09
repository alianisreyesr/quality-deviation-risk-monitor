# Architecture and Data Lineage

## Purpose

This document explains how synthetic records move through the portfolio prototype. It is intentionally lightweight and designed to make assumptions and rule decisions visible to a reviewer.

## Data flow

```text
[Synthetic CSV]
      |
      v
[FastAPI loader]
      |  validates expected fields
      v
[Explainable risk-scoring rules]
      |  severity + due date + owner + recurrence + completeness
      v
[API response]
      |  score + risk level + reasons + human review status
      v
[Reviewer / future UI]
```

## Control-oriented design choices

| Design choice | Why it matters |
| --- | --- |
| Synthetic source data | Keeps the public portfolio independent of employer information |
| Explicit field names | Supports traceability and consistent interpretation |
| Explainable rule output | Shows the reason for each risk signal rather than hiding logic in a black box |
| Human review status | Keeps prioritization advisory; a reviewer remains accountable for decisions |
| Version-controlled rules | Makes changes to scoring logic reviewable through Git history |

## Data-quality checks

The current prototype evaluates completeness by checking the `record_complete` field and assigns an additional risk signal when it is false. A future iteration can replace this simplified indicator with field-level validations and test evidence.

## Non-production scope

This is a learning and portfolio project. It is not validated software, does not manage real quality records, and should not be used to make regulated quality decisions.
