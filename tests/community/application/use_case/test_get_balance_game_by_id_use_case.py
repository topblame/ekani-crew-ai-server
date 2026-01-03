from datetime import datetime, timedelta

import pytest

from app.community.domain.balance_game import BalanceGame, BalanceVote, VoteChoice
from app.community.domain.comment import Comment
from app.community.application.use_case.get_balance_game_by_id_use_case import (
    GetBalanceGameByIdUseCase,
    BalanceGameDetail,
    BalanceGameCommentDTO,
)
from tests.community.fixtures.fake_balance_game_repository import (
    FakeBalanceGameRepository,
)
from tests.community.fixtures.fake_balance_vote_repository import (
    FakeBalanceVoteRepository,
)
from tests.community.fixtures.fake_comment_repository import FakeCommentRepository
from tests.user.fixtures.fake_user_repository import FakeUserRepository
from app.user.domain.user import User
from app.shared.vo.mbti import MBTI


class TestGetBalanceGameByIdUseCase:
    """GetBalanceGameByIdUseCase 테스트"""

    def setup_method(self):
        self.game_repo = FakeBalanceGameRepository()
        self.vote_repo = FakeBalanceVoteRepository()
        self.comment_repo = FakeCommentRepository()
        self.user_repo = FakeUserRepository()
        self.use_case = GetBalanceGameByIdUseCase(
            balance_game_repository=self.game_repo,
            balance_vote_repository=self.vote_repo,
            comment_repository=self.comment_repo,
            user_repository=self.user_repo,
        )

    def test_존재하지_않는_게임_조회시_에러(self):
        """존재하지 않는 게임 ID로 조회 시 ValueError를 발생시킨다"""
        with pytest.raises(ValueError, match="게임을 찾을 수 없습니다"):
            self.use_case.execute("non-existent-id")

    def test_게임_상세_조회(self):
        """게임 상세를 조회한다"""
        game = BalanceGame(
            id="game-1",
            question="짜장면 vs 짬뽕",
            option_left="짜장면",
            option_right="짬뽕",
            week_of="2024-W01",
            is_active=True,
            created_at=datetime.now(),
        )
        self.game_repo.save(game)

        result = self.use_case.execute("game-1")

        assert result.id == "game-1"
        assert result.question == "짜장면 vs 짬뽕"
        assert result.option_left == "짜장면"
        assert result.option_right == "짬뽕"

    def test_투표_결과_포함(self):
        """상세에 투표 결과가 포함된다"""
        game = BalanceGame(
            id="game-1",
            question="짜장면 vs 짬뽕",
            option_left="짜장면",
            option_right="짬뽕",
            week_of="2024-W01",
            is_active=True,
            created_at=datetime.now(),
        )
        self.game_repo.save(game)

        # 3:1 투표
        for i in range(3):
            self.vote_repo.save(
                BalanceVote(
                    id=f"vote-left-{i}",
                    game_id="game-1",
                    user_id=f"user-{i}",
                    user_mbti="INTJ",
                    choice=VoteChoice.LEFT,
                )
            )
        self.vote_repo.save(
            BalanceVote(
                id="vote-right-1",
                game_id="game-1",
                user_id="user-3",
                user_mbti="ENFP",
                choice=VoteChoice.RIGHT,
            )
        )

        result = self.use_case.execute("game-1")

        assert result.total_votes == 4
        assert result.left_votes == 3
        assert result.right_votes == 1
        assert result.left_percentage == 75.0
        assert result.right_percentage == 25.0

    def test_댓글_목록_포함(self):
        """상세에 댓글 목록이 포함된다"""
        game = BalanceGame(
            id="game-1",
            question="짜장면 vs 짬뽕",
            option_left="짜장면",
            option_right="짬뽕",
            week_of="2024-W01",
            is_active=True,
            created_at=datetime.now(),
        )
        self.game_repo.save(game)

        # 사용자 생성
        user = User(id="user-1", email="test@test.com", mbti=MBTI("INTJ"))
        self.user_repo.save(user)

        # 댓글 추가
        self.comment_repo.save(
            Comment(
                id="comment-1",
                target_type="balance_game",
                target_id="game-1",
                author_id="user-1",
                content="첫 번째 댓글",
            )
        )

        result = self.use_case.execute("game-1")

        assert len(result.comments) == 1
        assert result.comments[0].id == "comment-1"
        assert result.comments[0].content == "첫 번째 댓글"
        assert result.comments[0].author_mbti == "INTJ"

    def test_한달_이내_게임은_투표_가능(self):
        """한 달 이내에 생성된 게임은 투표 가능하다"""
        game = BalanceGame(
            id="game-1",
            question="짜장면 vs 짬뽕",
            option_left="짜장면",
            option_right="짬뽕",
            week_of="2024-W01",
            is_active=True,
            created_at=datetime.now() - timedelta(days=15),
        )
        self.game_repo.save(game)

        result = self.use_case.execute("game-1")

        assert result.is_votable is True

    def test_한달_경과_게임은_투표_불가(self):
        """한 달이 경과한 게임은 투표 불가하다"""
        game = BalanceGame(
            id="game-1",
            question="짜장면 vs 짬뽕",
            option_left="짜장면",
            option_right="짬뽕",
            week_of="2024-W01",
            is_active=False,
            created_at=datetime.now() - timedelta(days=35),
        )
        self.game_repo.save(game)

        result = self.use_case.execute("game-1")

        assert result.is_votable is False
