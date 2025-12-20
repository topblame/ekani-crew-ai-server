from app.mbti_test.domain.mbti_message import MBTIMessage


def test_create_mbti_message():
    message = MBTIMessage(
        role="ASSISTANT",
        content="당신은 어떤 종류의 책을 가장 좋아하나요?",
        question_type="NORMAL",
        source="AI",
    )

    assert message.role == "ASSISTANT"
    assert message.content == "당신은 어떤 종류의 책을 가장 좋아하나요?"
    assert message.question_type == "NORMAL"
    assert message.source == "AI"
