from __future__ import annotations

from abc import ABC, abstractmethod

from app.mbti_test.domain.models import AIQuestionResponse, GenerateAIQuestionCommand


class AIQuestionProviderPort(ABC):
    @abstractmethod
    def generate_questions(self, command: GenerateAIQuestionCommand) -> AIQuestionResponse:
        """
        LLM 기반으로 다음 질문(1~2개)을 생성한다.
        - JSON 스키마 강제
        - Markdown fence 제거/정규화
        """
        raise NotImplementedError
