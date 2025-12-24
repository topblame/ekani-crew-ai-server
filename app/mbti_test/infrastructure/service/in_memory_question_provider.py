from app.mbti_test.application.port.output.question_provider_port import QuestionProviderPort
from app.mbti_test.domain.mbti_message import MBTIMessage
from app.mbti_test.infrastructure.service.human_question_provider import HumanQuestionProvider


class InMemoryQuestionProvider(QuestionProviderPort):
    def __init__(self):
        self._human_provider = HumanQuestionProvider()

    def get_initial_question(self) -> MBTIMessage:
        # Return the first human question (index 0)
        return self._human_provider.get_question(0)
