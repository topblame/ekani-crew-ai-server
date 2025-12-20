import uuid
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.mbti_test.application.port.input.start_mbti_test_use_case import (
    StartMBTITestUseCase,
    StartMBTITestCommand,
    StartMBTITestResponse as StartMBTITestUseCaseResponse,
)
from app.mbti_test.application.use_case.start_mbti_test_service import StartMBTITestService
from app.mbti_test.application.port.output.mbti_test_session_repository import MBTITestSessionRepositoryPort
from app.mbti_test.application.port.output.question_provider_port import QuestionProviderPort
from app.mbti_test.adapter.input.web.router_ai_question import router as ai_question_router
from tests.mbti.fixtures.fake_mbti_test_session_repository import FakeMBTITestSessionRepository
from tests.mbti.fixtures.fake_question_provider import FakeQuestionProvider

mbti_router = APIRouter()
# AI 질문 엔드포인트도 이 라우터에 합친다
mbti_router.include_router(ai_question_router)

# --- Dependencies ---
def get_mbti_test_session_repository() -> MBTITestSessionRepositoryPort:
    # In a real scenario, this would return a persistent repository implementation
    return FakeMBTITestSessionRepository()


def get_question_provider() -> QuestionProviderPort:
    # In a real scenario, this would return a real question provider
    return FakeQuestionProvider()


def get_start_mbti_test_use_case(
    repository: MBTITestSessionRepositoryPort = Depends(get_mbti_test_session_repository),
    question_provider: QuestionProviderPort = Depends(get_question_provider),
) -> StartMBTITestUseCase:
    return StartMBTITestService(
        mbti_test_session_repository=repository,
        question_provider=question_provider,
    )


# --- API Models ---
class StartTestRequest(BaseModel):
    user_id: uuid.UUID


class StartTestResponse(BaseModel):
    session_id: uuid.UUID
    first_question: str


# --- Router ---
@mbti_router.post("/start", response_model=StartTestResponse)
def start_test(
    request: StartTestRequest,
    use_case: StartMBTITestUseCase = Depends(get_start_mbti_test_use_case),
):
    """
    MBTI 테스트 세션을 시작하고 첫 번째 질문을 반환합니다.
    """
    command = StartMBTITestCommand(user_id=request.user_id)
    result: StartMBTITestUseCaseResponse = use_case.execute(command)

    return StartTestResponse(
        session_id=result.session.id,
        first_question=result.first_question.content,
    )
