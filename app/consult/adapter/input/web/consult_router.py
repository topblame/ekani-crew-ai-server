from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.consult.application.use_case.start_consult_use_case import StartConsultUseCase
from app.consult.application.use_case.send_message_use_case import SendMessageUseCase
from app.user.application.port.user_repository_port import UserRepositoryPort
from app.consult.application.port.consult_repository_port import ConsultRepositoryPort
from app.consult.application.port.ai_counselor_port import AICounselorPort
from app.auth.adapter.input.web.auth_dependency import get_current_user_id
from app.consult.domain.message import Message
from app.user.infrastructure.repository.mysql_user_repository import MySQLUserRepository
from app.consult.infrastructure.repository.mysql_consult_repository import MySQLConsultRepository
from app.consult.infrastructure.service.openai_counselor_adapter import OpenAICounselorAdapter
from config.database import get_db_session
from config.settings import get_settings

consult_router = APIRouter()


def get_user_repository() -> UserRepositoryPort:
    return MySQLUserRepository(get_db_session())


def get_consult_repository() -> ConsultRepositoryPort:
    return MySQLConsultRepository(get_db_session())


def get_ai_counselor() -> AICounselorPort:
    settings = get_settings()
    return OpenAICounselorAdapter(api_key=settings.OPENAI_API_KEY)


class SendMessageRequest(BaseModel):
    content: str


@consult_router.post("/start")
def start_consult(
    user_id: str = Depends(get_current_user_id),
    user_repo: UserRepositoryPort = Depends(get_user_repository),
    consult_repo: ConsultRepositoryPort = Depends(get_consult_repository),
    ai_counselor: AICounselorPort = Depends(get_ai_counselor),
):
    """
    상담 세션을 시작한다.

    1. user_id로 User 조회
    2. User의 MBTI, Gender 확인
    3. StartConsultUseCase 실행
    4. 세션 ID 반환
    """
    user = user_repo.find_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="사용자를 찾을 수 없습니다",
        )

    if not user.mbti or not user.gender:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="프로필 정보(MBTI, 성별)를 먼저 입력해주세요",
        )

    use_case = StartConsultUseCase(consult_repo, ai_counselor)
    result = use_case.execute(user_id=user_id, mbti=user.mbti, gender=user.gender)

    return result


@consult_router.post("/{session_id}/message")
def send_message(
    session_id: str,
    request: SendMessageRequest,
    user_id: str = Depends(get_current_user_id),
    consult_repo: ConsultRepositoryPort = Depends(get_consult_repository),
    ai_counselor: AICounselorPort = Depends(get_ai_counselor),
):
    """
    메시지를 전송하고 AI 응답을 받는다.

    1. 세션 조회 및 소유자 검증
    2. 메시지 전송
    3. AI 응답 반환
    """
    use_case = SendMessageUseCase(consult_repo, ai_counselor)

    try:
        result = use_case.execute(
            session_id=session_id,
            user_id=user_id,
            content=request.content
        )
        return result
    except ValueError as e:
        error_message = str(e)
        if "상담이 완료되었습니다" in error_message:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_message,
            )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error_message,
        )
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        )


@consult_router.get("/history")
def get_history(
    user_id: str = Depends(get_current_user_id),
    consult_repo: ConsultRepositoryPort = Depends(get_consult_repository),
):
    """
    완료된 상담 세션 히스토리를 조회한다.

    Returns:
        완료된 상담 세션 목록 (최신순)
    """
    sessions = consult_repo.find_completed_by_user_id(user_id)

    return {
        "sessions": [
            {
                "id": session.id,
                "created_at": session.created_at.isoformat(),
                "mbti_test": session.mbti.value,
                "gender": session.gender.value,
                "analysis": session.get_analysis(),
            }
            for session in sessions
        ]
    }


@consult_router.post("/{session_id}/message/stream")
def send_message_stream(
    session_id: str,
    request: SendMessageRequest,
    user_id: str = Depends(get_current_user_id),
    consult_repo: ConsultRepositoryPort = Depends(get_consult_repository),
    ai_counselor: AICounselorPort = Depends(get_ai_counselor),
):
    """
    메시지를 전송하고 AI 응답을 SSE 스트리밍으로 받는다.

    1. 세션 조회 및 소유자 검증
    2. 메시지 저장
    3. AI 응답 스트리밍 반환
    """
    # 세션 조회 및 소유자 검증
    session = consult_repo.find_by_id(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="세션을 찾을 수 없습니다",
        )

    if session.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="이 세션에 접근할 권한이 없습니다",
        )

    # 턴 제한 체크
    if session.is_completed():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="상담이 완료되었습니다. 추가 메시지를 보낼 수 없습니다.",
        )

    # 사용자 메시지 저장
    user_message = Message(role="user", content=request.content)
    session.add_message(user_message)
    consult_repo.save(session)

    # SSE 스트리밍 생성
    def event_generator():
        full_response = ""
        for chunk in ai_counselor.generate_response_stream(session, request.content):
            full_response += chunk
            yield f"data: {chunk}\n\n"

        # AI 응답 저장
        ai_message = Message(role="assistant", content=full_response)
        session.add_message(ai_message)
        consult_repo.save(session)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream"
    )
