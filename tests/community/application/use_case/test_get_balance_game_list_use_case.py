from datetime import datetime, timedelta

import pytest

from app.community.domain.balance_game import BalanceGame, BalanceVote, VoteChoice
from app.community.domain.comment import Comment
from app.community.application.use_case.get_balance_game_list_use_case import (
    GetBalanceGameListUseCase,
    BalanceGameListItem,
)
from tests.community.fixtures.fake_balance_game_repository import (
    FakeBalanceGameRepository,
)
from tests.community.fixtures.fake_balance_vote_repository import (
    FakeBalanceVoteRepository,
)
from tests.community.fixtures.fake_comment_repository import FakeCommentRepository


class TestGetBalanceGameListUseCase:
    """GetBalanceGameListUseCase 테스트"""

    def setup_method(self):
        self.game_repo = FakeBalanceGameRepository()
        self.vote_repo = FakeBalanceVoteRepository()
        self.comment_repo = FakeCommentRepository()
        self.use_case = GetBalanceGameListUseCase(
            balance_game_repository=self.game_repo,
            balance_vote_repository=self.vote_repo,
            comment_repository=self.comment_repo,
        )

    def test_빈_목록_조회(self):
        """게임이 없으면 빈 목록을 반환한다"""
        result = self.use_case.execute()

        assert result == []

    def test_게임_목록_조회(self):
        """게임 목록을 조회한다"""
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

        result = self.use_case.execute()

        assert len(result) == 1
        assert result[0].id == "game-1"
        assert result[0].question == "짜장면 vs 짬뽕"

    def test_투표_퍼센티지_포함(self):
        """목록에 투표 퍼센티지가 포함된다"""
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

        result = self.use_case.execute()

        assert result[0].left_percentage == 75.0
        assert result[0].right_percentage == 25.0

    def test_댓글_수_포함(self):
        """목록에 댓글 수가 포함된다"""
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

        # 댓글 3개 추가
        for i in range(3):
            self.comment_repo.save(
                Comment(
                    id=f"comment-{i}",
                    target_type="balance_game",
                    target_id="game-1",
                    author_id=f"user-{i}",
                    content=f"댓글 {i}",
                )
            )

        result = self.use_case.execute()

        assert result[0].comment_count == 3

    def test_한달_이내_게임은_투표_가능(self):
        """한 달 이내에 생성된 게임은 투표 가능하다"""
        game = BalanceGame(
            id="game-1",
            question="짜장면 vs 짬뽕",
            option_left="짜장면",
            option_right="짬뽕",
            week_of="2024-W01",
            is_active=True,
            created_at=datetime.now() - timedelta(days=15),  # 15일 전
        )
        self.game_repo.save(game)

        result = self.use_case.execute()

        assert result[0].is_votable is True

    def test_한달_경과_게임은_투표_불가(self):
        """한 달이 경과한 게임은 투표 불가하다"""
        game = BalanceGame(
            id="game-1",
            question="짜장면 vs 짬뽕",
            option_left="짜장면",
            option_right="짬뽕",
            week_of="2024-W01",
            is_active=False,
            created_at=datetime.now() - timedelta(days=35),  # 35일 전
        )
        self.game_repo.save(game)

        result = self.use_case.execute()

        assert result[0].is_votable is False

    def test_최신순_정렬(self):
        """게임 목록은 최신순으로 정렬된다"""
        for i in range(3):
            game = BalanceGame(
                id=f"game-{i}",
                question=f"질문 {i}",
                option_left="왼쪽",
                option_right="오른쪽",
                week_of=f"2024-W0{i+1}",
                is_active=i == 2,  # 마지막만 active
                created_at=datetime.now() - timedelta(days=30 - i * 10),
            )
            self.game_repo.save(game)

        result = self.use_case.execute()

        assert len(result) == 3
        assert result[0].id == "game-2"  # 가장 최신
        assert result[1].id == "game-1"
        assert result[2].id == "game-0"  # 가장 오래됨