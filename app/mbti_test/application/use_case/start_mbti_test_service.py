import uuid
from datetime import datetime

from app.mbti_test.application.port.input.start_mbti_test_use_case import (
    StartMBTITestUseCase,
    StartMBTITestCommand,
    StartMBTITestResponse,
)
from app.mbti_test.application.port.output.mbti_test_session_repository import MBTITestSessionRepositoryPort
from app.mbti_test.application.port.output.question_provider_port import QuestionProviderPort
from app.mbti_test.domain.mbti_test_session import MBTITestSession, TestStatus


class StartMBTITestService(StartMBTITestUseCase):
    def __init__(
        self,
        mbti_test_session_repository: MBTITestSessionRepositoryPort,
        question_provider: QuestionProviderPort,
    ):
        self._mbti_test_session_repository = mbti_test_session_repository
        self._question_provider = question_provider

    def execute(self, command: StartMBTITestCommand) -> StartMBTITestResponse:
        first_question = self._question_provider.get_initial_question()

        session = MBTITestSession(
            id=uuid.uuid4(),
            user_id=command.user_id,
            test_type=command.test_type,
            status=TestStatus.IN_PROGRESS,
            created_at=datetime.now(),
            questions=[first_question.content],  # Save first question
        )

        self._mbti_test_session_repository.save(session)

        return StartMBTITestResponse(
            session=session,
            first_question=first_question,
        )
