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


class DeviationListResponse(BaseModel):
    count: int
    records: list[DeviationResponse]


class SummaryResponse(BaseModel):
    total_records: int
    risk_counts: dict[RiskLevel, int]
    review_status_counts: dict[str, int]
    overdue_records: int
    unassigned_records: int
