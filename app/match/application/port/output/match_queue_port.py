from abc import ABC, abstractmethod
from typing import Optional, List, Tuple
from app.shared.vo.mbti import MBTI
from app.match.domain.match_ticket import MatchTicket

class MatchQueuePort(ABC):
    """
    매칭 대기열(Queue)에 접근하기 위한 포트 (Interface)
    """

    @abstractmethod
    async def enqueue(self, ticket: MatchTicket) -> None:
        pass

    @abstractmethod
    async def dequeue(self, mbti: MBTI) -> Optional[MatchTicket]:
        pass

    @abstractmethod
    async def remove(self, user_id: str, mbti: MBTI) -> bool:
        pass

    @abstractmethod
    async def get_queue_size(self, mbti: MBTI) -> int:
        pass

    @abstractmethod
    async def get_sorted_targets_by_size(self, mbti_list: List[str]) -> List[Tuple[str, int]]:
        pass