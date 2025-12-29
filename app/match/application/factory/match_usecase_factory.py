from app.match.adapter.output.chat.chat_client_adapter import ChatClientAdapter
from app.match.adapter.output.notification.websocket_match_notification_adapter import WebSocketMatchNotificationAdapter
from app.match.application.usecase.match_usecase import MatchUseCase
from app.match.adapter.output.persistence.redis_match_queue_adapter import RedisMatchQueueAdapter
from app.match.adapter.output.persistence.redis_match_state_adapter import RedisMatchStateAdapter
from config.connection_manager import manager as connection_manager
from config.redis import get_redis  # 설정 파일에서 Redis 클라이언트 가져오기


class MatchUseCaseFactory:
    @staticmethod
    def create() -> MatchUseCase:
        redis_client = get_redis()
        queue_adapter = RedisMatchQueueAdapter(redis_client)
        state_adapter = RedisMatchStateAdapter(redis_client)
        chat_adapter = ChatClientAdapter()
        notification_adapter = WebSocketMatchNotificationAdapter(connection_manager)

        return MatchUseCase(
            match_queue_port=queue_adapter,
            chat_room_port=chat_adapter,
            match_state_port=state_adapter,
            match_notification_port=notification_adapter
        )