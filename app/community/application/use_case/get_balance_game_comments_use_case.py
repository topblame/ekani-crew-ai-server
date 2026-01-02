from dataclasses import dataclass
from datetime import datetime

from app.community.application.port.balance_game_repository_port import (
    BalanceGameRepositoryPort,
)
from app.community.application.port.comment_repository_port import CommentRepositoryPort
from app.user.application.port.user_repository_port import UserRepositoryPort


@dataclass
class BalanceGameCommentWithAuthorMBTI:
    """작성자 MBTI를 포함한 밸런스 게임 댓글 정보"""

    id: str
    game_id: str
    author_id: str
    author_mbti: str | None
    content: str
    created_at: datetime


class GetBalanceGameCommentsUseCase:
    """밸런스 게임 댓글 목록 조회 유스케이스"""

    def __init__(
        self,
        comment_repository: CommentRepositoryPort,
        balance_game_repository: BalanceGameRepositoryPort,
        user_repository: UserRepositoryPort,
    ):
        self._comment_repository = comment_repository
        self._balance_game_repository = balance_game_repository
        self._user_repository = user_repository

    def execute(self, game_id: str) -> list[BalanceGameCommentWithAuthorMBTI]:
        """밸런스 게임의 댓글 목록을 작성자 MBTI와 함께 조회한다"""
        # 밸런스 게임 존재 여부 확인
        game = self._balance_game_repository.find_by_id(game_id)
        if game is None:
            raise ValueError("밸런스 게임을 찾을 수 없습니다")

        # 댓글 조회 (시간순 정렬됨)
        comments = self._comment_repository.find_by_target("balance_game", game_id)

        # 작성자 MBTI 정보 조회 및 결과 생성
        result = []
        for comment in comments:
            user = self._user_repository.find_by_id(comment.author_id)
            author_mbti = user.mbti.value if user and user.mbti else None

            result.append(
                BalanceGameCommentWithAuthorMBTI(
                    id=comment.id,
                    game_id=game_id,
                    author_id=comment.author_id,
                    author_mbti=author_mbti,
                    content=comment.content,
                    created_at=comment.created_at,
                )
            )

        return result