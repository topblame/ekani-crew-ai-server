from __future__ import annotations

from dataclasses import dataclass

from app.mbti_test.application.port.ai_question_provider_port import AIQuestionProviderPort
from app.mbti_test.domain.models import AIQuestionResponse, GenerateAIQuestionCommand


@dataclass
class GenerateAIQuestionUseCase:
    provider: AIQuestionProviderPort

    def execute(self, command: GenerateAIQuestionCommand) -> AIQuestionResponse:
        # 세션/턴 검증은 다른 팀(1~3번) 영역에서 담당한다고 가정하고,
        # 이 유스케이스는 "질문 생성" 책임만 가진다.
        if command.turn < 1 or command.turn > 5:
            # MBTI 테스트 턴 정책(1~5) 외 입력은 즉시 방어
            raise ValueError("turn must be between 1 and 5")

        return self.provider.generate_questions(command)