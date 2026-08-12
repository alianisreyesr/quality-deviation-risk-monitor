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
