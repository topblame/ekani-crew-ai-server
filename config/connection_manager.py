from fastapi import WebSocket
from typing import Dict, List, Optional, Tuple


class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}
        # Track user_id -> (room_id, websocket) mapping for cleanup
        self.user_connections: Dict[str, Tuple[str, WebSocket]] = {}

    async def connect(self, websocket: WebSocket, room_id: str, user_id: Optional[str] = None):
        await websocket.accept()
        if room_id not in self.active_connections:
            self.active_connections[room_id] = []
        self.active_connections[room_id].append(websocket)

        # Track user connection if user_id provided
        if user_id:
            self.user_connections[user_id] = (room_id, websocket)
            print(f"[ConnectionManager] User {user_id} connected to room {room_id}")

    def disconnect(self, websocket: WebSocket, room_id: str) -> Optional[str]:
        """
        Disconnect websocket and return user_id if found.
        """
        if room_id in self.active_connections:
            if websocket in self.active_connections[room_id]:
                self.active_connections[room_id].remove(websocket)

        # Find and remove user from user_connections
        disconnected_user_id = None
        for user_id, (tracked_room_id, tracked_ws) in list(self.user_connections.items()):
            if tracked_ws == websocket and tracked_room_id == room_id:
                disconnected_user_id = user_id
                del self.user_connections[user_id]
                print(f"[ConnectionManager] User {user_id} disconnected from room {room_id}")
                break

        return disconnected_user_id

    def register_user(self, user_id: str, room_id: str, websocket: WebSocket):
        """Register user_id with their websocket connection"""
        self.user_connections[user_id] = (room_id, websocket)
        print(f"[ConnectionManager] Registered user {user_id} to room {room_id}")

    def get_user_room(self, user_id: str) -> Optional[str]:
        """Get room_id for a user"""
        if user_id in self.user_connections:
            return self.user_connections[user_id][0]
        return None

    async def broadcast(self, message: str, room_id: str):
        if room_id in self.active_connections:
            for connection in self.active_connections[room_id]:
                await connection.send_text(message)

    async def send_to_user(self, user_id: str, message: str):
        """Send a message to a specific user."""
        if user_id in self.user_connections:
            _room_id, websocket = self.user_connections[user_id]
            await websocket.send_text(message)
            print(f"[ConnectionManager] Sent message to user {user_id}")
        else:
            print(f"[ConnectionManager] User {user_id} not found for sending message.")


# 싱글톤 인스턴스
manager = ConnectionManager()
