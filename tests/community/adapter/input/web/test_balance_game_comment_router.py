from datetime import datetime

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.community.adapter.input.web.balance_game_router import (
    balance_game_router,
    get_balance_game_repository,
    get_comment_repository,
    get_user_repository,
)
from app.community.domain.balance_game import BalanceGame
from app.community.domain.comment import Comment
from app.shared.vo.mbti import MBTI
from app.user.domain.user import User
from tests.community.fixtures.fake_balance_game_repository import (
    FakeBalanceGameRepository,
)
from tests.community.fixtures.fake_comment_repository import FakeCommentRepository
from tests.user.fixtures.fake_user_repository import FakeUserRepository


@pytest.fixture
def fake_balance_game_repository():
    return FakeBalanceGameRepository()


@pytest.fixture
def fake_comment_repository():
    return FakeCommentRepository()


@pytest.fixture
def fake_user_repository():
    return FakeUserRepository()


@pytest.fixture
def client(fake_balance_game_repository, fake_comment_repository, fake_user_repository):
    app = FastAPI()
    app.include_router(balance_game_router, prefix="/community")

    def override_balance_game_repository():
        return fake_balance_game_repository

    def override_comment_repository():
        return fake_comment_repository

    def override_user_repository():
        return fake_user_repository

    app.dependency_overrides[get_balance_game_repository] = override_balance_game_repository
    app.dependency_overrides[get_comment_repository] = override_comment_repository
    app.dependency_overrides[get_user_repository] = override_user_repository
    return TestClient(app)


class TestBalanceGameCommentRouter:
    """Balance Game Comment API 라우터 테스트"""

    def test_create_balance_game_comment(
        self, client, fake_balance_game_repository, fake_comment_repository
    ):
        """밸런스 게임에 댓글을 작성할 수 있다"""
        # Given
        game = BalanceGame(
            id="game-1",
            question="MBTI로 연인 고를 때 뭐가 중요해?",
            option_left="성격 궁합",
            option_right="외모",
            week_of=datetime(2025, 1, 6),
            is_active=True,
        )
        fake_balance_game_repository.save(game)

        # When
        response = client.post(
            "/community/balance/game-1/comments",
            json={
                "author_id": "user-1",
                "content": "성격 궁합이 더 중요하지!",
            },
        )

        # Then
        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert data["content"] == "성격 궁합이 더 중요하지!"
        assert data["author_id"] == "user-1"

    def test_create_balance_game_comment_game_not_found(self, client):
        """존재하지 않는 밸런스 게임에 댓글 작성 시 404를 반환한다"""
        response = client.post(
            "/community/balance/non-existent/comments",
            json={
                "author_id": "user-1",
                "content": "댓글 내용",
            },
        )

        assert response.status_code == 404

    def test_get_balance_game_comments(
        self,
        client,
        fake_balance_game_repository,
        fake_comment_repository,
        fake_user_repository,
    ):
        """밸런스 게임의 댓글 목록을 조회할 수 있다"""
        # Given
        game = BalanceGame(
            id="game-1",
            question="테스트 질문",
            option_left="왼쪽",
            option_right="오른쪽",
            week_of=datetime(2025, 1, 6),
            is_active=True,
        )
        fake_balance_game_repository.save(game)

        user = User(
            id="user-2",
            email="user2@test.com",
            mbti=MBTI("ENFP"),
        )
        fake_user_repository.save(user)

        comment = Comment(
            id="comment-1",
            target_type="balance_game",
            target_id="game-1",
            author_id="user-2",
            content="ENFP는 외모도 중요해!",
            created_at=datetime(2025, 1, 1, 12, 0, 0),
        )
        fake_comment_repository.save(comment)

        # When
        response = client.get("/community/balance/game-1/comments")

        # Then
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["content"] == "ENFP는 외모도 중요해!"
        assert data["items"][0]["author_mbti"] == "ENFP"

    def test_get_balance_game_comments_game_not_found(self, client):
        """존재하지 않는 밸런스 게임의 댓글 조회 시 404를 반환한다"""
        response = client.get("/community/balance/non-existent/comments")

        assert response.status_code == 404