from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.community.application.port.balance_game_repository_port import BalanceGameRepositoryPort
from app.community.application.port.balance_vote_repository_port import BalanceVoteRepositoryPort
from app.community.application.port.comment_repository_port import CommentRepositoryPort
from app.community.application.use_case.vote_balance_game_use_case import VoteBalanceGameUseCase
from app.community.application.use_case.get_balance_result_use_case import GetBalanceResultUseCase
from app.community.application.use_case.add_balance_game_comment_use_case import (
    AddBalanceGameCommentUseCase,
)
from app.community.application.use_case.get_balance_game_comments_use_case import (
    GetBalanceGameCommentsUseCase,
)
from app.community.application.use_case.get_balance_game_list_use_case import (
    GetBalanceGameListUseCase,
)
from app.community.application.use_case.get_balance_game_by_id_use_case import (
    GetBalanceGameByIdUseCase,
)
from app.community.domain.balance_game import VoteChoice
from app.community.infrastructure.repository.mysql_balance_game_repository import MySQLBalanceGameRepository
from app.community.infrastructure.repository.mysql_balance_vote_repository import MySQLBalanceVoteRepository
from app.community.infrastructure.repository.mysql_comment_repository import (
    MySQLCommentRepository,
)
from app.user.application.port.user_repository_port import UserRepositoryPort
from app.user.infrastructure.repository.mysql_user_repository import (
    MySQLUserRepository,
)
from config.database import get_db


balance_game_router = APIRouter()


def get_balance_game_repository(db: Session = Depends(get_db)) -> BalanceGameRepositoryPort:
    return MySQLBalanceGameRepository(db)


def get_balance_vote_repository(db: Session = Depends(get_db)) -> BalanceVoteRepositoryPort:
    return MySQLBalanceVoteRepository(db)


def get_comment_repository(db: Session = Depends(get_db)) -> CommentRepositoryPort:
    return MySQLCommentRepository(db)


def get_user_repository(db: Session = Depends(get_db)) -> UserRepositoryPort:
    return MySQLUserRepository(db)


class BalanceGameResponse(BaseModel):
    id: str
    question: str
    option_left: str
    option_right: str
    week_of: str
    is_active: bool


class BalanceGameListItemResponse(BaseModel):
    id: str
    question: str
    option_left: str
    option_right: str
    left_percentage: float
    right_percentage: float
    comment_count: int
    is_votable: bool
    week_of: str
    created_at: datetime


class BalanceGameListResponse(BaseModel):
    items: list[BalanceGameListItemResponse]


class BalanceGameDetailCommentResponse(BaseModel):
    id: str
    author_id: str
    author_mbti: str | None
    content: str
    created_at: datetime


class BalanceGameDetailResponse(BaseModel):
    id: str
    question: str
    option_left: str
    option_right: str
    week_of: str
    total_votes: int
    left_votes: int
    right_votes: int
    left_percentage: float
    right_percentage: float
    comments: list[BalanceGameDetailCommentResponse]
    is_votable: bool
    created_at: datetime


class VoteRequest(BaseModel):
    user_id: str
    user_mbti: str
    choice: str  # "left" or "right"


class VoteResponse(BaseModel):
    vote_id: str
    choice: str


class MBTIBreakdownResponse(BaseModel):
    left: int
    right: int


class BalanceResultResponse(BaseModel):
    total_votes: int
    left_votes: int
    right_votes: int
    left_percentage: float
    right_percentage: float
    mbti_breakdown: dict[str, MBTIBreakdownResponse]


@balance_game_router.get("/balance/current")
def get_current_balance_game(
    game_repo: BalanceGameRepositoryPort = Depends(get_balance_game_repository),
) -> BalanceGameResponse:
    """현재 활성 밸런스 게임 조회"""
    game = game_repo.find_current_active()
    if not game:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="현재 활성화된 밸런스 게임이 없습니다",
        )

    return BalanceGameResponse(
        id=game.id,
        question=game.question,
        option_left=game.option_left,
        option_right=game.option_right,
        week_of=game.week_of,
        is_active=game.is_active,
    )


@balance_game_router.post("/balance/{game_id}/vote", status_code=status.HTTP_201_CREATED)
def vote_balance_game(
    game_id: str,
    request: VoteRequest,
    game_repo: BalanceGameRepositoryPort = Depends(get_balance_game_repository),
    vote_repo: BalanceVoteRepositoryPort = Depends(get_balance_vote_repository),
) -> VoteResponse:
    """밸런스 게임 투표"""
    choice = VoteChoice.LEFT if request.choice == "left" else VoteChoice.RIGHT

    use_case = VoteBalanceGameUseCase(game_repo, vote_repo)
    try:
        vote_id = use_case.execute(
            game_id=game_id,
            user_id=request.user_id,
            user_mbti=request.user_mbti,
            choice=choice,
        )
    except ValueError as e:
        error_message = str(e)
        if "찾을 수 없습니다" in error_message:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_message,
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_message,
        )

    return VoteResponse(vote_id=vote_id, choice=request.choice)


@balance_game_router.get("/balance/{game_id}/result")
def get_balance_result(
    game_id: str,
    game_repo: BalanceGameRepositoryPort = Depends(get_balance_game_repository),
    vote_repo: BalanceVoteRepositoryPort = Depends(get_balance_vote_repository),
) -> BalanceResultResponse:
    """밸런스 게임 결과 조회 (MBTI별 투표 비율)"""
    use_case = GetBalanceResultUseCase(game_repo, vote_repo)
    try:
        result = use_case.execute(game_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )

    mbti_breakdown = {
        mbti: MBTIBreakdownResponse(left=data["left"], right=data["right"])
        for mbti, data in result.mbti_breakdown.items()
    }

    return BalanceResultResponse(
        total_votes=result.total_votes,
        left_votes=result.left_votes,
        right_votes=result.right_votes,
        left_percentage=result.left_percentage,
        right_percentage=result.right_percentage,
        mbti_breakdown=mbti_breakdown,
    )


# ================= Comment Endpoints =================


class CreateBalanceGameCommentRequest(BaseModel):
    author_id: str
    content: str


class BalanceGameCommentResponse(BaseModel):
    id: str
    game_id: str
    author_id: str
    author_mbti: str | None
    content: str
    created_at: datetime


class BalanceGameCommentListResponse(BaseModel):
    items: list[BalanceGameCommentResponse]


@balance_game_router.post(
    "/balance/{game_id}/comments", status_code=status.HTTP_201_CREATED
)
def create_balance_game_comment(
    game_id: str,
    request: CreateBalanceGameCommentRequest,
    game_repo: BalanceGameRepositoryPort = Depends(get_balance_game_repository),
    comment_repo: CommentRepositoryPort = Depends(get_comment_repository),
    user_repo: UserRepositoryPort = Depends(get_user_repository),
) -> BalanceGameCommentResponse:
    """밸런스 게임 댓글 작성"""
    use_case = AddBalanceGameCommentUseCase(
        comment_repository=comment_repo,
        balance_game_repository=game_repo,
    )

    try:
        comment_id = use_case.execute(
            game_id=game_id,
            author_id=request.author_id,
            content=request.content,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )

    # 작성자 MBTI 조회
    user = user_repo.find_by_id(request.author_id)
    author_mbti = user.mbti.value if user and user.mbti else None

    return BalanceGameCommentResponse(
        id=comment_id,
        game_id=game_id,
        author_id=request.author_id,
        author_mbti=author_mbti,
        content=request.content,
        created_at=datetime.now(),
    )


@balance_game_router.get("/balance/{game_id}/comments")
def get_balance_game_comments(
    game_id: str,
    game_repo: BalanceGameRepositoryPort = Depends(get_balance_game_repository),
    comment_repo: CommentRepositoryPort = Depends(get_comment_repository),
    user_repo: UserRepositoryPort = Depends(get_user_repository),
) -> BalanceGameCommentListResponse:
    """밸런스 게임 댓글 목록 조회"""
    use_case = GetBalanceGameCommentsUseCase(
        comment_repository=comment_repo,
        balance_game_repository=game_repo,
        user_repository=user_repo,
    )

    try:
        comments = use_case.execute(game_id=game_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )

    items = [
        BalanceGameCommentResponse(
            id=comment.id,
            game_id=comment.game_id,
            author_id=comment.author_id,
            author_mbti=comment.author_mbti,
            content=comment.content,
            created_at=comment.created_at,
        )
        for comment in comments
    ]

    return BalanceGameCommentListResponse(items=items)


# ================= List & Detail Endpoints =================


@balance_game_router.get("/balance")
def get_balance_game_list(
    game_repo: BalanceGameRepositoryPort = Depends(get_balance_game_repository),
    vote_repo: BalanceVoteRepositoryPort = Depends(get_balance_vote_repository),
    comment_repo: CommentRepositoryPort = Depends(get_comment_repository),
) -> BalanceGameListResponse:
    """밸런스 게임 목록 조회"""
    use_case = GetBalanceGameListUseCase(
        balance_game_repository=game_repo,
        balance_vote_repository=vote_repo,
        comment_repository=comment_repo,
    )

    games = use_case.execute()

    items = [
        BalanceGameListItemResponse(
            id=game.id,
            question=game.question,
            option_left=game.option_left,
            option_right=game.option_right,
            left_percentage=game.left_percentage,
            right_percentage=game.right_percentage,
            comment_count=game.comment_count,
            is_votable=game.is_votable,
            week_of=game.week_of,
            created_at=game.created_at,
        )
        for game in games
    ]

    return BalanceGameListResponse(items=items)


@balance_game_router.get("/balance/{game_id}")
def get_balance_game_detail(
    game_id: str,
    game_repo: BalanceGameRepositoryPort = Depends(get_balance_game_repository),
    vote_repo: BalanceVoteRepositoryPort = Depends(get_balance_vote_repository),
    comment_repo: CommentRepositoryPort = Depends(get_comment_repository),
    user_repo: UserRepositoryPort = Depends(get_user_repository),
) -> BalanceGameDetailResponse:
    """밸런스 게임 상세 조회"""
    use_case = GetBalanceGameByIdUseCase(
        balance_game_repository=game_repo,
        balance_vote_repository=vote_repo,
        comment_repository=comment_repo,
        user_repository=user_repo,
    )

    try:
        detail = use_case.execute(game_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )

    comments = [
        BalanceGameDetailCommentResponse(
            id=comment.id,
            author_id=comment.author_id,
            author_mbti=comment.author_mbti,
            content=comment.content,
            created_at=comment.created_at,
        )
        for comment in detail.comments
    ]

    return BalanceGameDetailResponse(
        id=detail.id,
        question=detail.question,
        option_left=detail.option_left,
        option_right=detail.option_right,
        week_of=detail.week_of,
        total_votes=detail.total_votes,
        left_votes=detail.left_votes,
        right_votes=detail.right_votes,
        left_percentage=detail.left_percentage,
        right_percentage=detail.right_percentage,
        comments=comments,
        is_votable=detail.is_votable,
        created_at=detail.created_at,
    )