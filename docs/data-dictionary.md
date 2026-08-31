# Data Dictionary — Synthetic Deviation Dataset

> **Scope note:** All records in this dataset are entirely synthetic and
> fictional. They do not represent real batches, products, sites, or
> quality events. This dictionary exists solely to demonstrate data-governance
> practices for portfolio purposes.

---

## Field Reference

### `deviation_id`

| Attribute | Value |
|-----------|-------|
| Type | String |
| Required | Yes |
| Max length | 50 characters |
| Format | Alphanumeric identifier, e.g. `DEV-0001` |
| Example | `DEV-0001` |
| Notes | Primary key. Unique per record. Never reused after deletion. |

---

### `title`

| Attribute | Value |
|-----------|-------|
| Type | String |
| Required | Yes |
| Max length | 255 characters |
| Example | `Cleaning validation protocol deviation — Line 3` |
| Notes | Human-readable description of the deviation event. |

---

### `severity`

| Attribute | Value |
|-----------|-------|
| Type | Categorical string |
| Required | Yes |
| Allowed values | `Low`, `Medium`, `High` |
| Example | `High` |
| Notes | Reflects the synthetic risk level assigned at event creation. Drives the severity component of the risk score (+3 for High, +1 for Medium, +0 for Low). |

---

### `opened_date`

| Attribute | Value |
|-----------|-------|
| Type | Date (ISO 8601: `YYYY-MM-DD`) |
| Required | Yes |
| Example | `2026-01-15` |
| Notes | Date the deviation was recorded. Must be ≤ `due_date`. |

---

### `due_date`

| Attribute | Value |
|-----------|-------|
| Type | Date (ISO 8601: `YYYY-MM-DD`) |
| Required | Yes |
| Example | `2026-03-15` |
| Notes | Target closure date. Records past this date receive +3 to risk score. |

---

### `investigation_owner`

| Attribute | Value |
|-----------|-------|
| Type | String (nullable) |
| Required | No |
| Max length | 100 characters |
| Example | `j.martinez` |
| Notes | Label identifying the person responsible for investigation. Null/empty means unassigned, which adds +2 to risk score. Not a real employee identifier. |

---

### `repeat_occurrence`

| Attribute | Value |
|-----------|-------|
| Type | Boolean |
| Required | Yes |
| Allowed values | `true`, `false` (also accepts `1`, `0`, `yes`, `no`) |
| Example | `false` |
| Notes | Indicates whether a similar deviation was recorded previously. A value of `true` adds +2 to risk score. |

---

### `record_complete`

| Attribute | Value |
|-----------|-------|
| Type | Boolean |
| Required | Yes |
| Allowed values | `true`, `false` (also accepts `1`, `0`, `yes`, `no`) |
| Example | `true` |
| Notes | Indicates whether all required supporting documentation has been attached. `false` adds +2 to risk score. Supports ALCOA+ *Complete* criterion. |

---

### `review_status`

| Attribute | Value |
|-----------|-------|
| Type | Categorical string |
| Required | Yes |
| Allowed values | `Open`, `Under Review`, `Investigation In Progress`, `Closed` |
| Example | `Open` |
| Notes | Current workflow state. Transitions are validated by the reviewer API (see `app/audit_router.py`). `Closed` is a terminal state. |

---

## Derived Fields (API-only, not stored in DB)

| Field | Type | Description |
|-------|------|-------------|
| `risk_score` | Integer ≥ 0 | Sum of all rule contributions. |
| `risk_level` | `Low` / `Medium` / `High` | High ≥ 5 pts, Medium 2–4 pts, Low 0–1 pts. |
| `risk_reasons` | List\[str\] | Human-readable list of triggered rules. |
| `scoring_rule_version` | String | Semver version of the rule set used to produce this score. |

---

## Data Quality Expectations

- `deviation_id`, `title`, `severity`, `opened_date`, `due_date`,
  `repeat_occurrence`, `record_complete`, and `review_status` must never be null.
- `investigation_owner` is intentionally nullable; null records represent
  unassigned deviations and are a valid data quality signal (not a data error).
- All categorical fields are validated against their allowed-value sets by
  `GET /data-quality` and by Pydantic models at the API boundary.
- `deviation_id` must be unique — `GET /data-quality` flags every record
  sharing a duplicated ID, not just the extras.

---

## Field Reference — Synthetic CAPA Dataset (`capas`)

> Same scope note as above: every CAPA record is entirely synthetic.

### `capa_id`

| Attribute | Value |
|-----------|-------|
| Type | String |
| Required | Yes |
| Notes | Primary key. Unique per record — duplicates are flagged by `GET /capas/data-quality`. |

### `deviation_id`

| Attribute | Value |
|-----------|-------|
| Type | String (nullable) |
| Required | No |
| Notes | Links a CAPA back to the deviation that triggered it. Null means the CAPA was raised independently (e.g. from a trend review), not from a single deviation. |

### `capa_type`

| Attribute | Value |
|-----------|-------|
| Type | Categorical string |
| Required | Yes |
| Allowed values | `Corrective`, `Preventive` |

### `severity`

Same allowed values and scoring role as the deviation `severity` field
(`Low` / `Medium` / `High`).

### `root_cause`

| Attribute | Value |
|-----------|-------|
| Type | String (nullable) |
| Required | No |
| Notes | Free-text root-cause category (e.g. `Training Gap`, `Equipment Failure`). Null/empty adds +1 to the CAPA risk score (incomplete investigation) and is bucketed as `Unspecified` in `GET /metrics` and `fact_capa_lifecycle`. |

### `opened_date` / `due_date` / `closure_date`

| Attribute | Value |
|-----------|-------|
| Type | Date (ISO 8601) |
| Required | `opened_date` and `due_date` yes; `closure_date` no |
| Notes | `closure_date` is set only once a CAPA reaches `Closed` status. `aging_days` freezes at `closure_date − opened_date` once closed; while open it is `today − opened_date`. |

### `owner`

| Attribute | Value |
|-----------|-------|
| Type | String (nullable) |
| Required | No |
| Notes | Null while open adds +2 to the risk score (unassigned CAPA). Not penalized once closed. |

### `recurrence_flag`

| Attribute | Value |
|-----------|-------|
| Type | Boolean |
| Required | Yes |
| Notes | `true` means the root cause matches a prior CAPA — a systemic-failure signal. Adds +2 to risk score. |

### `effectiveness_check_complete`

| Attribute | Value |
|-----------|-------|
| Type | Boolean |
| Required | Yes |
| Notes | A CAPA `Closed` with this still `false` adds +2 to risk score — closing without verifying effectiveness is a data-integrity gap, not just a process nicety. |

### `status`

| Attribute | Value |
|-----------|-------|
| Type | Categorical string |
| Required | Yes |
| Allowed values | `Open`, `In Progress`, `Pending Effectiveness Check`, `Closed` |

## Derived Fields — CAPA (API-only)

| Field | Type | Description |
|-------|------|--------------|
| `aging_days` | Integer ≥ 0 | Days open, or days-to-close once closed. |
| `risk_score` / `risk_level` / `risk_reasons` | — | Same shape as deviations, produced by `app/capa_scoring.py`. |
| `scoring_rule_version` | String | Version of the **CAPA** rule set (`CAPA_SCORING_RULE_VERSION`) — independent of the deviation rule version. |

See [risk rules and controls →](risk-rules.md) for the full CAPA rule set.

---

> Last updated: 2026-08-31  
> Maintained by: portfolio owner  
> This dictionary must be updated whenever field definitions, allowed values,
> or scoring rules change.
