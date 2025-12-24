import uuid
from fastapi import APIRouter, Depends, HTTPException
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel

from app.mbti_test.application.port.input.start_mbti_test_use_case import StartMBTITestCommand
from app.mbti_test.application.port.input.answer_question_use_case import AnswerQuestionCommand
from app.mbti_test.application.use_case.start_mbti_test_service import StartMBTITestService
from app.mbti_test.application.use_case.answer_question_service import AnswerQuestionService
from app.mbti_test.domain.mbti_test_session import TestType
from app.auth.adapter.input.web.auth_dependency import get_current_user_id
from app.mbti_test.application.port.output.mbti_test_session_repository import MBTITestSessionRepositoryPort
from app.mbti_test.application.port.output.question_provider_port import QuestionProviderPort
from app.mbti_test.application.port.ai_question_provider_port import AIQuestionProviderPort
from app.mbti_test.infrastructure.repository.in_memory_mbti_test_session_repository import InMemoryMBTITestSessionRepository
from app.mbti_test.infrastructure.service.in_memory_question_provider import InMemoryQuestionProvider
from app.mbti_test.infrastructure.service.human_question_provider import HumanQuestionProvider
from app.mbti_test.adapter.output.openai_ai_question_provider import create_openai_question_provider_from_settings

mbti_router = APIRouter()

# Singleton session repository (persists across requests)
_session_repository = InMemoryMBTITestSessionRepository()


def get_session_repository() -> MBTITestSessionRepositoryPort:
    return _session_repository


def get_question_provider() -> QuestionProviderPort:
    return InMemoryQuestionProvider()


def get_human_question_provider() -> HumanQuestionProvider:
    return HumanQuestionProvider()


def get_ai_question_provider() -> AIQuestionProviderPort:
    return create_openai_question_provider_from_settings()


class AnswerRequest(BaseModel):
    content: str


@mbti_router.post("/start")
async def start_mbti_test(
    test_type: TestType = TestType.HUMAN,
    user_id: str = Depends(get_current_user_id),
    session_repository: MBTITestSessionRepositoryPort = Depends(get_session_repository),
    question_provider: QuestionProviderPort = Depends(get_question_provider)
):
    use_case = StartMBTITestService(session_repository, question_provider)
    command = StartMBTITestCommand(user_id=uuid.UUID(user_id), test_type=test_type)
    result = use_case.execute(command)

    return jsonable_encoder({"session": result.session, "first_question": result.first_question})


@mbti_router.post("/{test_session_id}/answer")
async def answer_question(
    test_session_id: str,
    request: AnswerRequest,
    user_id: str = Depends(get_current_user_id),
    session_repository: MBTITestSessionRepositoryPort = Depends(get_session_repository),
    human_question_provider: HumanQuestionProvider = Depends(get_human_question_provider),
    ai_question_provider: AIQuestionProviderPort = Depends(get_ai_question_provider),
):
    use_case = AnswerQuestionService(
        session_repository=session_repository,
        human_question_provider=human_question_provider,
        ai_question_provider=ai_question_provider,
    )

    try:
        command = AnswerQuestionCommand(session_id=test_session_id, answer=request.content)
        result = use_case.execute(command)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    return jsonable_encoder({
        "question_number": result.question_number,
        "total_questions": result.total_questions,
        "next_question": result.next_question,
        "is_completed": result.is_completed,
    })