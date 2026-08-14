"""
Risk scoring configuration for Quality Deviation Risk Monitor.

References:
  - ICH Q10 §3.2: Deviation management, ~30-day closure expectation
  - ICH Q9(R1) §4: Risk ranking via numerical scoring
"""

SEVERITY_SCORES: dict[str, int] = {
    "High":   3,
    "Medium": 1,
    "Low":    0,
}

AGING_THRESHOLD_DAYS_TIER1: int = 30
AGING_THRESHOLD_DAYS_TIER2: int = 60
AGING_SCORE_TIER1: int = 1
AGING_SCORE_TIER2: int = 2

SCORE_PAST_DUE_DATE:       int = 3
SCORE_NO_OWNER:            int = 2
SCORE_REPEAT_OCCURRENCE:   int = 2
SCORE_INCOMPLETE_RECORD:   int = 2

RISK_THRESHOLD_HIGH:   int = 5
RISK_THRESHOLD_MEDIUM: int = 2
