from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from config.connection_manager import manager

match_websocket_router = APIRouter()


@match_websocket_router.websocket("/ws/match/{user_id}")
async def match_websocket_endpoint(websocket: WebSocket, user_id: str):
    """
    매칭 대기 중인 사용자가 연결하는 WebSocket 엔드포인트.
    매칭이 성사되면 이 연결을 통해 알림을 받습니다.
    """
    # room_id는 "match_waiting"으로 설정 (매칭 대기용 가상 룸)
    room_id = f"match_waiting_{user_id}"
    await manager.connect(websocket, room_id, user_id)
    print(f"[MatchWebSocket] User {user_id} connected for match notifications")

    try:
        while True:
            # 클라이언트로부터 ping/pong 또는 연결 유지 메시지 수신
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, room_id)
        print(f"[MatchWebSocket] User {user_id} disconnected from match notifications")
