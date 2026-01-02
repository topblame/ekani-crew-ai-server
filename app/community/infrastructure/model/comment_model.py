from sqlalchemy import Column, String, Text, DateTime
from config.database import Base


class CommentModel(Base):
    """댓글 ORM 모델"""

    __tablename__ = "comments"

    id = Column(String(36), primary_key=True)
    target_type = Column(String(20), nullable=False, default="post", index=True)
    target_id = Column(String(36), nullable=False, index=True)
    author_id = Column(String(36), nullable=False, index=True)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, nullable=False)