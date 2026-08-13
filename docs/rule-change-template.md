# Rule Change Review Template

> Use this template for every change to `app/scoring.py`, `app/data_quality.py`
> (field validation rules), or any document that defines data quality thresholds.
> Complete all sections before merging. Leave placeholder text where approval
> processes are not implemented (portfolio artifact).

---

## Rule Change Record

| Field | Value |
|-------|-------|
| **Change ID** | RC-YYYY-NNN |
| **Date** | YYYY-MM-DD |
| **Author** | *(GitHub username)* |
| **Reviewer** | *(placeholder — not a regulated approval)* |
| **Affected module** | `app/scoring.py` / `app/data_quality.py` / other |
| **Rule version before** | X.Y.Z |
| **Rule version after** | X.Y.Z |
| **SCORING_RULE_VERSION bump** | Yes / No |

---

## 1. Proposed Change

*Describe the specific rule being added, modified, or removed. Include the
exact constant, threshold, or allowed-value set being changed.*

**Before:**
```python
# Example
if severity == "High":
    score += 3
```

**After:**
```python
# Example
if severity == "High":
    score += 4
```

---

## 2. Rationale

*Explain why this change is needed. Reference the data observation, portfolio
learning objective, or design principle that motivates the change.*

---

## 3. Impact Assessment

| Question | Answer |
|----------|--------|
| Which records will have their `risk_score` or `risk_level` change? | *(describe)* |
| Will any currently-High records drop to Medium or Low? | Yes / No |
| Will any currently-Low records rise to High? | Yes / No |
| Does this change the `SCORING_RULE_VERSION`? | Yes / No |
| Are downstream consumers (API clients, dashboard, tests) affected? | Yes / No |

---

## 4. Test Evidence

*List the test cases that cover the changed rule. All tests must pass before
merging. Include the pytest command and output summary.*

```
pytest tests/test_scoring.py tests/test_data_quality.py -v
```

| Test name | Result |
|-----------|--------|
| `test_...` | PASS |

---

## 5. Approval Placeholder

> **Portfolio note:** In a regulated GxP environment, rule changes to a
> validated scoring system would require documented impact assessment, review
> by a qualified person, and traceability to a change control record before
> implementation. This section serves as a structural placeholder for that
> process.

- [ ] Impact assessment complete
- [ ] Test evidence captured
- [ ] `SCORING_RULE_VERSION` bumped (if applicable)
- [ ] `CHANGELOG.md` updated
- [ ] `docs/data-dictionary.md` updated (if field definitions changed)
- [ ] PR approved

---

## 6. Implementation Reference

| Artifact | Link |
|----------|------|
| Pull request | *(PR URL)* |
| Commit SHA | *(SHA)* |
| Related issue | *(Issue URL)* |
| CI run | *(Actions URL)* |

---

> Template version: 1.0  
> Last updated: 2026-08-13
