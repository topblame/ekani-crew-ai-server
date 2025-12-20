from typing import Literal

from pydantic import BaseModel


class MBTIMessage(BaseModel):
    role: Literal["USER", "ASSISTANT"]
    content: str
    question_type: Literal["NORMAL", "SUDDEN"]
    source: Literal["HUMAN", "AI"]
