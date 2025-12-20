from abc import ABC, abstractmethod
import uuid

from app.mbti_test.domain.mbti_test_session import MBTITestSession


class MBTITestSessionRepositoryPort(ABC):
    @abstractmethod
    def save(self, session: MBTITestSession) -> MBTITestSession:
        pass

    @abstractmethod
    def find_by_id(self, session_id: uuid.UUID) -> MBTITestSession | None:
        pass
