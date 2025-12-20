from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import List, Literal


MBTIDimension = Literal["E/I", "S/N", "T/F", "J/P"]


class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


@dataclass(frozen=True)
class ChatMessage:
    role: MessageRole
    content: str


@dataclass(frozen=True)
class AIQuestion:
    text: str
    target_dimensions: List[MBTIDimension]


@dataclass(frozen=True)
class AIQuestionResponse:
    turn: int
    questions: List[AIQuestion]


@dataclass(frozen=True)
class GenerateAIQuestionCommand:
    """
    다른 팀(세션/히스토리 담당)이 만든 세션 구조를 건드리지 않기 위해
    이 유스케이스는 session_id + (turn, history)를 외부(요청)에서 주입받는다.
    """
    session_id: str
    turn: int
    history: List[ChatMessage]
    question_mode: Literal["normal", "surprise"] = "normal"