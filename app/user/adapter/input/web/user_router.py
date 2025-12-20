from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.auth.adapter.input.web.auth_dependency import get_current_user_id
from app.user.application.port.user_repository_port import UserRepositoryPort
from app.user.domain.user import User
from app.shared.vo.mbti import MBTI
from app.shared.vo.gender import Gender
from app.user.infrastructure.repository.mysql_user_repository import MySQLUserRepository
from config.database import get_db_session

user_router = APIRouter()


def get_user_repository() -> UserRepositoryPort:
    return MySQLUserRepository(get_db_session())


class UpdateProfileRequest(BaseModel):
    mbti: str
    gender: str


@user_router.get("/profile")
def get_profile(
    user_id: str = Depends(get_current_user_id),
    user_repo: UserRepositoryPort = Depends(get_user_repository),
):
    """현재 로그인한 사용자의 프로필 조회"""
    user = user_repo.find_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="사용자를 찾을 수 없습니다",
        )

    return {
        "id": user.id,
        "email": user.email,
        "mbti_test": user.mbti.value if user.mbti else None,
        "gender": user.gender.value if user.gender else None,
    }


@user_router.put("/profile")
def update_profile(
    request: UpdateProfileRequest,
    user_id: str = Depends(get_current_user_id),
    user_repo: UserRepositoryPort = Depends(get_user_repository),
):
    """MBTI/성별 프로필 저장 (upsert)"""
    user = user_repo.find_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="사용자를 찾을 수 없습니다",
        )

    try:
        mbti = MBTI(request.mbti)
        gender = Gender(request.gender.upper())
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    updated_user = User(
        id=user.id,
        email=user.email,
        mbti=mbti,
        gender=gender,
    )
    user_repo.save(updated_user)

    return {
        "id": updated_user.id,
        "email": updated_user.email,
        "mbti_test": updated_user.mbti.value,
        "gender": updated_user.gender.value,
    }