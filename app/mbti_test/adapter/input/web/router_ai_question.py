from __future__ import annotations

from typing import Annotated, List, Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.mbti_test.adapter.output.openai_ai_question_provider import (
    create_openai_question_provider_from_settings,
)
from app.mbti_test.application.usecase.generate_ai_question_usecase import GenerateAIQuestionUseCase
from app.mbti_test.domain.models import ChatMessage, GenerateAIQuestionCommand, MessageRole


router = APIRouter(tags=["MBTI Test"])


class ChatMessageDTO(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str = Field(min_length=1)


class GenerateAIQuestionRequest(BaseModel):
    turn: Annotated[int, Field(ge=1, le=5)]
    history: Annotated[List[ChatMessageDTO], Field(default_factory=list)]
    question_mode: Literal["normal", "surprise"] = "normal"


class AIQuestionDTO(BaseModel):
    text: str
    target_dimensions: List[str]


class GenerateAIQuestionResponse(BaseModel):
    turn: int
    questions: List[AIQuestionDTO]


def _usecase_dep() -> GenerateAIQuestionUseCase:
    provider = create_openai_question_provider_from_settings()
    return GenerateAIQuestionUseCase(provider=provider)


@router.post("/{session_id}/ai-question", response_model=GenerateAIQuestionResponse)
def generate_ai_question(
    session_id: str,
    req: GenerateAIQuestionRequest,
    usecase: GenerateAIQuestionUseCase = Depends(_usecase_dep),
) -> GenerateAIQuestionResponse:
    # 세션 존재/권한/히스토리 저장은 다른 팀 영역(1~3번)이 담당한다고 가정.
    # 여기서는 받은 history로만 질문 생성.
    history = [
        ChatMessage(role=MessageRole(m.role), content=m.content)
        for m in req.history
    ]
    cmd = GenerateAIQuestionCommand(
        session_id=session_id,
        turn=req.turn,
        history=history,
        question_mode=req.question_mode,
    )

    try:
        result = usecase.execute(cmd)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception:
        # 내부 프롬프트/LLM 실패는 502로 처리 (원인 노출 최소화)
        raise HTTPException(status_code=502, detail="AI question generation failed")

    return GenerateAIQuestionResponse(
        turn=result.turn,
        questions=[
            AIQuestionDTO(text=q.text, target_dimensions=q.target_dimensions)
            for q in result.questions
        ],
    )
