import uuid
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.community.application.port.topic_repository_port import TopicRepositoryPort
from app.community.domain.topic import Topic
from app.community.infrastructure.repository.mysql_topic_repository import MySQLTopicRepository
from config.database import get_db


topic_router = APIRouter()


def get_topic_repository(db: Session = Depends(get_db)) -> TopicRepositoryPort:
    return MySQLTopicRepository(db)


class CreateTopicRequest(BaseModel):
    title: str
    description: str
    start_date: date
    end_date: date


class TopicResponse(BaseModel):
    id: str
    title: str
    description: str
    start_date: date
    end_date: date
    is_active: bool


@topic_router.post("/topics", status_code=status.HTTP_201_CREATED)
def create_topic(
    request: CreateTopicRequest,
    topic_repo: TopicRepositoryPort = Depends(get_topic_repository),
) -> TopicResponse:
    """토픽 등록 (관리자)"""
    topic = Topic(
        id=str(uuid.uuid4()),
        title=request.title,
        description=request.description,
        start_date=request.start_date,
        end_date=request.end_date,
        is_active=True,
    )
    topic_repo.save(topic)

    return TopicResponse(
        id=topic.id,
        title=topic.title,
        description=topic.description,
        start_date=topic.start_date,
        end_date=topic.end_date,
        is_active=topic.is_active,
    )


@topic_router.get("/topics/current")
def get_current_topic(
    topic_repo: TopicRepositoryPort = Depends(get_topic_repository),
) -> TopicResponse | None:
    """현재 활성 토픽 조회 (게시판 헤더용)"""
    topic = topic_repo.find_current_active()
    if not topic:
        return None

    return TopicResponse(
        id=topic.id,
        title=topic.title,
        description=topic.description,
        start_date=topic.start_date,
        end_date=topic.end_date,
        is_active=topic.is_active,
    )
