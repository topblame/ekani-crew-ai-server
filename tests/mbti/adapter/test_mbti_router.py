import uuid
import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from fastapi import FastAPI

from app.mbti_test.adapter.input.web.mbti_router import mbti_router
from app.auth.domain.session import Session


@pytest.fixture
def app():
    """테스트용 FastAPI 앱"""
    app = FastAPI()
    app.include_router(mbti_router, prefix="/mbti-test")
    return app


@pytest.fixture
def client(app):
    """테스트 클라이언트"""
    return TestClient(app)


def mock_session(session: Session):
    """세션 인증을 모킹하는 컨텍스트 매니저"""
    mock_repo = AsyncMock()
    mock_repo.find_by_session_id.return_value = session
    return patch(
        "app.auth.adapter.input.web.auth_dependency.RedisSessionRepository",
        return_value=mock_repo
    )


def test_start_mbti_test_endpoint(client: TestClient):
    # Given
    user_id = uuid.uuid4()
    session = Session(session_id="valid-session", user_id=str(user_id))

    # When
    with mock_session(session):
        response = client.post(
            "/mbti-test/start?test_type=ai",
            cookies={"session_id": "valid-session"}
        )

    # Then
    assert response.status_code == 200
    response_json = response.json()
    assert "session" in response_json
    assert "first_question" in response_json


def test_start_mbti_test_without_auth_returns_401(client: TestClient):


    # When


    response = client.post("/mbti-test/start?test_type=ai")





    # Then


    assert response.status_code == 401








def test_answer_question_chat_endpoint(client: TestClient):








    # Given








    user_id = uuid.uuid4()








    session = Session(session_id="valid-session", user_id=str(user_id))

















    with mock_session(session):








        # 1. Start test to get session_id








        start_response = client.post(








            "/mbti-test/start",








            cookies={"session_id": "valid-session"}








        )








        assert start_response.status_code == 200








        session_id = start_response.json()["session"]["id"]

















        # 2. Post an answer to the chat endpoint (for the greeting)








        chat_response_1 = client.post(








            f"/mbti-test/{session_id}/chat",








            json={"content": "Hi"},








            cookies={"session_id": "valid-session"}








        )








        assert chat_response_1.status_code == 200








        response_json_1 = chat_response_1.json()








        assert response_json_1["question_number"] == 1

















        # 3. Post a second answer (for the first real question)








        chat_response_2 = client.post(








            f"/mbti-test/{session_id}/chat",








            json={"content": "My real answer"},








            cookies={"session_id": "valid-session"}








        )

















    # Then








    assert chat_response_2.status_code == 200








    response_json_2 = chat_response_2.json()








    assert "next_question" in response_json_2








    assert response_json_2["question_number"] == 2










