"""
Centralized router configuration.
All application routers are registered here and imported into main.py.
"""

from fastapi import FastAPI

from app.auth.adapter.input.web.google_oauth_router import google_oauth_router
from app.match.adapter.input.web.match_router import match_router
from app.user.infrastructure.model.user_model import UserModel  # noqa: F401
from app.converter.adapter.input.web.converter_router import converter_router
from app.user.adapter.input.web.user_router import user_router
from app.mbti_test.adapter.input.web.mbti_router import mbti_router
from app.chat.adapter.input.web.chat_websocket_router import chat_websocket_router
from app.chat.adapter.input.web.chat_router import chat_router
from app.chat.infrastructure.model.chat_room_model import ChatRoomModel  # noqa: F401
from app.chat.infrastructure.model.chat_message_model import ChatMessageModel  # noqa: F401
def setup_routers(app: FastAPI) -> None:
    """모든 라우터를 FastAPI 앱에 등록한다."""
    app.include_router(google_oauth_router, prefix="/auth", tags=["Auth"])
    app.include_router(user_router, prefix="/user", tags=["User"])
    app.include_router(converter_router, prefix="/converter", tags=["Converter"])
    app.include_router(mbti_router, prefix="/mbti-test", tags=["MBTI Test"])
    app.include_router(chat_router, tags=["Chat"])
    app.include_router(chat_websocket_router, tags=["Chat"])
    app.include_router(match_router, prefix="/match", tags=["Match"])

