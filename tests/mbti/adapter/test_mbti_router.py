import uuid
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

# This fixture is based on app/test_main.py
@pytest.fixture
def client():
    """Mock lifespan events for testing without a real DB connection."""
    with patch('config.database.engine') as mock_engine:
        with patch('config.database.Base') as mock_base:
            mock_engine.dispose = MagicMock()
            from app.main import app
            with TestClient(app) as c:
                yield c


def test_start_mbti_test_endpoint(client: TestClient):
    # Given
    user_id = uuid.uuid4()
    request_data = {"user_id": str(user_id)}

    # When
    response = client.post("/mbti_test-test/start", json=request_data)

    # Then
    assert response.status_code == 200
    response_json = response.json()
    assert "session_id" in response_json
    assert "first_question" in response_json

    # Validate session_id is a UUID
    try:
        uuid.UUID(response_json["session_id"])
    except ValueError:
        pytest.fail("session_id is not a valid UUID")

    # Check if the question is a non-empty string
    assert isinstance(response_json["first_question"], str)
    assert len(response_json["first_question"]) > 0
