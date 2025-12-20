from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any, Dict, List

from app.mbti_test.application.port.ai_question_provider_port import AIQuestionProviderPort
from app.mbti_test.domain.models import (
    AIQuestion,
    AIQuestionResponse,
    GenerateAIQuestionCommand,
    MessageRole,
)

def _turn_target_dimensions(turn: int) -> List[str]:
    # 턴 목표: 1 라포/자가진단, 2 E/I, 3 S/N, 4 T/F, 5 J/P
    if turn == 1:
        return []  # 라포/자가진단은 특정 차원 강제X (다만 질문은 해야 함)
    if turn == 2:
        return ["E/I"]
    if turn == 3:
        return ["S/N"]
    if turn == 4:
        return ["T/F"]
    if turn == 5:
        return ["J/P"]
    return []


def _strip_markdown_fences(text: str) -> str:
    # response_format=json_object 를 쓰더라도 가끔 fence가 섞일 수 있어 방어
    text = text.strip()
    # ```json ... ``` or ``` ... ```
    fence_pattern = r"^```(?:json)?\s*(.*?)\s*```$"
    m = re.match(fence_pattern, text, flags=re.DOTALL | re.IGNORECASE)
    if m:
        return m.group(1).strip()
    return text


def _parse_json_object(text: str) -> Dict[str, Any]:
    cleaned = _strip_markdown_fences(text)
    return json.loads(cleaned)


def _build_system_prompt() -> str:
    # 사과/AI 자기 언급 금지, 1~2개 질문, 2~3문장, 구체 사례 요청, 부족하면 예시 재요청
    return (
        "너는 MBTI 테스트를 진행하는 질문자다.\n"
        "규칙:\n"
        "- 매 턴 질문은 1~2개만 만든다.\n"
        "- 각 질문은 2~3문장으로, 사용자의 '구체 사례'를 요청한다.\n"
        "- 정보가 부족하면 '구체 예시 한 개 더'를 요청하는 재질문을 포함한다.\n"
        "- 사과하지 말고, AI/모델/시스템 같은 자기 언급을 하지 않는다.\n"
        "- 출력은 반드시 JSON 하나이며, 아래 스키마를 지킨다.\n"
        '  {"questions":[{"text":"...", "target_dimensions":["E/I"]} ...], "turn": n}\n'
        "- 질문 외의 설명/장식 문구를 넣지 않는다.\n"
    )


def _build_user_prompt(command: GenerateAIQuestionCommand) -> str:
    targets = _turn_target_dimensions(command.turn)
    mode_line = (
        "질문 모드: 돌발(surprise)\n"
        "- 질문에는 반드시 '예상 밖 상황/제약'을 1개 이상 포함해라. (시간 압박/역할 강제/갑작스런 변수/낯선 사람·환경)\n"
        "- 평범한 MBTI 질문(모임이 좋나, 혼자가 좋나 등)으로 묻지 마라.\n"
        "- 사용자가 둘 중 하나를 선택해야 하는 형태로 묻고, 이유 + 실제 경험 예시 1개를 요구해라.\n"
        if command.question_mode == "surprise"
        else
        "질문 모드: 일반(normal)\n"
        "- 대화 맥락을 이어서 자연스럽게 후속 질문을 해라.\n"
    )

    # 턴 1은 라포/자가진단이지만, 그래도 차원 단서를 살짝 볼 수 있게 설계 가능
    target_line = (
        f"이번 턴 번호: {command.turn}\n"
        f"이번 턴 목표 차원: {targets if targets else '라포/자가진단(특정 차원 강제 없음)'}\n"
    )

    # 히스토리는 최근 메시지 위주로 충분 (세션 담당이 길이 제어 가능)
    history_lines = []
    for msg in command.history:
        role = msg.role.value if isinstance(msg.role, MessageRole) else str(msg.role)
        history_lines.append(f"{role}: {msg.content}")

    history_block = "\n".join(history_lines).strip() or "(히스토리 없음)"

    return (
        f"{mode_line}\n"
        f"{target_line}"
        "대화 히스토리:\n"
        f"{history_block}\n"
        "위 히스토리를 바탕으로 다음 질문 JSON만 출력해라."
    )


@dataclass
class OpenAIQuestionProvider(AIQuestionProviderPort):
    """
    OpenAI 클라이언트는 외부에서 주입(테스트에서 모킹)한다.
    settings.py에서 키/모델을 읽는 함수는 create_client 팩토리에서 처리하도록 분리 가능.
    """
    openai_client: Any
    model: str

    def generate_questions(self, command: GenerateAIQuestionCommand) -> AIQuestionResponse:
        system_prompt = _build_system_prompt()
        user_prompt = _build_user_prompt(command)

        resp = self.openai_client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            response_format={"type": "json_object"},
        )

        content = resp.choices[0].message.content  # openai python SDK 1.x 형태 가정
        data = _parse_json_object(content)

        turn = int(data.get("turn", command.turn))
        raw_questions = data.get("questions", [])
        questions: List[AIQuestion] = []
        for q in raw_questions:
            questions.append(
                AIQuestion(
                    text=str(q.get("text", "")).strip(),
                    target_dimensions=list(q.get("target_dimensions", [])),
                )
            )

        # 최소 방어: 질문 비어있으면 실패로 처리
        if not questions or any(not q.text for q in questions):
            raise ValueError("LLM returned invalid questions payload")

        return AIQuestionResponse(turn=turn, questions=questions)

# (선택) settings.py 기반 클라이언트 팩토리: 기존 프로젝트 스타일에 맞게 라우터에서 사용
def create_openai_question_provider_from_settings() -> OpenAIQuestionProvider:
    from config.settings import get_settings
    from openai import OpenAI

    settings = get_settings()  # ✅ 인스턴스 가져오기
    api_key = settings.OPENAI_API_KEY
    model = getattr(settings, "OPENAI_MODEL", None) or "gpt-4o-mini"
    client = OpenAI(api_key=api_key)
    return OpenAIQuestionProvider(openai_client=client, model=model)