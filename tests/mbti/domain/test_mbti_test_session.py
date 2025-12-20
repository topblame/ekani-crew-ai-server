import uuid
from datetime import datetime

from app.mbti_test.domain.mbti_test_session import MBTITestSession


def test_create_mbti_test_session():
    user_id = uuid.uuid4()
    session = MBTITestSession(user_id=user_id)

    assert isinstance(session.id, uuid.UUID)
    assert session.user_id == user_id
    assert session.status == "IN_PROGRESS"
    assert isinstance(session.created_at, datetime)
