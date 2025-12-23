from fastapi import APIRouter, HTTPException

from app.match.adapter.input.web.request.match_cancel_request import MatchCancelRequest
from app.shared.vo.mbti import MBTI
from app.match.adapter.input.web.request.match_request import MatchRequest
from app.match.application.factory.match_usecase_factory import MatchUseCaseFactory

match_router = APIRouter()


@match_router.post("/request")
async def request_match(request: MatchRequest):
    """
    매칭 대기열에 유저를 등록합니다.
    """
    try:
        # 1. String -> Enum 변환
        mbti_enum = MBTI(request.mbti.upper())

        # 2. UseCase 생성 및 실행
        usecase = MatchUseCaseFactory.create()
        result = await usecase.request_match(
            user_id=request.user_id,
            mbti=mbti_enum,
            level=request.level
        )

        return result

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@match_router.post("/cancel")
async def cancel_match(request: MatchCancelRequest):
    """
    매칭 대기열에서 유저를 삭제(취소)합니다.
    """
    try:
        mbti_enum = MBTI(request.mbti.upper())

        usecase = MatchUseCaseFactory.create()
        result = await usecase.cancel_match(request.user_id, mbti_enum)

        return result

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@match_router.get("/queue/{mbti}")
async def get_queue_status(mbti: str):
    """
    (테스트용) 특정 MBTI 대기열의 현재 대기 인원수를 확인합니다.
    """
    try:
        mbti_enum = MBTI(mbti.upper())

        usecase = MatchUseCaseFactory.create()

        count = await usecase.get_waiting_count(mbti_enum)

        return {
            "mbti": mbti.upper(),
            "waiting_count": count
        }

    except ValueError:
        raise HTTPException(status_code=400, detail="유효하지 않은 MBTI입니다.")