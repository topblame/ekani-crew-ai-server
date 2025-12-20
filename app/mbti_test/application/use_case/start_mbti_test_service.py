from app.mbti_test.application.port.input.start_mbti_test_use_case import (
    StartMBTITestUseCase,
    StartMBTITestCommand,
    StartMBTITestResponse,
)
from app.mbti_test.application.port.output.mbti_test_session_repository import MBTITestSessionRepositoryPort
from app.mbti_test.application.port.output.question_provider_port import QuestionProviderPort
from app.mbti_test.domain.mbti_test_session import MBTITestSession


class StartMBTITestService(StartMBTITestUseCase):
    def __init__(
        self,
        mbti_test_session_repository: MBTITestSessionRepositoryPort,
        question_provider: QuestionProviderPort,
    ):
        self._mbti_test_session_repository = mbti_test_session_repository
        self._question_provider = question_provider

    def execute(self, command: StartMBTITestCommand) -> StartMBTITestResponse:
        # Create a new session
        session = MBTITestSession(user_id=command.user_id)

        # Save the session
        self._mbti_test_session_repository.save(session)

        # Get the first question
        first_question = self._question_provider.get_initial_question()

        return StartMBTITestResponse(
            session=session,
            first_question=first_question,
        )
