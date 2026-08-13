from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

ReviewAction = Literal["acknowledge", "investigate", "close"]


class ReviewActionRequest(BaseModel):
    action: ReviewAction
    actor: str = Field(min_length=1, max_length=100)
    comment: str | None = Field(default=None, max_length=1000)


class AuditEventResponse(BaseModel):
    event_id: int
    deviation_id: str
    action: ReviewAction
    actor: str
    comment: str | None
    previous_status: str
    new_status: str
    created_at: datetime


class TransitionRejectedResponse(BaseModel):
    """Returned as HTTP 409 when a state transition is not permitted."""
    detail: str
    deviation_id: str
    current_status: str
    requested_action: str
    allowed_actions: list[str]


class AuditTrailResponse(BaseModel):
    """Audit history for a single deviation."""
    deviation_id: str
    current_review_status: str
    event_count: int
    events: list[dict]
