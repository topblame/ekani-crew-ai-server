from typing import Optional
from app.match.domain.match_ticket import MatchTicket
from app.match.domain.mbti_compatibility import MBTICompatibility
from app.match.application.port.output.match_queue_port import MatchQueuePort
from app.shared.vo.mbti import MBTI


class MatchService:
    """
    매칭 탐색 알고리즘을 수행하는 애플리케이션 서비스
    """

    def __init__(self, match_queue_port: MatchQueuePort):
        self.match_queue = match_queue_port

    async def find_partner(self, my_ticket: MatchTicket, level: int = 1) -> Optional[MatchTicket]:
        # 1. 레벨에 맞는 타겟 MBTI 리스트 확보
        target_mbti_values = [m.value for m in MBTICompatibility.get_targets(my_ticket.mbti.value, level)]

        if not target_mbti_values:
            return None

        # 2. [최적화] 대기자가 많은 순서대로 정렬된 리스트 받기
        sorted_targets = await self.match_queue.get_sorted_targets_by_size(target_mbti_values)

        # 3. 순차 탐색 (0명인 큐는 스킵)
        for mbti_str, count in sorted_targets:
            if count == 0:
                continue

            target_mbti = MBTI(mbti_str)
            partner_ticket = await self.match_queue.dequeue(target_mbti)

            if partner_ticket:
                return partner_ticket

        return None