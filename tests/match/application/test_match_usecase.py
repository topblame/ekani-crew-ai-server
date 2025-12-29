from unittest.mock import AsyncMock

import pytest
from app.shared.vo.mbti import MBTI
from app.match.application.usecase.match_usecase import MatchUseCase
from tests.match.fixtures.fake_match_queue_adapter import FakeMatchQueueAdapter


@pytest.mark.asyncio
async def test_request_match_should_enqueue_user():
    # Given
    fake_adapter = FakeMatchQueueAdapter()

    mock_chat_port = AsyncMock()
    mock_chat_port.create_chat_room.return_value = True

    usecase = MatchUseCase(
        match_queue_port=fake_adapter,
        chat_room_port=mock_chat_port,
        match_state_port=AsyncMock()
    )

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

    mock_chat_port = AsyncMock()
    mock_chat_port.create_chat_room.return_value = True

    usecase = MatchUseCase(
        match_queue_port=fake_adapter,
        chat_room_port=mock_chat_port,
        match_state_port=AsyncMock()
    )

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

    mock_chat_port = AsyncMock()
    mock_chat_port.create_chat_room.return_value = True

    usecase = MatchUseCase(
        match_queue_port=fake_adapter,
        chat_room_port=mock_chat_port,
        match_state_port=AsyncMock()
    )

    user_id = "user_cancel"
    mbti = MBTI("INFP")

    await usecase.request_match(user_id, mbti)
    assert await fake_adapter.get_queue_size(mbti) == 1

    # When
    result = await usecase.cancel_match(user_id, mbti)

    # Then
    await usecase.cancel_match(user_id, mbti)
    assert await fake_adapter.get_queue_size(mbti) == 0


@pytest.mark.asyncio
async def test_request_match_sends_websocket_notification_to_partner():
    # Given
    fake_queue_adapter = FakeMatchQueueAdapter()

    mock_chat_port = AsyncMock()
    mock_chat_port.create_chat_room.return_value = True

    mock_match_state_port = AsyncMock()
    mock_match_state_port.is_available_for_match.return_value = True # Partner is available

    mock_notification_port = AsyncMock()

    usecase = MatchUseCase(
        match_queue_port=fake_queue_adapter,
        chat_room_port=mock_chat_port,
        match_state_port=mock_match_state_port,
        match_notification_port=mock_notification_port
    )

    user_a_id = "user_A"
    user_a_mbti = MBTI("INFP")
    user_b_id = "user_B"
    user_b_mbti = MBTI("ENTJ") # Compatible with INFP

    # 1. User A requests match (goes into queue)
    await usecase.request_match(user_a_id, user_a_mbti)
    assert await fake_queue_adapter.is_user_in_queue(user_a_id, user_a_mbti) is True

    # 2. User B requests match (finds User A)
    result_b = await usecase.request_match(user_b_id, user_b_mbti)

    # Then
    # User B (requester) should get a 'matched' status via HTTP response
    assert result_b["status"] == "matched"
    assert result_b["partner"]["user_id"] == user_a_id
    assert "roomId" in result_b

    # User A (partner) should receive a WebSocket notification
    mock_notification_port.notify_match_success.assert_called_once()
    args, kwargs = mock_notification_port.notify_match_success.call_args
    
    notified_user_id = args[0]
    notification_payload = args[1]

    assert notified_user_id == user_a_id
    assert notification_payload["status"] == "matched"
    assert notification_payload["partner"]["user_id"] == user_b_id
    assert notification_payload["roomId"] == result_b["roomId"] # Same room ID
    
    # Verify state updates
    mock_match_state_port.set_matched.assert_any_call(
        user_id=user_a_id,
        mbti=user_a_mbti.value,
        room_id=result_b["roomId"],
        partner_id=user_b_id,
        expire_seconds=usecase.MATCH_EXPIRE_SECONDS
    )
    mock_match_state_port.set_matched.assert_any_call(
        user_id=user_b_id,
        mbti=user_b_mbti.value,
        room_id=result_b["roomId"],
        partner_id=user_a_id,
        expire_seconds=usecase.MATCH_EXPIRE_SECONDS
    )

    # Chat room should be created
    mock_chat_port.create_chat_room.assert_called_once()
    assert mock_chat_port.create_chat_room.call_args[0][0]["roomId"] == result_b["roomId"]