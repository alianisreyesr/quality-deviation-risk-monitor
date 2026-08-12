from pydantic import BaseModel
from typing import List, Optional


class DeviationRecord(BaseModel):
    deviation_id: str
    title: str
    severity: str
    opened_date: str
    due_date: str
    investigation_owner: Optional[str] = None
    repeat_occurrence: bool
    record_complete: bool
    review_status: str


class DeviationResponse(DeviationRecord):
    risk_score: int
    risk_level: str
    risk_reasons: List[str]


class DeviationsListResponse(BaseModel):
    count: int
    records: List[DeviationResponse]


class RiskCounts(BaseModel):
    Low: int
    Medium: int
    High: int


class SummaryResponse(BaseModel):
    total_records: int
    risk_counts: RiskCounts
    review_status_counts: dict
