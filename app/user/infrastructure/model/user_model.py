import uuid

from sqlalchemy import Column, String, DateTime
from sqlalchemy.orm import relationship
from config.database import Base


class UserModel(Base):
    """User ORM 모델"""

    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), nullable=False, unique=True, index=True)
    mbti = Column(String(4), nullable=True)
    gender = Column(String(10), nullable=True)
    updated_at = Column(DateTime, nullable=True)

    # Relationships
    oauth_identities = relationship("OAuthIdentityModel", back_populates="user")
