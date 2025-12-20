import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class MBTITestSession(BaseModel):
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    user_id: uuid.UUID
    status: Literal["IN_PROGRESS", "COMPLETED"] = "IN_PROGRESS"
    created_at: datetime = Field(default_factory=datetime.utcnow)
