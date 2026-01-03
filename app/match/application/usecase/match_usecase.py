import uuid
from datetime import datetime
from typing import Optional

from app.match.application.port.output.chat_room_port import ChatRoomPort
from app.match.application.port.output.match_notification_port import MatchNotificationPort
from app.match.application.service.match_service import MatchService
from app.shared.vo.mbti import MBTI
from app.match.domain.match_ticket import MatchTicket
from app.match.application.port.output.match_queue_port import MatchQueuePort
from app.match.application.port.output.match_state_port import MatchStatePort, MatchState


class MatchUseCase:
    # How long to wait for user to connect to chat before match expires (seconds)
    MATCH_EXPIRE_SECONDS = 60

    def __init__(
        self,
        match_queue_port: MatchQueuePort,
        chat_room_port: ChatRoomPort,
        match_state_port: Optional[MatchStatePort] = None,
        match_notification_port: Optional[MatchNotificationPort] = None,
    ):
        self.match_queue = match_queue_port
        self.match_service = MatchService(match_queue_port)
        self.chat_room_port = chat_room_port
        self.match_state = match_state_port
        self.match_notification_port = match_notification_port

    async def request_match(self, user_id: str, mbti: MBTI, level: int = 1) -> dict:
        """
        유저의 매칭 요청을 처리합니다 (Enqueue).
        """
        # Check if user was just matched (waiting to connect to chat room)
        # Note: CHATTING state does NOT block new matches - users can have multiple chat rooms
        if self.match_state:
            user_state = await self.match_state.get_state(user_id)
            if user_state and user_state.state == MatchState.MATCHED:
                # User was just matched, should connect to that chat room first
                return {
                    "status": "already_matched",
                    "message": "이미 매칭되었습니다. 채팅방에 입장해주세요.",
                    "roomId": user_state.room_id,
                    "my_mbti": mbti.value,
                    "partner": {
                        "user_id": user_state.partner_id,
                        "mbti": None  # We don't store partner's MBTI in state
                    }
                }

        if await self.match_queue.is_user_in_queue(user_id, mbti):
            # 이미 대기열에 있는 유저가 다른 레벨로 재요청한 경우,
            # 기존 대기열에서 제거하고 새로운 요청으로 계속 진행합니다.
            await self.match_queue.remove(user_id, mbti)

        # 도메인 객체 생성
        my_ticket = MatchTicket(user_id=user_id, mbti=mbti)

        # Service에 level 전달
        partner_ticket = await self.match_service.find_partner(my_ticket, level)

        if partner_ticket:
            # Check if partner is still available (not matched/chatting with someone else)
            if self.match_state:
                if not await self.match_state.is_available_for_match(partner_ticket.user_id):
                    # Partner is no longer available, try to find another partner
                    # For now, just add user to queue
                    await self.match_queue.enqueue(my_ticket)
                    await self.match_state.set_queued(user_id, mbti.value)
                    wait_count = await self.get_waiting_count(mbti)
                    return {
                        "status": "waiting",
                        "message": "매칭 대기열에 등록되었습니다.",
                        "my_mbti": mbti.value,
                        "wait_count": wait_count
                    }

            # 2. [MATCH-3] 매칭 성공 시 채팅방 데이터 생성
            room_id = str(uuid.uuid4())
            timestamp = datetime.now().isoformat()

            chat_payload = {
                "roomId": room_id,
                "users": [
                    {"userId": my_ticket.user_id, "mbti": my_ticket.mbti.value},
                    {"userId": partner_ticket.user_id, "mbti": partner_ticket.mbti.value}
                ],
                "timestamp": timestamp
            }

            # 3. [MATCH-3] Chat 도메인으로 데이터 전송 (비동기 처리 가능)
            await self.chat_room_port.create_chat_room(chat_payload)

            # 4. Set matched state for both users (with expiration)
            if self.match_state:
                await self.match_state.set_matched(
                    user_id=my_ticket.user_id,
                    mbti=my_ticket.mbti.value,
                    room_id=room_id,
                    partner_id=partner_ticket.user_id,
                    expire_seconds=self.MATCH_EXPIRE_SECONDS
                )
                await self.match_state.set_matched(
                    user_id=partner_ticket.user_id,
                    mbti=partner_ticket.mbti.value,
                    room_id=room_id,
                    partner_id=my_ticket.user_id,
                    expire_seconds=self.MATCH_EXPIRE_SECONDS
                )
            
            # 5. Notify partner via WebSocket
            if self.match_notification_port:
                partner_payload = {
                    "status": "matched",
                    "message": "매칭이 성사되었습니다!",
                    "roomId": room_id,
                    "my_mbti": partner_ticket.mbti.value,
                    "partner": {
                        "user_id": my_ticket.user_id,
                        "mbti": my_ticket.mbti.value
                    }
                }
                await self.match_notification_port.notify_match_success(partner_ticket.user_id, partner_payload)

            # 6. Return response to the requester
            return {
                "status": "matched",
                "message": "매칭이 성사되었습니다!",
                "roomId": room_id,
                "my_mbti": my_ticket.mbti.value,
                "partner": {
                    "user_id": partner_ticket.user_id,
                    "mbti": partner_ticket.mbti.value
                }
            }

        # 매칭 실패 시 대기열 등록
        try:
            await self.match_queue.enqueue(my_ticket)
            # Set queued state
            if self.match_state:
                await self.match_state.set_queued(user_id, mbti.value)
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

        # Clear user state regardless of queue removal result
        if self.match_state:
            await self.match_state.clear_state(user_id)

        if is_removed:
            return {"status": "cancelled", "message": "매칭이 취소되었습니다."}
        else:
            return {"status": "fail", "message": "대기열에서 유저를 찾을 수 없습니다."}

    async def get_waiting_count(self, mbti: MBTI) -> int:
        """
        특정 MBTI 큐의 대기 인원을 조회합니다.
        """
        return await self.match_queue.get_queue_size(mbti)