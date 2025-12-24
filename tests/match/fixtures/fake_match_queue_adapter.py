from typing import Dict, Optional, List, Tuple
from collections import deque

from app.shared.vo.mbti import MBTI
from app.match.domain.match_ticket import MatchTicket
from app.match.application.port.output.match_queue_port import MatchQueuePort


class FakeMatchQueueAdapter(MatchQueuePort):
    def __init__(self):
        # Key를 MBTI 객체가 아닌 'str'로 변경하여 객체 불일치 문제 해결
        self._queues: Dict[str, deque] = {}

    async def enqueue(self, ticket: MatchTicket) -> None:
        # 키를 문자열로 변환
        mbti_key = ticket.mbti.value

        if mbti_key not in self._queues:
            self._queues[mbti_key] = deque()

        for t in self._queues[mbti_key]:
            if t.user_id == ticket.user_id:
                raise ValueError("이미 대기열에 등록된 유저입니다.")

        self._queues[mbti_key].append(ticket)

    async def dequeue(self, mbti: MBTI) -> Optional[MatchTicket]:
        mbti_key = mbti.value
        if mbti_key in self._queues and self._queues[mbti_key]:
            return self._queues[mbti_key].popleft()
        return None

    async def remove(self, user_id: str, mbti: MBTI) -> bool:
        mbti_key = mbti.value
        if mbti_key not in self._queues:
            return False

        queue = self._queues[mbti_key]
        for ticket in queue:
            if ticket.user_id == user_id:
                queue.remove(ticket)
                return True
        return False

    async def get_queue_size(self, mbti: MBTI) -> int:
        return len(self._queues.get(mbti.value, []))

    async def get_sorted_targets_by_size(self, mbti_list: List[str]) -> List[Tuple[str, int]]:
        """
        테스트용: 메모리 큐의 사이즈를 확인하고 정렬하여 반환
        """
        result = []
        for mbti_str in mbti_list:
            size = len(self._queues.get(mbti_str, []))
            result.append((mbti_str, size))

        # 사이즈 내림차순 정렬
        result.sort(key=lambda x: x[1], reverse=True)
        return result