"""
Centralized router configuration.
All application routers are registered here and imported into main.py.
"""

from fastapi import FastAPI

from app.auth.adapter.input.web.google_oauth_router import google_oauth_router
from app.user.infrastructure.model.user_model import UserModel  # noqa: F401
from app.consult.infrastructure.model.consult_session_model import ConsultSessionModel  # noqa: F401
from app.consult.adapter.input.web.consult_router import consult_router
from app.converter.adapter.input.web.converter_router import converter_router
from app.user.adapter.input.web.user_router import user_router
from app.mbti_test.adapter.input.web.mbti_router import mbti_router
def setup_routers(app: FastAPI) -> None:
    """모든 라우터를 FastAPI 앱에 등록한다."""
    app.include_router(google_oauth_router, prefix="/auth")
    app.include_router(user_router, prefix="/user")
    app.include_router(converter_router, prefix="/converter")
    app.include_router(consult_router, prefix="/consult")
    app.include_router(mbti_router, prefix="/mbti_test-test")

