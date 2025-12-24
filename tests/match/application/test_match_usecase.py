import pytest
from app.shared.vo.mbti import MBTI
from app.match.application.usecase.match_usecase import MatchUseCase
from tests.match.fixtures.fake_match_queue_adapter import FakeMatchQueueAdapter


@pytest.mark.asyncio
async def test_request_match_should_enqueue_user():
    # Given
    fake_adapter = FakeMatchQueueAdapter()
    usecase = MatchUseCase(match_queue_port=fake_adapter)
    user_id = "user_test"
    mbti = MBTI("ENTP")

    # When
    result = await usecase.request_match(user_id, mbti)

    # Then
    assert result["status"] == "waiting"
    assert result["wait_count"] == 1

    # 큐에 실제로 들어갔는지 확인
    assert await fake_adapter.get_queue_size(mbti) == 1


@pytest.mark.asyncio
async def test_request_match_duplicate_user():
    # Given
    fake_adapter = FakeMatchQueueAdapter()
    usecase = MatchUseCase(match_queue_port=fake_adapter)
    user_id = "user_test"
    mbti = MBTI("ENTP")

    # 첫 번째 요청
    await usecase.request_match(user_id, mbti)

    # When (두 번째 요청)
    result = await usecase.request_match(user_id, mbti)

    # Then
    assert result["status"] == "already_waiting"
    assert result["wait_count"] == 1  # 카운트가 늘어나지 않아야 함


@pytest.mark.asyncio
async def test_cancel_match_should_remove_user():
    # Given
    fake_adapter = FakeMatchQueueAdapter()
    usecase = MatchUseCase(match_queue_port=fake_adapter)
    user_id = "user_cancel"
    mbti = MBTI("INFP")

    await usecase.request_match(user_id, mbti)
    assert await fake_adapter.get_queue_size(mbti) == 1

    # When
    result = await usecase.cancel_match(user_id, mbti)

    # Then
    assert result["status"] == "cancelled"
    assert await fake_adapter.get_queue_size(mbti) == 0