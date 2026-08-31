from datetime import date
from typing import Any, Literal

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


CapaType = Literal["Corrective", "Preventive"]
CapaStatus = Literal["Open", "In Progress", "Pending Effectiveness Check", "Closed"]


class CapaResponse(BaseModel):
    capa_id: str
    deviation_id: str | None
    title: str
    capa_type: CapaType
    severity: RiskLevel
    root_cause: str | None
    opened_date: date
    due_date: date
    closure_date: date | None
    owner: str | None
    recurrence_flag: bool
    effectiveness_check_complete: bool
    status: CapaStatus
    aging_days: int = Field(ge=0, description="Days open (or days-to-close for closed CAPAs).")
    risk_score: int = Field(ge=0)
    risk_level: RiskLevel
    risk_reasons: list[str]
    scoring_rule_version: str = Field(
        description="Version of the CAPA risk-scoring rule set used to produce this score."
    )


class CapaListResponse(BaseModel):
    count: int
    records: list[CapaResponse]


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


# ---------------------------------------------------------------------------
# Quality metrics
# ---------------------------------------------------------------------------

class QualityMetricsResponse(BaseModel):
    """Aggregated quality metrics across deviations and CAPA records."""
    generated_at: str = Field(description="ISO-8601 date the metrics were computed against.")
    deviation_aging: dict[str, Any]
    capa_aging: dict[str, Any]
    recurrence: dict[str, float]
    severity_distribution: dict[str, dict[str, int]]
    capa_closure: dict[str, Any]
    root_causes: dict[str, int]
