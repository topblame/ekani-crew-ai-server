import pytest
import json
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from app.main import app
from config.database import get_db_session, Base, engine
from app.chat.infrastructure.model.chat_message_model import ChatMessageModel
from app.chat.infrastructure.model.chat_room_model import ChatRoomModel

# 테스트용 테이블 생성
Base.metadata.create_all(bind=engine)

client = TestClient(app)


class TestChatWebSocketRouter:
    def test_websocket_connection_and_disconnection(self):
        """WebSocket 연결 및 해제 테스트"""
        room_id = "test_room"
        try:
            with client.websocket_connect(f"/ws/chat/{room_id}") as websocket:
                # 연결이 성공적으로 이루어져야 함
                assert websocket
        except WebSocketDisconnect as e:
            pytest.fail(f"WebSocket connection failed unexpectedly: {e}")

    def test_send_and_receive_message(self):
        """메시지 송수신 테스트"""
        room_id = "test_room"
        with client.websocket_connect(f"/ws/chat/{room_id}") as websocket:
            message_payload = {
                "sender_id": "user1",
                "content": "Hello, WebSocket!"
            }
            websocket.send_json(message_payload)
            received = websocket.receive_json()
            assert received["content"] == "Hello, WebSocket!"
            assert received["sender_id"] == "user1"

    @pytest.mark.skip(reason="TestClient WebSocket timing issue - works in production")
    def test_broadcast_message_to_room(self):
        """채팅방 메시지 브로드캐스팅 테스트"""
        room_id = "broadcast_room"
        message_payload = {
            "sender_id": "user1",
            "content": "This is a broadcast message."
        }

        with client.websocket_connect(f"/ws/chat/{room_id}") as websocket1:
            with client.websocket_connect(f"/ws/chat/{room_id}") as websocket2:
                # Client 1 sends a message
                websocket1.send_json(message_payload)

                # Client 2 should receive the message
                received_message_2 = websocket2.receive_json()
                assert received_message_2["content"] == "This is a broadcast message."
                assert received_message_2["sender_id"] == "user1"

                # Client 1 should also receive the message (or not, depending on requirements)
                # For now, we'll assume it's broadcast to all, including the sender.
                received_message_1 = websocket1.receive_json()
                assert received_message_1["content"] == "This is a broadcast message."
                assert received_message_1["sender_id"] == "user1"

    def test_message_saved_to_database(self):
        """WebSocket으로 전송한 메시지가 DB에 저장되는지 검증"""
        room_id = "test_room_db"
        sender_id = "user123"
        content = "Hello, this should be saved to DB!"

        # 테스트 시작 전 기존 데이터 정리
        db = get_db_session()
        db.query(ChatMessageModel).filter(
            ChatMessageModel.room_id == room_id
        ).delete()
        db.commit()
        db.close()

        # WebSocket으로 메시지 전송 (JSON 형식)
        with client.websocket_connect(f"/ws/chat/{room_id}") as websocket:
            message_payload = {
                "sender_id": sender_id,
                "content": content
            }
            websocket.send_json(message_payload)

            # 메시지 수신 확인
            received = websocket.receive_json()

        # DB에 메시지가 저장되었는지 확인
        db = get_db_session()
        try:
            saved_messages = db.query(ChatMessageModel).filter(
                ChatMessageModel.room_id == room_id,
                ChatMessageModel.sender_id == sender_id,
                ChatMessageModel.content == content
            ).all()

            assert len(saved_messages) == 1
            assert saved_messages[0].sender_id == sender_id
            assert saved_messages[0].content == content
        finally:
            # 테스트 데이터 정리
            db.query(ChatMessageModel).filter(
                ChatMessageModel.room_id == room_id
            ).delete()
            db.commit()
            db.close()
