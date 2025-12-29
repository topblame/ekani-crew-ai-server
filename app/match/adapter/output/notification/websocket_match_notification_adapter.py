import json
from typing import Dict, Any

from app.match.application.port.output.match_notification_port import MatchNotificationPort
from config.connection_manager import ConnectionManager


class WebSocketMatchNotificationAdapter(MatchNotificationPort):
    """
    An adapter that sends match notifications via WebSocket.
    """

    def __init__(self, connection_manager: ConnectionManager):
        self.connection_manager = connection_manager

    async def notify_match_success(self, user_id: str, payload: Dict[str, Any]):
        """
        Sends a JSON-serialized match success payload to a user.
        """
        message = json.dumps(payload)
        await self.connection_manager.send_to_user(user_id, message)
