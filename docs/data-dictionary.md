# Synthetic Data Dictionary

## Dataset boundary

`data/deviations.csv` is a small synthetic dataset created solely for portfolio demonstration. It does not represent any real manufacturing site, product, batch, patient, deviation record, employee, or organization.

## Data-handling principles

- Do not replace the sample dataset with confidential, personal, patient, batch, or proprietary data.
- Treat the values as illustrative test data, not as validated operational records.
- Any real-world data pipeline would need approved governance, access controls, retention rules, integrity checks, and documented validation.

## Field guide

The dataset and API expose deviation attributes used to demonstrate filtering and risk prioritization. Field names, permitted values, and implementation details should be verified against `data/deviations.csv`, `sql/schema.sql`, and `app/main.py` when extending the project.

| Field category | Purpose in the prototype | Example use |
| --- | --- | --- |
| Deviation identifier | Distinguishes a synthetic record | API lookup and UI table key |
| Date/timestamp | Indicates when the synthetic event was recorded | Trend or aging views |
| Site/area | Represents an illustrative operational location | Grouping and filtering |
| Process/category | Represents an illustrative quality domain | Pattern review |
| Severity | Represents an illustrative impact tier | Risk-prioritization input |
| Status | Represents a synthetic workflow state | Review-queue filtering |
| Recurrence/count signal | Represents repeat-event context where modeled | Risk-prioritization input |
| Risk score/priority | System-generated decision-support output | Sort order for reviewer attention |

## Data lineage

```text
Synthetic CSV record
  → load/transform logic
  → SQL-aligned representation
  → FastAPI response
  → React dashboard display
```

## Data integrity note

The project demonstrates awareness of data-integrity principles such as attributable, legible, contemporaneous, original, and accurate (ALCOA+) records. It does not implement the technical and procedural controls required to claim ALCOA+ conformance in a regulated production environment.
