from pydantic import BaseModel, Field

class MatchRequest(BaseModel):
    user_id: str
    mbti: str
    level: int = Field(default=1, ge=1, le=4, description="1:천생연분, 2:좋음, 3:무난, 4:전체")