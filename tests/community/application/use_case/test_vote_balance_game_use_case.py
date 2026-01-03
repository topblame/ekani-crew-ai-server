import pytest
from datetime import datetime, timedelta

from app.community.domain.balance_game import BalanceGame, VoteChoice
from app.community.application.use_case.vote_balance_game_use_case import VoteBalanceGameUseCase
from tests.community.fixtures.fake_balance_game_repository import FakeBalanceGameRepository
from tests.community.fixtures.fake_balance_vote_repository import FakeBalanceVoteRepository


@pytest.fixture
def game_repository():
    return FakeBalanceGameRepository()


@pytest.fixture
def vote_repository():
    return FakeBalanceVoteRepository()


@pytest.fixture
def use_case(game_repository, vote_repository):
    return VoteBalanceGameUseCase(game_repository, vote_repository)


@pytest.fixture
def active_game(game_repository):
    game = BalanceGame(
        id="game-123",
        question="연인이 늦잠 자서 데이트에 30분 늦음",
        option_left="솔직하게 화난다고 말한다",
        option_right="괜찮다고 하고 넘어간다",
        week_of="2025-W01",
        is_active=True,
    )
    game_repository.save(game)
    return game


class TestVoteBalanceGameUseCase:
    """VoteBalanceGameUseCase 테스트"""

    def test_vote_left_successfully(self, use_case, active_game, vote_repository):
        """왼쪽 선택지에 투표할 수 있다"""
        # Given: 활성화된 게임과 사용자 정보
        user_id = "user-123"
        user_mbti = "INTJ"

        # When: 왼쪽에 투표하면
        vote_id = use_case.execute(
            game_id=active_game.id,
            user_id=user_id,
            user_mbti=user_mbti,
            choice=VoteChoice.LEFT,
        )

        # Then: 투표가 저장된다
        assert vote_id is not None
        saved_vote = vote_repository.find_by_game_and_user(active_game.id, user_id)
        assert saved_vote is not None
        assert saved_vote.choice == VoteChoice.LEFT
        assert saved_vote.user_mbti == "INTJ"

    def test_vote_right_successfully(self, use_case, active_game, vote_repository):
        """오른쪽 선택지에 투표할 수 있다"""
        # Given: 활성화된 게임과 사용자 정보
        user_id = "user-456"
        user_mbti = "ENFP"

        # When: 오른쪽에 투표하면
        vote_id = use_case.execute(
            game_id=active_game.id,
            user_id=user_id,
            user_mbti=user_mbti,
            choice=VoteChoice.RIGHT,
        )

        # Then: 투표가 저장된다
        assert vote_id is not None
        saved_vote = vote_repository.find_by_game_and_user(active_game.id, user_id)
        assert saved_vote is not None
        assert saved_vote.choice == VoteChoice.RIGHT

    def test_duplicate_vote_raises_error(self, use_case, active_game):
        """같은 게임에 중복 투표 시 에러 발생"""
        # Given: 이미 투표한 사용자
        user_id = "user-123"
        user_mbti = "INTJ"
        use_case.execute(
            game_id=active_game.id,
            user_id=user_id,
            user_mbti=user_mbti,
            choice=VoteChoice.LEFT,
        )

        # When/Then: 다시 투표하면 에러 발생
        with pytest.raises(ValueError, match="이미 투표했습니다"):
            use_case.execute(
                game_id=active_game.id,
                user_id=user_id,
                user_mbti=user_mbti,
                choice=VoteChoice.RIGHT,
            )

    def test_vote_on_nonexistent_game_raises_error(self, use_case):
        """존재하지 않는 게임에 투표 시 에러 발생"""
        # When/Then: 존재하지 않는 게임에 투표하면 에러 발생
        with pytest.raises(ValueError, match="게임을 찾을 수 없습니다"):
            use_case.execute(
                game_id="nonexistent-game",
                user_id="user-123",
                user_mbti="INTJ",
                choice=VoteChoice.LEFT,
            )

    def test_vote_on_inactive_game_raises_error(self, use_case, game_repository):
        """비활성화된 게임에 투표 시 에러 발생"""
        # Given: 비활성화된 게임
        inactive_game = BalanceGame(
            id="game-inactive",
            question="비활성 게임",
            option_left="왼쪽",
            option_right="오른쪽",
            week_of="2024-W52",
            is_active=False,
        )
        game_repository.save(inactive_game)

        # When/Then: 비활성 게임에 투표하면 에러 발생
        with pytest.raises(ValueError, match="비활성화된 게임입니다"):
            use_case.execute(
                game_id="game-inactive",
                user_id="user-123",
                user_mbti="INTJ",
                choice=VoteChoice.LEFT,
            )

    def test_vote_on_expired_game_raises_error(self, use_case, game_repository):
        """한 달이 경과한 게임에 투표 시 에러 발생"""
        # Given: 35일 전에 생성된 게임
        expired_game = BalanceGame(
            id="game-expired",
            question="만료된 게임",
            option_left="왼쪽",
            option_right="오른쪽",
            week_of="2024-W01",
            is_active=True,  # 아직 활성 상태
            created_at=datetime.now() - timedelta(days=35),
        )
        game_repository.save(expired_game)

        # When/Then: 만료된 게임에 투표하면 에러 발생
        with pytest.raises(ValueError, match="투표 기간이 종료되었습니다"):
            use_case.execute(
                game_id="game-expired",
                user_id="user-123",
                user_mbti="INTJ",
                choice=VoteChoice.LEFT,
            )
