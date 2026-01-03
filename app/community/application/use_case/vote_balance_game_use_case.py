import uuid
from datetime import datetime, timedelta

from app.community.application.port.balance_game_repository_port import BalanceGameRepositoryPort
from app.community.application.port.balance_vote_repository_port import BalanceVoteRepositoryPort
from app.community.domain.balance_game import BalanceVote, VoteChoice


class VoteBalanceGameUseCase:
    """밸런스 게임 투표 유스케이스"""

    VOTABLE_DAYS = 30  # 투표 가능 기간 (일)

    def __init__(
        self,
        game_repository: BalanceGameRepositoryPort,
        vote_repository: BalanceVoteRepositoryPort,
    ):
        self._game_repository = game_repository
        self._vote_repository = vote_repository

    def execute(
        self,
        game_id: str,
        user_id: str,
        user_mbti: str,
        choice: VoteChoice,
    ) -> str:
        """밸런스 게임에 투표하고 vote_id를 반환한다"""
        # 게임 존재 여부 확인
        game = self._game_repository.find_by_id(game_id)
        if game is None:
            raise ValueError("게임을 찾을 수 없습니다")

        # 게임 활성화 여부 확인
        if not game.is_active:
            raise ValueError("비활성화된 게임입니다")

        # 투표 기간 확인 (30일 이내)
        if not self._is_votable(game.created_at):
            raise ValueError("투표 기간이 종료되었습니다")

        # 중복 투표 확인
        existing_vote = self._vote_repository.find_by_game_and_user(game_id, user_id)
        if existing_vote is not None:
            raise ValueError("이미 투표했습니다")

        # 투표 생성 및 저장
        vote = BalanceVote(
            id=str(uuid.uuid4()),
            game_id=game_id,
            user_id=user_id,
            user_mbti=user_mbti,
            choice=choice,
        )
        self._vote_repository.save(vote)

        return vote.id

    def _is_votable(self, created_at: datetime) -> bool:
        """투표 가능 여부를 판단한다 (생성 후 30일 이내)"""
        cutoff = datetime.now() - timedelta(days=self.VOTABLE_DAYS)
        return created_at > cutoff
