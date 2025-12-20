import uuid
from typing import Dict

from app.mbti_test.application.port.output.mbti_test_session_repository import MBTITestSessionRepositoryPort
from app.mbti_test.domain.mbti_test_session import MBTITestSession


class FakeMBTITestSessionRepository(MBTITestSessionRepositoryPort):
    def __init__(self):
        self._sessions: Dict[uuid.UUID, MBTITestSession] = {}

    def save(self, session: MBTITestSession) -> MBTITestSession:
        self._sessions[session.id] = session
        return session

    def find_by_id(self, session_id: uuid.UUID) -> MBTITestSession | None:
        return self._sessions.get(session_id)

    def find_all(self) -> list[MBTITestSession]:
        return list(self._sessions.values())
