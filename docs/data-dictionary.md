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

---

> Last updated: 2026-08-13  
> Maintained by: portfolio owner  
> This dictionary must be updated whenever field definitions, allowed values,
> or scoring rules change.
