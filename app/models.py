from datetime import date
from typing import Literal

from pydantic import BaseModel, Field

RiskLevel = Literal["Low", "Medium", "High"]


class DeviationResponse(BaseModel):
    deviation_id: str
    title: str
    severity: RiskLevel
    opened_date: date
    due_date: date
    investigation_owner: str | None
    repeat_occurrence: bool
    record_complete: bool
    review_status: str
    risk_score: int = Field(ge=0)
    risk_level: RiskLevel
    risk_reasons: list[str]
    scoring_rule_version: str = Field(
        description="Version of the risk-scoring rule set used to produce this score."
    )


class DeviationListResponse(BaseModel):
    count: int
    records: list[DeviationResponse]


class SummaryResponse(BaseModel):
    total_records: int
    risk_counts: dict[RiskLevel, int]
    review_status_counts: dict[str, int]
    overdue_records: int
    unassigned_records: int


# ---------------------------------------------------------------------------
# Data Quality
# ---------------------------------------------------------------------------

class FieldQualityReport(BaseModel):
    """Quality statistics for a single dataset field."""
    field_name: str
    total_records: int
    null_count: int
    invalid_count: int
    null_rate: float = Field(description="Fraction of records with null/empty value (0–1)")
    invalid_rate: float = Field(description="Fraction of records with an invalid value (0–1)")
    sample_invalid_values: list[str] = Field(
        default_factory=list,
        description="Up to 5 example invalid values for diagnostic purposes.",
    )


class DataQualityResponse(BaseModel):
    """Dataset-level data quality summary."""
    total_records: int
    records_with_any_issue: int
    issue_rate: float = Field(description="Fraction of records with at least one data issue (0–1)")
    fields: list[FieldQualityReport]
