from app.match.application.usecase.match_usecase import MatchUseCase
from app.match.adapter.output.persistence.redis_match_queue_adapter import RedisMatchQueueAdapter
from config.redis import get_redis  # 설정 파일에서 Redis 클라이언트 가져오기


class MatchUseCaseFactory:
    @staticmethod
    def create() -> MatchUseCase:
        redis_client = get_redis()
        adapter = RedisMatchQueueAdapter(redis_client)

        return MatchUseCase(match_queue_port=adapter)