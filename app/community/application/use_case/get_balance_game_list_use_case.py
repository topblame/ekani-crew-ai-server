from dataclasses import dataclass
from datetime import datetime, timedelta

from app.community.application.port.balance_game_repository_port import (
    BalanceGameRepositoryPort,
)
from app.community.application.port.balance_vote_repository_port import (
    BalanceVoteRepositoryPort,
)
from app.community.application.port.comment_repository_port import CommentRepositoryPort
from app.community.domain.balance_game import VoteChoice


@dataclass
class BalanceGameListItem:
    """밸런스 게임 목록 아이템"""

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


class GetBalanceGameListUseCase:
    """밸런스 게임 목록 조회 유스케이스"""

    VOTABLE_DAYS = 30  # 투표 가능 기간 (일)

    def __init__(
        self,
        balance_game_repository: BalanceGameRepositoryPort,
        balance_vote_repository: BalanceVoteRepositoryPort,
        comment_repository: CommentRepositoryPort,
    ):
        self._game_repo = balance_game_repository
        self._vote_repo = balance_vote_repository
        self._comment_repo = comment_repository

    def execute(self) -> list[BalanceGameListItem]:
        """밸런스 게임 목록을 조회한다"""
        games = self._game_repo.find_all()

        result = []
        for game in games:
            left_count = self._vote_repo.count_by_choice(game.id, VoteChoice.LEFT)
            right_count = self._vote_repo.count_by_choice(game.id, VoteChoice.RIGHT)
            total = left_count + right_count

            left_percentage = (left_count / total * 100) if total > 0 else 0.0
            right_percentage = (right_count / total * 100) if total > 0 else 0.0

            comment_count = self._comment_repo.count_by_target(
                "balance_game", game.id
            )

            is_votable = self._is_votable(game.created_at)

            result.append(
                BalanceGameListItem(
                    id=game.id,
                    question=game.question,
                    option_left=game.option_left,
                    option_right=game.option_right,
                    left_percentage=left_percentage,
                    right_percentage=right_percentage,
                    comment_count=comment_count,
                    is_votable=is_votable,
                    week_of=game.week_of,
                    created_at=game.created_at,
                )
            )

        return result

    def _is_votable(self, created_at: datetime) -> bool:
        """투표 가능 여부를 판단한다 (생성 후 30일 이내)"""
        cutoff = datetime.now() - timedelta(days=self.VOTABLE_DAYS)
        return created_at > cutoff