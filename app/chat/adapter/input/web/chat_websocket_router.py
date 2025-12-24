import json
import uuid
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from .connection_manager import manager
from app.chat.application.use_case.save_chat_message_use_case import SaveChatMessageUseCase
from app.chat.infrastructure.repository.mysql_chat_message_repository import MySQLChatMessageRepository
from config.database import get_db_session

chat_websocket_router = APIRouter()


@chat_websocket_router.websocket("/ws/chat/{room_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: str):
    await manager.connect(websocket, room_id)

    # 의존성 주입
    db_session = get_db_session()
    message_repository = MySQLChatMessageRepository(db_session)
    save_message_use_case = SaveChatMessageUseCase(message_repository)

    try:
        while True:
            # JSON 형식으로 메시지 수신
            data = await websocket.receive_text()
            message_data = json.loads(data)

            sender_id = message_data.get("sender_id")
            content = message_data.get("content")

            if not sender_id or not content:
                await websocket.send_json({"error": "sender_id and content are required"})
                continue

            # 메시지 ID 생성
            message_id = str(uuid.uuid4())

            # DB에 메시지 저장
            save_message_use_case.execute(
                message_id=message_id,
                room_id=room_id,
                sender_id=sender_id,
                content=content
            )

            # 브로드캐스트용 메시지 생성
            broadcast_message = {
                "message_id": message_id,
                "room_id": room_id,
                "sender_id": sender_id,
                "content": content
            }

            # 채팅방의 모든 클라이언트에게 브로드캐스트
            await manager.broadcast(json.dumps(broadcast_message), room_id)

    except WebSocketDisconnect:
        manager.disconnect(websocket, room_id)
    finally:
        db_session.close()

