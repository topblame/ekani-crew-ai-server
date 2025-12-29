from abc import ABC, abstractmethod
from typing import Dict, Any


class MatchNotificationPort(ABC):
    """
    An outbound port for sending match-related notifications.
    """

    @abstractmethod
    async def notify_match_success(self, user_id: str, payload: Dict[str, Any]):
        """
        Notifies a user that a match has been successfully made.

        Args:
            user_id: The ID of the user to notify.
            payload: The notification payload containing match details.
        """
        pass
