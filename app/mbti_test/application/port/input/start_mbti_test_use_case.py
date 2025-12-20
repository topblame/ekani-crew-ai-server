import uuid
from abc import ABC, abstractmethod
from pydantic import BaseModel

from app.mbti_test.domain.mbti_message import MBTIMessage
from app.mbti_test.domain.mbti_test_session import MBTITestSession


class StartMBTITestCommand(BaseModel):
    user_id: uuid.UUID


class StartMBTITestResponse(BaseModel):
    session: MBTITestSession
    first_question: MBTIMessage


class StartMBTITestUseCase(ABC):
    @abstractmethod
    def execute(self, command: StartMBTITestCommand) -> StartMBTITestResponse:
        pass
