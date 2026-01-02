import uuid

from app.community.application.port.balance_game_repository_port import (
    BalanceGameRepositoryPort,
)
from app.community.application.port.comment_repository_port import CommentRepositoryPort
from app.community.domain.comment import Comment


class AddBalanceGameCommentUseCase:
    """밸런스 게임 댓글 작성 유스케이스"""

    def __init__(
        self,
        comment_repository: CommentRepositoryPort,
        balance_game_repository: BalanceGameRepositoryPort,
    ):
        self._comment_repository = comment_repository
        self._balance_game_repository = balance_game_repository

    def execute(self, game_id: str, author_id: str, content: str) -> str:
        """밸런스 게임에 댓글을 추가하고 comment_id를 반환한다"""
        # 밸런스 게임 존재 여부 확인
        game = self._balance_game_repository.find_by_id(game_id)
        if game is None:
            raise ValueError("밸런스 게임을 찾을 수 없습니다")

        # 댓글 생성 및 저장
        comment = Comment(
            id=str(uuid.uuid4()),
            target_type="balance_game",
            target_id=game_id,
            author_id=author_id,
            content=content,
        )
        self._comment_repository.save(comment)

        return comment.id