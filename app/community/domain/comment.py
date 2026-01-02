from datetime import datetime
from typing import Literal

CommentTargetType = Literal["post", "balance_game"]


class Comment:
    """댓글 도메인 엔티티"""

    def __init__(
        self,
        id: str,
        author_id: str,
        content: str,
        target_type: CommentTargetType = "post",
        target_id: str | None = None,
        post_id: str | None = None,
        created_at: datetime | None = None,
    ):
        self.id = id
        self.author_id = author_id
        self.content = content
        self.target_type = target_type
        # 하위 호환성: post_id가 주어지면 target_type="post", target_id=post_id로 처리
        if post_id is not None and target_id is None:
            self.target_type = "post"
            self.target_id = post_id
        else:
            self.target_id = target_id
        self.created_at = created_at or datetime.now()

    @property
    def post_id(self) -> str | None:
        """하위 호환성을 위한 post_id 속성"""
        if self.target_type == "post":
            return self.target_id
        return None
