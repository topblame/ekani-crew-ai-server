import pytest
from datetime import datetime
from app.shared.vo.mbti import MBTI
from app.match.domain.match_ticket import MatchTicket

def test_create_match_ticket():
    # Given
    user_id = "user_123"
    mbti = MBTI("INFP")

    # When
    ticket = MatchTicket(user_id=user_id, mbti=mbti)

    # Then
    assert ticket.user_id == "user_123"
    assert ticket.mbti == mbti
    assert isinstance(ticket.created_at, datetime)

def test_match_ticket_validation():
    # Given / When / Then
    with pytest.raises(ValueError):
        MatchTicket(user_id="", mbti=MBTI("INFP"))  # 빈 ID 테스트