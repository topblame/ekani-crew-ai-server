from app.mbti_test.application.port.output.question_provider_port import QuestionProviderPort
from app.mbti_test.domain.mbti_message import MBTIMessage


class FakeQuestionProvider(QuestionProviderPort):
    def get_initial_question(self) -> MBTIMessage:
        return MBTIMessage(
            role="ASSISTANT",
            content="안녕하세요! MBTI 테스트를 시작하겠습니다. 첫 번째 질문입니다: 혼자 있을 때 에너지를 얻나요, 아니면 다른 사람들과 함께 있을 때 에너지를 얻나요?",
            question_type="NORMAL",
            source="AI",
        )
