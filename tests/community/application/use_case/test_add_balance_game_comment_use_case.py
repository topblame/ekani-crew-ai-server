from datetime import datetime, timedelta

import pytest

from app.community.domain.balance_game import BalanceGame
from app.community.application.use_case.add_balance_game_comment_use_case import (
    AddBalanceGameCommentUseCase,
)
from tests.community.fixtures.fake_balance_game_repository import (
    FakeBalanceGameRepository,
)
from tests.community.fixtures.fake_comment_repository import FakeCommentRepository


class TestAddBalanceGameCommentUseCase:
    """AddBalanceGameCommentUseCase 테스트"""

    def setup_method(self):
        self.game_repo = FakeBalanceGameRepository()
        self.comment_repo = FakeCommentRepository()
        self.use_case = AddBalanceGameCommentUseCase(
            comment_repository=self.comment_repo,
            balance_game_repository=self.game_repo,
        )

    def test_댓글_작성_성공(self):
        """댓글을 성공적으로 작성한다"""
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

        comment_id = self.use_case.execute(
            game_id="game-1",
            author_id="user-1",
            content="첫 번째 댓글입니다",
        )

        assert comment_id is not None
        comments = self.comment_repo.find_by_target("balance_game", "game-1")
        assert len(comments) == 1
        assert comments[0].content == "첫 번째 댓글입니다"

    def test_존재하지_않는_게임에_댓글_작성시_에러(self):
        """존재하지 않는 게임에 댓글 작성 시 에러 발생"""
        with pytest.raises(ValueError, match="밸런스 게임을 찾을 수 없습니다"):
            self.use_case.execute(
                game_id="non-existent",
                author_id="user-1",
                content="댓글",
            )

    def test_만료된_게임에_댓글_작성시_에러(self):
        """한 달이 경과한 게임에 댓글 작성 시 에러 발생"""
        expired_game = BalanceGame(
            id="game-expired",
            question="만료된 게임",
            option_left="왼쪽",
            option_right="오른쪽",
            week_of="2024-W01",
            is_active=True,
            created_at=datetime.now() - timedelta(days=35),
        )
        self.game_repo.save(expired_game)

        with pytest.raises(ValueError, match="댓글 작성 기간이 종료되었습니다"):
            self.use_case.execute(
                game_id="game-expired",
                author_id="user-1",
                content="만료된 게임에 댓글",
            )