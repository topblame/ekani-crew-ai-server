from datetime import datetime
from app.shared.vo.mbti import MBTI

class MatchTicket:
    """
    매칭 대기열에 진입하는 유저의 대기표(Ticket) 엔티티
    """
    def __init__(self, user_id: str, mbti: MBTI):
        self._validate(user_id, mbti)
        self.user_id = user_id
        self.mbti = mbti
        self.created_at = datetime.now()

    def _validate(self, user_id: str, mbti: MBTI) -> None:
        if not user_id:
            raise ValueError("User ID는 필수입니다.")
        if mbti is None:
            raise ValueError("MBTI 정보는 필수입니다.")

    def __eq__(self, other):
        if isinstance(other, MatchTicket):
            return self.user_id == other.user_id
        return False