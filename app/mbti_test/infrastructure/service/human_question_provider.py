from app.mbti_test.domain.mbti_message import MBTIMessage, MessageRole, MessageSource

# 12개의 저장된 질문 (E/I, S/N, T/F, J/P 각 3개씩)
HUMAN_QUESTIONS = [
    # E/I 차원 (1-3)
    "새로운 사람들을 만나면 에너지가 충전되는 편인가요, 아니면 혼자만의 시간이 필요한 편인가요?",
    "파티나 모임에서 먼저 다가가서 대화를 시작하는 편인가요?",
    "주말에 친구들과 어울리는 것과 집에서 쉬는 것 중 어떤 것을 더 선호하시나요?",

    # S/N 차원 (4-6)
    "문제를 해결할 때 과거의 경험과 검증된 방법을 선호하나요, 아니면 새로운 가능성을 탐색하나요?",
    "세부 사항에 집중하는 편인가요, 아니면 큰 그림을 먼저 보는 편인가요?",
    "현실적이고 구체적인 정보를 선호하나요, 아니면 상상력과 영감을 더 중요시하나요?",

    # T/F 차원 (7-9)
    "결정을 내릴 때 논리와 객관적 사실을 우선하나요, 아니면 사람들의 감정과 가치를 우선하나요?",
    "친구가 고민을 털어놓을 때, 해결책을 제시하려 하나요 아니면 공감하며 들어주려 하나요?",
    "비판을 받을 때 사실 여부를 먼저 확인하나요, 아니면 상대방의 의도를 먼저 생각하나요?",

    # J/P 차원 (10-12)
    "여행을 갈 때 상세한 계획을 세우는 편인가요, 아니면 그때그때 결정하는 편인가요?",
    "마감 기한이 있을 때 미리미리 끝내는 편인가요, 아니면 마감 직전에 집중하는 편인가요?",
    "일상에서 정해진 루틴을 따르는 것을 선호하나요, 아니면 유연하게 변화하는 것을 선호하나요?",
]


class HumanQuestionProvider:
    """저장된 인간 질문을 제공하는 Provider"""

    def get_question(self, question_index: int) -> MBTIMessage | None:
        """
        질문 인덱스에 해당하는 질문을 반환합니다.

        Args:
            question_index: 0-based 질문 인덱스 (0-11)

        Returns:
            MBTIMessage or None if index out of range
        """
        if question_index < 0 or question_index >= len(HUMAN_QUESTIONS):
            return None

        return MBTIMessage(
            role=MessageRole.ASSISTANT,
            content=HUMAN_QUESTIONS[question_index],
            source=MessageSource.HUMAN,
        )

    def get_total_questions(self) -> int:
        return len(HUMAN_QUESTIONS)
