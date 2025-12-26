import uuid
from typing import Dict

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel

from app.auth.adapter.input.web.auth_dependency import get_current_user_id
from app.mbti_test.application.port.input.start_mbti_test_use_case import StartMBTITestCommand
from app.mbti_test.application.port.input.answer_question_use_case import AnswerQuestionCommand
from app.mbti_test.application.use_case.start_mbti_test_service import StartMBTITestService
from app.mbti_test.application.use_case.answer_question_service import AnswerQuestionService
from app.mbti_test.application.port.output.mbti_test_session_repository import MBTITestSessionRepositoryPort
from app.mbti_test.application.port.ai_question_provider_port import AIQuestionProviderPort
from app.mbti_test.infrastructure.repository.in_memory_mbti_test_session_repository import InMemoryMBTITestSessionRepository
from app.mbti_test.infrastructure.service.human_question_provider import HumanQuestionProvider
from app.mbti_test.adapter.output.openai_ai_question_provider import create_openai_question_provider_from_settings

# 결과 조회용 DI + UseCase + Exceptions
from app.mbti_test.infrastructure.di import get_calculate_final_mbti_usecase
from app.mbti_test.application.use_case.calculate_final_mbti_usecase import CalculateFinalMBTIUseCase
from app.mbti_test.domain.exceptions import SessionNotFound, SessionNotCompleted
from app.mbti_test.application.port.output.user_repository_port import UserRepositoryPort

mbti_router = APIRouter()

# 기존 /ai-question 라우터 포함
from app.mbti_test.adapter.input.web.router_ai_question import router as ai_question_router
mbti_router.include_router(ai_question_router)

# DI (현재는 인메모리, 필요 시 MySQL Repo로 교체)
_session_repository = InMemoryMBTITestSessionRepository()

class InMemoryUserRepository(UserRepositoryPort):
    def __init__(self):
        self.mbti_map = {}
    def update_mbti(self, user_id: uuid.UUID, mbti: str) -> None:
        self.mbti_map[str(user_id)] = mbti

_user_repository = InMemoryUserRepository()
#InMemoryUserRepository 인메모리 세션/유저 저장소 추가  ⬇️ (MySQL 대신 메모리로 통일)
def get_session_repository() -> MBTITestSessionRepositoryPort:
    return _session_repository

def get_human_question_provider() -> HumanQuestionProvider:
    return HumanQuestionProvider()

def get_ai_question_provider() -> AIQuestionProviderPort:
    return create_openai_question_provider_from_settings()
# 결과 계산도 인메모리로 사용하도록 DI 추가  ⬇️
def get_calculate_final_mbti_usecase_inmemory() -> CalculateFinalMBTIUseCase:
    return CalculateFinalMBTIUseCase(
        session_repo=_session_repository,
        user_repo=_user_repository,
        required_answers=12,  # 필요 시 24 → 12로 변경한 값 유지
    )

# ... /start, /answer는 동일하게 _session_repository 사용 ...
class AnswerRequest(BaseModel):
    content: str

class MBTIResultResponse(BaseModel):
    mbti: str
    dimension_scores: Dict[str, int]
    timestamp: str

@mbti_router.post("/start")
async def start_mbti_test(
    user_id: str = Depends(get_current_user_id),
    session_repository: MBTITestSessionRepositoryPort = Depends(get_session_repository),
    human_question_provider: HumanQuestionProvider = Depends(get_human_question_provider),
):
    use_case = StartMBTITestService(session_repository, human_question_provider)
    command = StartMBTITestCommand(user_id=uuid.UUID(user_id))
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
        "analysis_result": result.analysis_result,
        "partial_analysis_result": result.partial_analysis_result,
    })

@mbti_router.get("/result/{session_id}", response_model=MBTIResultResponse)
def get_result(
    session_id: uuid.UUID,
    use_case: CalculateFinalMBTIUseCase = Depends(get_calculate_final_mbti_usecase_inmemory),  # ⬅️ 인메모리 DI로 교체
):
    try:
        result = use_case.execute(session_id=session_id)
        return MBTIResultResponse(
            mbti=result.mbti,
            dimension_scores=result.dimension_scores,
            timestamp=result.timestamp.isoformat(),
        )
    except SessionNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except SessionNotCompleted as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
