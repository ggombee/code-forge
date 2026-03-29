---
alwaysApply: true
---

# Candidate Profile + Practice Knowledge 참조 규칙

코드 구현/리뷰/리팩토링 시 아래 자료를 반드시 참조한다.

## 1. Candidate Profile

`${CLAUDE_PLUGIN_ROOT}/.candidate/profile.md`

사용자의 코딩 철학, 트레이드오프 판단 기준, 회사 코드에서 확인된 습관이 기록되어 있다.

**적용 규칙:**
- 코드 작성 시 profile.md 기준에 맞춰 구현 (interface 기본, 훅 반환값 객체, handleXxx 등)
- 트레이드오프 발생 시 profile에 해당 항목이 있으면 따른다. 없으면 사용자에게 질문
- 상충 시 자의적으로 무시하지 않고 물어본다
- **다른 프로젝트 탐색 금지**: profile.md가 유일한 참조

## 2. Practice Knowledge

Phase별 참조는 `${CLAUDE_PLUGIN_ROOT}/skills/practice/references/phase-guide.md`를 따른다.

- `${CLAUDE_PLUGIN_ROOT}/skills/practice/knowledge/build-guide.md` — 구현 시 참조 (React + TS + 삽질기록)
- `${CLAUDE_PLUGIN_ROOT}/skills/practice/knowledge/review-guide.md` — 리팩토링/리뷰 시 참조 (설계철학 + 안티패턴 + 성능 + 평가)
- `${CLAUDE_PLUGIN_ROOT}/skills/practice/knowledge/interview-guide.md` — 면접 대비
- `${CLAUDE_PLUGIN_ROOT}/skills/practice/knowledge/toss-context.md` — 특정 회사 과제에서만

**Phase 1 (구현):** profile.md + build-guide.md만. review-guide 읽기 금지.
**Phase 2 (리팩토링):** profile.md + review-guide.md + build-guide.md
**Phase 3 (면접):** interview-guide.md + DECISIONS.md

## 2.5. 구현 시 설명 규칙 (Phase 1)

코드를 구현할 때 **왜 이렇게 하는지**를 사용자에게 간단히 설명하면서 진행한다.

- 각 기능 구현 전: "이건 이렇게 구현하려고 합니다. 이유: ..." (1-2줄)
- 트레이드오프가 있으면: "A와 B 방법이 있는데, profile 기준으로 A로 갑니다" 또는 "어떻게 할까요?"
- 구현 후: "이렇게 했습니다" + diff (긴 설명 불필요)
- **묵묵히 코드만 쓰지 않는다** — 사용자가 "뭘 왜 하고 있는지" 항상 알 수 있어야 함
- 단, 자명한 것(import 추가, 오타 수정 등)은 설명 생략

## 3. 우선순위

```
profile.md (개인 취향) > knowledge (일반론) > 에이전트 기본 규칙
```

상충 시 profile 우선. 근거가 명확히 다르면 물어본다.

## 4. 커밋 컨벤션

```
chore: 초기 세팅, 폴더 구조 변경
feat: 기능 구현
fix: 버그 수정
refactor: 구조 개선, 추상화
test: 테스트 추가
docs: README, 문서
```

**필수 규칙:**
- Co-Authored-By 절대 넣지 않음
- 이모지 넣지 않음
- 존댓말 금지 — "구현합니다" X → "추가", "수정" 등 간결체
- 메시지는 짧고 구체적으로: `feat: add reservation filter logic`
- 하나의 커밋 = 하나의 의도 — feat와 refactor를 섞지 않음

## 5. AI 흔적 제거

- 이모지, Co-Authored-By, 과도한 주석, AI 특유 문체 금지
- 코드 주석은 "왜(Why)"만. "무엇(What)"은 코드가 설명
- 개발자 노트 톤으로 작성
- 획일적 패턴 금지 — 모든 컴포넌트가 같은 구조, 모든 훅이 같은 형태 X
