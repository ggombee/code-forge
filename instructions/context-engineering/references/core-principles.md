# Core Principles - 상세 가이드

## 1. Find the Right Altitude

적절한 추상화 수준 찾기.

### 수준별 비교

| ❌ Too Low | ✅ Right Altitude | ❌ Too High |
|-----------|------------------|-------------|
| 복잡한 조건문 | 명확한 원칙 + 예시 | 모호한 지시 |
| 모든 엣지 케이스 나열 | 핵심 패턴 제공 | 구체성 부족 |
| "If X then Y, unless Z..." | "Follow pattern: [코드]" | "잘 만들어줘" |

### 예시: API 에러 처리

```text
❌ Too Low:
"If status === 400, check error.code. If code === 'INVALID_INPUT',
show field-specific errors. If code === 'VALIDATION_ERROR',
check error.fields array. For each field..."

✅ Right Altitude:
"Handle API errors with appropriate user messages.
Example:
  400 → Show field errors
  401 → Redirect to login
  500 → Show generic error"

❌ Too High:
"적절히 에러 처리해줘"
```

---

## 2. Context as Finite Resource

컨텍스트는 제한된 자원.

### Just-in-Time Loading

| 전략 | 방법 | 효과 |
|------|------|------|
| **@imports** | 필요한 시점에만 로드 | 90%+ 절약 |
| **references/** | 상세 문서 분리 | 메인 파일 간결 |
| **Subagent** | 조사 작업 위임 | 요약만 반환 |

### Minimal Start

```text
1차 시도: 최소 프롬프트
  ↓ 실패
2차 시도: 예시 1개 추가
  ↓ 실패
3차 시도: 제약사항 명시
```

### Token Minimization

```text
❌ "Use TypeScript for type safety and better development experience"
✅ "TypeScript"

❌ "Create a new file called utils.ts and add helper functions"
✅ "utils.ts: helper functions"

❌ 중복 설명
✅ 표 형식 압축
```

---

## 3. Explicit > Implicit (Claude 4.x)

명시적 지시가 핵심.

### Claude 4.x 특징

| 상황 | Claude 3.x | Claude 4.x |
|------|-----------|-----------|
| "Create dashboard" | 추가 기능 자동 포함 | 최소한만 구현 |
| "Suggest changes" | 때때로 바로 구현 | 제안만 |
| "Fix bug" | 주변 코드도 개선 | 버그만 수정 |

### 명시적 지시 패턴

```text
❌ "Create dashboard"
✅ "Create dashboard. Include:
   - User stats cards
   - Activity timeline
   - Quick actions
   - Recent notifications
   Go beyond basics to create fully-featured UI."
```

### Behavior Control

```xml
<!-- 적극적 행동 -->
<default_to_action>
Implement changes directly rather than suggesting.
When you see an opportunity for improvement, apply it.
</default_to_action>

<!-- 보수적 행동 -->
<do_not_act_before_instructions>
Wait for explicit user instruction before taking action.
Only suggest, never implement without confirmation.
</do_not_act_before_instructions>
```

---

## 요약

| 원칙 | 핵심 |
|------|------|
| Right Altitude | 패턴 + 예시 (조건문 ❌) |
| Finite Resource | Just-in-Time, 최소화 |
| Explicit | "Create X with Y and Z" (모호함 ❌) |
