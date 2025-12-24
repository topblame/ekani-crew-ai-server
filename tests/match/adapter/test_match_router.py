import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from app.match.application.usecase.match_usecase import MatchUseCase
from tests.match.fixtures.fake_match_queue_adapter import FakeMatchQueueAdapter


# Fixture: app/test_main.py와 동일한 방식의 Mock Client
@pytest.fixture
def client():
    with patch('config.database.engine') as mock_engine:
        with patch('config.database.Base') as mock_base:
            mock_engine.dispose = MagicMock()
            from app.main import app
            with TestClient(app) as c:
                yield c


# Fixture: Fake Adapter가 주입된 UseCase를 반환하는 Mock Factory
@pytest.fixture
def mock_usecase_factory():
    fake_adapter = FakeMatchQueueAdapter()
    # 상태 유지를 위해 factory 호출 시마다 매번 새로운 fake_adapter가 아닌,
    # 이 테스트 함수 내에서 공유되는 adapter를 가진 usecase를 반환하도록 함
    usecase_instance = MatchUseCase(match_queue_port=fake_adapter)

    # Factory.create()가 호출될 때 이 usecase_instance를 반환하게 설정
    with patch("app.match.application.factory.match_usecase_factory.MatchUseCaseFactory.create") as mock_create:
        mock_create.return_value = usecase_instance
        yield fake_adapter  # 테스트 코드에서 adapter 상태 확인용으로 반환


def test_request_match_endpoint(client, mock_usecase_factory):
    # Given
    request_data = {
        "user_id": "api_user_1",
        "mbti": "INTJ"
    }

    # When
    response = client.post("/match/request", json=request_data)

    # Then
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "waiting"
    assert data["my_mbti"] == "INTJ"
    assert data["wait_count"] == 1


def test_get_queue_status_endpoint(client, mock_usecase_factory):
    # Given: 미리 유저 한 명 등록 (Mock Factory 덕분에 같은 Adapter 공유)
    client.post("/match/request", json={"user_id": "user_q1", "mbti": "ENTP"})
    client.post("/match/request", json={"user_id": "user_q2", "mbti": "ENTP"})

    # When
    response = client.get("/match/queue/ENTP")

    # Then
    assert response.status_code == 200
    data = response.json()
    assert data["mbti"] == "ENTP"
    assert data["waiting_count"] == 2


def test_cancel_match_endpoint(client, mock_usecase_factory):
    # Given
    client.post("/match/request", json={"user_id": "user_c1", "mbti": "ISFP"})

    # When
    response = client.post("/match/cancel", json={"user_id": "user_c1", "mbti": "ISFP"})

    # Then
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "cancelled"

    # 큐 확인
    status_res = client.get("/match/queue/ISFP")
    assert status_res.json()["waiting_count"] == 0