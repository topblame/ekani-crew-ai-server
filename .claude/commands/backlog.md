---
description: "Create backlog item for next test in plan.md"
---

# Backlog Generator

`/backlog` → plan.md에서 다음 미완료 항목의 백로그 카드 생성

---

## 규칙

1. `/backlog MBTI-1` → 해당 백로그 ID 항목의 백로그 생성
2. `/backlog` (argument 없음) → plan.md에서 다음 `- [ ]` 항목 찾아서 생성
3. 노션에 바로 붙여넣기 가능한 마크다운 형식 (코드블록으로 감싸서 출력)

---

## 출력 형식

```markdown
# 제목
- [Domain] 사용자로서, ~하고 싶다 [백로그ID]

# Domain
- (도메인명)

# Purpose
- (사용자 스토리: ~로서, ~하고 싶다)
- (배경/필요성 설명 1)
- (배경/필요성 설명 2)
- (이 백로그의 핵심 목적)

# Success Criteria
- [ ] (확인 가능한 조건 1)
- [ ] (확인 가능한 조건 2)
- [ ] (확인 가능한 조건 3)
- [ ] (테스트 관련 조건)

# Todo
- [ ] (도메인/모델 작업)
- [ ] (UseCase 작업)
- [ ] (테스트 작성)
- [ ] (API 연결)
```

---

## 예시

```markdown
# 제목
- [MBTI] 사용자로서, 채팅 형식으로 MBTI 검사를 시작하고 싶다 [MBTI-1]

# Domain
- MBTI Test Domain

# Purpose
- 사용자로서, 나 자신의 MBTI 성향을 파악하기 위한 채팅형 검사를 시작하고 싶다.
- 사용자의 검사 시작 요청을 하나의 독립된 분석 세션으로 관리
- 이후 이어질 질문·응답 대화를 하나의 흐름으로 묶을 수 있어야 한다.
- MBTI 검사를 시작할 수 있는 최소 단위의 세션을 생성하는 것

# Success Criteria
- [ ] `POST /mbti-test/start` 요청 시 `MBTITestSession`이 DB에 생성
- [ ] 생성된 세션은 고유한 `session_id`를 가진다
- [ ] 세션의 초기 상태가 `IN_PROGRESS`로 설정
- [ ] 세션 생성 책임만 검증하는 단위 테스트가 존재

# Todo
- [ ] MBTITestSession 도메인 모델 정의
- [ ] 세션 생성 UseCase 구현
- [ ] 세션 생성 단위 테스트 작성
- [ ] POST /mbti-test/start API에서 세션 생성 로직 연결
```

---

## 작성 원칙

- **제목**: `[Domain] 사용자로서, ~하고 싶다 [Domain-N]` (plan.md 형식 그대로)
- **Purpose**: 사용자 스토리 → 배경 → 핵심 목적
- **Success Criteria**: PM/QA가 확인 가능한 조건
- **Todo**: 도메인 → UseCase → 테스트 → API 순서