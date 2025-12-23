from app.match.application.service.match_service import MatchService
from app.shared.vo.mbti import MBTI
from app.match.domain.match_ticket import MatchTicket
from app.match.application.port.output.match_queue_port import MatchQueuePort


class MatchUseCase:
    def __init__(self, match_queue_port: MatchQueuePort):
        self.match_queue = match_queue_port
        self.match_service = MatchService(match_queue_port)

    async def request_match(self, user_id: str, mbti: MBTI, level: int = 1) -> dict:
        """
        유저의 매칭 요청을 처리합니다 (Enqueue).
        """
        # 도메인 객체 생성
        my_ticket = MatchTicket(user_id=user_id, mbti=mbti)

        # Service에 level 전달
        partner_ticket = await self.match_service.find_partner(my_ticket, level)

        if partner_ticket:
            # 매칭 성공! (나는 큐에 안 들어감, 상대는 큐에서 나옴)
            return {
                "status": "matched",
                "message": "매칭이 성사되었습니다!",
                "my_mbti": mbti.value,
                "partner": {
                    "user_id": partner_ticket.user_id,
                    "mbti": partner_ticket.mbti.value
                }
            }

        # 매칭 실패 시 대기열 등록
        try:
            await self.match_queue.enqueue(my_ticket)
            status = "waiting"
            message = "매칭 대기열에 등록되었습니다."

        except ValueError:
            status = "already_waiting"
            message = "이미 대기열에 등록된 유저입니다."

        # 대기 인원 조회
        wait_count = await self.get_waiting_count(mbti)

        return {
            "status": status,
            "message": message,
            "my_mbti": mbti.value,
            "wait_count": wait_count
        }

    async def cancel_match(self, user_id: str, mbti: MBTI) -> dict:
        """
        매칭 요청을 취소합니다 (Remove).
        """
        # Redis IO 발생 -> await 필수!
        is_removed = await self.match_queue.remove(user_id, mbti)

        if is_removed:
            return {"status": "cancelled", "message": "매칭이 취소되었습니다."}
        else:
            return {"status": "fail", "message": "대기열에서 유저를 찾을 수 없습니다."}

    async def get_waiting_count(self, mbti: MBTI) -> int:
        """
        특정 MBTI 큐의 대기 인원을 조회합니다.
        """
        return await self.match_queue.get_queue_size(mbti)