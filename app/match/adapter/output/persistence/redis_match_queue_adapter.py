import json
import redis.asyncio as aioredis
from typing import Optional
from datetime import datetime

from app.shared.vo.mbti import MBTI
from app.match.domain.match_ticket import MatchTicket
from app.match.application.port.output.match_queue_port import MatchQueuePort


class RedisMatchQueueAdapter(MatchQueuePort):
    def __init__(self, client: aioredis.Redis):
        self.redis = client
        self.key_prefix = "match:queue:"

    def _get_list_key(self, mbti: MBTI) -> str:
        # 순서 관리용 (List)
        return f"{self.key_prefix}{mbti.value}:list"

    def _get_set_key(self, mbti: MBTI) -> str:
        # 중복/취소 관리용 (Set) - user_id만 저장
        return f"{self.key_prefix}{mbti.value}:set"

    def _serialize(self, ticket: MatchTicket) -> str:
        return json.dumps({
            "user_id": ticket.user_id,
            "mbti": ticket.mbti.value,
            "created_at": ticket.created_at.isoformat()
        })

    def _deserialize(self, data: str) -> MatchTicket:
        raw = json.loads(data)
        ticket = MatchTicket(
            user_id=raw["user_id"],
            mbti=MBTI(raw["mbti"])
        )
        if "created_at" in raw:
            ticket.created_at = datetime.fromisoformat(raw["created_at"])
        return ticket

    async def enqueue(self, ticket: MatchTicket) -> None:
        list_key = self._get_list_key(ticket.mbti)
        set_key = self._get_set_key(ticket.mbti)

        # 1. [O(1)] Set에 유저가 있는지 확인 (중복 체크)
        # sismember: 있으면 1, 없으면 0 반환
        if await self.redis.sismember(set_key, ticket.user_id):
            raise ValueError("이미 대기열에 등록된 유저입니다.")

        # 2. [O(1)] 데이터 저장 (Set + List)
        # 트랜잭션(Pipeline)을 사용하여 원자성 보장 권장
        async with self.redis.pipeline() as pipe:
            pipe.sadd(set_key, ticket.user_id)  # Set에 ID 등록
            pipe.rpush(list_key, self._serialize(ticket))  # List에 티켓 등록
            await pipe.execute()

        print(f"[Redis] Enqueued {ticket.user_id}")

    async def dequeue(self, mbti: MBTI) -> Optional[MatchTicket]:
        list_key = self._get_list_key(mbti)
        set_key = self._get_set_key(mbti)

        # 유효한 유저가 나올 때까지 반복 (Lazy Removal 처리)
        while True:
            # 1. [O(1)] List에서 가장 오래된 티켓 꺼냄
            data = await self.redis.lpop(list_key)

            if not data:
                return None  # 대기열이 비었음

            ticket = self._deserialize(data)

            # 2. [O(1)] 유효성 검사: Set에서 삭제 시도
            # srem은 삭제에 성공하면 1, 없어서 못 지웠으면(이미 취소된 유저) 0을 반환
            is_valid_user = await self.redis.srem(set_key, ticket.user_id)

            if is_valid_user:
                print(f"[Redis] Dequeued valid user: {ticket.user_id}")
                return ticket
            else:
                # Set에 없다는 건, 중간에 cancel_match를 요청했던 유저라는 뜻.
                # List에 남아있던 '유령 티켓'이므로 버리고(continue) 다음 사람을 뽑음.
                print(f"[Redis] Skipped cancelled user (Ghost Ticket): {ticket.user_id}")
                continue

    async def remove(self, user_id: str, mbti: MBTI) -> bool:
        """
        매칭 취소: List는 건드리지 않고 Set에서만 삭제합니다. [O(1)]
        """
        set_key = self._get_set_key(mbti)

        # srem: Set에서 제거. 성공 시 1(True), 실패 시 0(False)
        removed_count = await self.redis.srem(set_key, user_id)

        if removed_count > 0:
            print(f"[Redis] Mark user as cancelled: {user_id}")
            return True
        return False

    async def get_queue_size(self, mbti: MBTI) -> int:
        # 실제 대기 인원은 List 길이가 아니라 Set의 크기입니다. (취소된 유령 티켓 제외)
        set_key = self._get_set_key(mbti)
        return await self.redis.scard(set_key)

    async def get_sorted_targets_by_size(self, mbti_list: list[str]) -> list[tuple[str, int]]:
        """
        Pipeline을 이용해 여러 MBTI 대기열 크기를 한 번에 조회하고,
        대기자가 많은 순서(내림차순)로 정렬하여 반환합니다.
        """
        if not mbti_list:
            return []

        async with self.redis.pipeline() as pipe:
            for mbti_str in mbti_list:
                # Set의 크기(실제 유효 대기자 수) 조회
                set_key = self._get_set_key(MBTI(mbti_str))
                pipe.scard(set_key)

            sizes = await pipe.execute()

        # (MBTI, Size) 튜플 리스트 생성
        result = list(zip(mbti_list, sizes))

        # 사이즈 기준 내림차순 정렬 (많은 곳부터 탐색)
        result.sort(key=lambda x: x[1], reverse=True)

        return result

    async def is_user_in_queue(self, user_id: str, mbti: MBTI) -> bool:
        """
        Set을 확인하여 유저가 대기열에 있는지 확인합니다. [O(1)]
        """
        set_key = self._get_set_key(mbti)
        return await self.redis.sismember(set_key, user_id)
