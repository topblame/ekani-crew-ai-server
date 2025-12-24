from pydantic import BaseModel

class MatchCancelRequest(BaseModel):
    user_id: str
    mbti: str