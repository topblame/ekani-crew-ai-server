from abc import ABC, abstractmethod

from app.community.domain.comment import Comment, CommentTargetType


class CommentRepositoryPort(ABC):
    """댓글 저장소 포트"""

    @abstractmethod
    def save(self, comment: Comment) -> None:
        """댓글을 저장한다"""
        pass

    @abstractmethod
    def find_by_post_id(self, post_id: str) -> list[Comment]:
        """게시글 ID로 댓글 목록을 조회한다 (시간순 정렬)"""
        pass

    @abstractmethod
    def count_by_post_id(self, post_id: str) -> int:
        """게시글 ID로 댓글 수를 조회한다"""
        pass

    @abstractmethod
    def find_by_target(
        self, target_type: CommentTargetType, target_id: str
    ) -> list[Comment]:
        """타겟 타입과 ID로 댓글 목록을 조회한다 (시간순 정렬)"""
        pass

    @abstractmethod
    def count_by_target(
        self, target_type: CommentTargetType, target_id: str
    ) -> int:
        """타겟 타입과 ID로 댓글 수를 조회한다"""
        pass
