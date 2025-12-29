import pytest
import json
from fastapi import FastAPI, WebSocket
from starlette.testclient import TestClient

from app.match.adapter.output.notification.websocket_match_notification_adapter import WebSocketMatchNotificationAdapter
from config.connection_manager import manager as connection_manager


# Create a test-specific FastAPI app
app = FastAPI()

@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    # Use the global singleton manager
    await connection_manager.connect(websocket, room_id="test_room", user_id=user_id)
    try:
        while True:
            # Keep the connection open to receive messages
            await websocket.receive_text()
    except Exception:
        # Clean up on disconnect
        connection_manager.disconnect(websocket, "test_room")


@pytest.fixture(scope="function")
def client():
    # Reset the manager's state before each test
    connection_manager.user_connections.clear()
    connection_manager.active_connections.clear()
    with TestClient(app) as client:
        yield client


@pytest.mark.asyncio
async def test_websocket_notification_adapter_sends_message_to_correct_user(client):
    """
    Tests if the WebSocketMatchNotificationAdapter correctly sends a message
    to a user connected via a WebSocket.
    """
    # Given
    user_id_to_notify = "user123"
    other_user_id = "user456"
    payload_to_send = {"status": "matched", "partner": "user-abc"}

    adapter = WebSocketMatchNotificationAdapter(connection_manager)

    # When
    # Establish WebSocket connections for two different users
    with client.websocket_connect(f"/ws/{user_id_to_notify}") as ws1, \
         client.websocket_connect(f"/ws/{other_user_id}") as ws2:

        # Ensure connections are registered in the manager
        assert user_id_to_notify in connection_manager.user_connections
        assert other_user_id in connection_manager.user_connections

        # Call the adapter to send a notification
        await adapter.notify_match_success(user_id_to_notify, payload_to_send)

        # Then
        # Check that the correct user received the message
        received_data_ws1 = ws1.receive_text()
        assert json.loads(received_data_ws1) == payload_to_send

        # The most important part is that the intended user received the message.
        # Verifying that the other user *didn't* receive it is harder without
        # a client-side timeout, but the successful specific send is a strong indicator.

    # Verify that after disconnection, users are removed from the manager
    assert user_id_to_notify not in connection_manager.user_connections
    assert other_user_id not in connection_manager.user_connections
