---
globs:
  - "**/*.{ts,tsx,js,jsx}"
alwaysApply: true
---

# 통합 사고 모델 (Integrated Thinking Model)

## 개요

코드를 작성하거나 수정할 때 자연스럽게 작동하는 **절차기억(procedural memory)** 기반 사고 모델

이 모델은 초기의 Chain-of-Thought(CoT) 단계 추론 아이디어에서 출발해, 실제 개발 워크플로우(탐색, 재구조화 판단, 검증)까지 포함하도록 확장한 형태다.
참고: https://www.ibm.com/kr-ko/think/topics/chain-of-thoughts

> 룰을 "적용"하는 것이 아닌, 코드에 "반응"하는 구조
> 모든 코드 작성(신규/수정/리팩토링)에 이 흐름을 따른다

---

## 핵심 사고 흐름

코드를 마주했을 때의 **자연스러운 인지 흐름**:

```
READ → REACT → ANALYZE → RESTRUCTURE → STRUCTURE → REFLECT
```

---

## 복잡도 판단 기준

| 복잡도 | 기준 | 예시 |
|--------|------|------|
| **LOW** | 단일 파일, 명확한 수정 | 오타 수정, 단순 스타일 변경 |
| **MEDIUM** | 2-5개 파일, 기존 패턴 따름 | 새 컴포넌트 추가, 훅 작성 |
| **HIGH** | 5개+ 파일, 새 패턴/아키텍처 | 도메인 리팩토링, 시스템 설계 |

**자동 판단 힌트:**
- 키워드 `리팩토링`, `아키텍처`, `시스템` → HIGH
- 키워드 `추가`, `수정`, `변경` → MEDIUM
- 키워드 `오타`, `텍스트`, `색상` → LOW
- 정책 키워드 (날짜계산, disabled, filter, 가격) → 최소 MEDIUM

---

## 복잡도별 단계 + 검증

### LOW: READ → REACT → VERIFY

```typescript
Edit("Button.tsx", "확인", "저장")
// 검증: tsc만 (build 생략)
```

### MEDIUM: READ → ANALYZE → STRUCTURE → REFLECT

```typescript
Read("유사 컴포넌트") → Write("새 컴포넌트")
// 검증: tsc + lint
```

### HIGH: 전체 6단계 + planner

```typescript
Task(subagent_type="planner", model="opus", prompt="리팩토링 계획")
// 검증: tsc + lint + build
```

### thinking-model 단계 매핑

| thinking-model | LOW | MEDIUM | HIGH |
|----------------|-----|--------|------|
| READ | O | O | O |
| REACT | O | O | O |
| ANALYZE | - | O | O |
| RESTRUCTURE | - | - | O |
| STRUCTURE | - | O | O |
| REFLECT | - | O | O |

### 에이전트 연계

| 복잡도 | 에이전트 | 모델 |
|--------|----------|------|
| LOW | - (직접 처리) | - |
| MEDIUM | explore, implementation-executor | haiku, sonnet |
| HIGH | planner, code-reviewer | opus, sonnet |

---

## 1. **READ (읽기)** - "맥락을 파악한다"

### 체크리스트

- [ ] 요청 의도를 명확히 이해했는가?
- [ ] 관련 코드가 어디에 있는지 파악했는가?
- [ ] 기존에 유사한 구현이 있는지 검색했는가? ← **기존 로직 참조 원칙**
- [ ] 관련 스펙/룰(.claude/rules)을 확인했는가?
- [ ] import/export 의존성을 파악했는가?
- [ ] 기존 테스트 파일이 있는지 확인했는가?
- [ ] 디자인 시스템 컴포넌트 사용 시 기존 사용 패턴을 Grep으로 확인했는가?

### 내부 점검 (출력 불필요)

```
- 대상: {파일 경로 또는 컴포넌트명}
- 의존성: {import하는 모듈, export하는 대상}
- 요청 핵심: {한 문장으로 요약}
- 참고할 기존 로직: {있다면 경로}
- 참고할 스펙/룰: {있다면 경로}
```

### 기존 로직 탐색 (신규 기능 시 필수)

**비즈니스 로직은 정책이다** - 날짜 계산, 필터 조건, disabled 조건 등은 임의로 새로 구현하지 않는다.

```typescript
// ❌ 나쁜 예: 기존 구현을 무시하고 새로 작성
const last14Days = [addDate(today, { days: -13 }), today]; // -13? -14?

// ✅ 좋은 예: 기존 유틸/상수를 찾아서 재사용
const last14Days = [addDate(today, { days: -14 }), today]; // 기존 getPeriod() 참조
```

**탐색 방법:**
```bash
# 유사 로직 검색
rg "getPeriod\|dateRange\|filterState" src/
```

### 디자인 시스템 컴포넌트 사용 (UI 작업 시 필수)

**디자인 시스템 컴포넌트는 기존 사용 패턴을 반드시 확인한다.** props, variant, color 등을 임의로 추측하지 않는다.

```bash
# 새 컴포넌트 사용 전 기존 패턴 확인
rg "Button" src/ --type tsx | head -10
rg "Typography.*color=" src/ --type tsx | head -10
```

**런타임 에러 방지:** TypeScript가 잡지 못하는 동적 스타일 에러 존재 → 기존 패턴 확인 필수

---

## 2. **REACT (반응)** - "직관적 판단"

### 체크리스트

- [ ] 기존 코드에서 거슬리는 부분이 있는가?
- [ ] 요청대로 구현하면 문제가 생길 것 같은가?
- [ ] 더 나은 접근법이 즉시 떠오르는가?

### 내부 점검 (출력 불필요)

```
- 첫인상: {간단한 소감}
- 우려사항: {있다면}
- 대안 아이디어: {있다면}
```

---

## 3. **ANALYZE (분석)** - "영향 범위를 파악한다"

### 체크리스트

- [ ] 이 변경이 다른 곳에 영향을 주는가?
- [ ] 기존 동작이 무엇인지 정확히 이해했는가?
- [ ] 타입 안전성이 유지되는가?
- [ ] 비즈니스 정책(날짜계산, 필터조건, disabled조건 등)이 기존과 일치하는가?
- [ ] 테스트/스펙 업데이트가 필요한가?

### 내부 점검 (출력 불필요)

```
- 영향 범위: {파일/컴포넌트 목록}
- 기존 동작: {입력 → 출력}
- 리스크: {상/중/하}
```

### UI 상태 변경 영향 확인

```
[값 변경] → [상태 업데이트] → [API 파라미터 반영] → [쿼리 재실행]
                ↓
        연쇄 초기화 필요? (탭 변경 → 필터 리셋)
                ↓
        disabled 조건 연쇄 업데이트?
```

**기존 정책 유지 항목:**

| 항목          | 예시                      |
| ------------- | ------------------------- |
| 화면 정책     | 레이아웃, 순서, 표시 조건 |
| 비활성화 조건 | disabled, readonly        |
| 유효성 검사   | 필수값, 포맷, 범위        |
| 기본값        | 초기 선택값, 기본 필터    |

---

## 4. **RESTRUCTURE (재구조화 판단)** - "구조 변경이 필요한가?"

### 판단 기준

| 구조 변경 필요          | 구조 변경 불필요 |
| ----------------------- | ---------------- |
| 동일 로직 3곳 이상 중복 | 1~2곳 유사 코드  |
| 명백한 책임 분리 위반   | 단순 가독성 개선 |
| 테스트 불가능한 구조    | 취향 차이 수준   |

> **원칙**: 불필요한 추상화를 피한다. 요청받은 것만 수정한다.

---

## 5. **STRUCTURE (구조화)** - "변경 계획을 수립한다"

### 체크리스트

- [ ] 변경을 작은 단위로 분리했는가?
- [ ] 기존 패턴/컨벤션을 따르고 있는가?
- [ ] 각 단계가 독립적으로 검증 가능한가?
- [ ] 필요한 테스트 추가/수정 계획이 포함되었는가?

---

## 6. **REFLECT (성찰)** - "결과를 검토한다"

### 체크리스트

- [ ] 원래 요청을 충족했는가?
- [ ] 의도치 않은 동작 변경이 없는가?
- [ ] 기존 정책(날짜, 필터, disabled 등)과 일치하는가?
- [ ] 더 나은 방법이 있었는가?
- [ ] lint/type/test 등의 검증 결과를 확인했는가?
- [ ] 디자인 시스템 컴포넌트 props가 기존 패턴과 일치하는가?

### 필수 검증 (코드 수정 후)

```bash
# 타입 에러 확인
npx tsc --noEmit | head -50

# 린트 확인
npm run lint
```

> **중요**: TypeScript가 잡지 못하는 런타임 에러(동적 스타일, 잘못된 props 등)가 있으므로
> 새 컴포넌트 사용 시 반드시 기존 패턴을 Grep으로 확인한 후 사용한다.

---

## 작업 모드

상황에 따라 적절한 모드로 전환한다.

| 모드       | 트리거                       | 행동                                |
| ---------- | ---------------------------- | ----------------------------------- |
| **모델링** | 복잡한 비즈니스 로직         | 흐름을 다이어그램/의사코드로 시각화 |
| **탐색**   | 요구사항 불명확, 여러 선택지 | 장단점 비교, 프로토타입 제안        |
| **코칭**   | 사용자가 직접 구현 원함      | 힌트와 방향 제시                    |
| **성찰**   | 막힌 상황, 작업 완료 후      | 접근법 리뷰, 대안 탐색              |

---

## 안전 규칙

### 필수 준수

1. **기존 로직 참조**: 유사 구현이 있으면 반드시 참고한다
2. **정책 유지**: 명시적 요청 없으면 기존 비즈니스 정책을 따른다
3. **최소 변경**: 요청받은 것만 수정한다 (과도한 개선 금지)
4. **검증 필수**: 변경 후 lint/type/build 통과 확인

### 금지 사항

- 요청 없이 "더 나은 패턴"으로 코드 변경
- 기존 정책(날짜계산, 필터조건 등)을 임의로 변경
- 테스트 없이 핵심 로직 수정

---

## 복잡한 작업 시 출력 포맷

간단한 작업은 바로 수행하고, 복잡한 작업(파일 3개 이상, 정책 변경 포함, 리스크 있음)은 아래 포맷 사용:

### 변경 계획

```markdown
## 목표

{한 문장}

## 변경 단계

| #   | 작업   | 파일   | 리스크     |
| --- | ------ | ------ | ---------- |
| 1   | {설명} | {경로} | {상/중/하} |

## 검증

- [ ] lint / build 통과
- [ ] 기존 동작과 동일함 확인
```

---

## 에이전트 연계

**상세**: `@../../instructions/multi-agent/agent-roster.md`

| 단계 | 활용 에이전트 | 모델 |
|------|---------------|------|
| READ | explore (병렬 탐색) | haiku |
| ANALYZE | explore, code-reviewer | haiku, sonnet |
| STRUCTURE | planner (HIGH 복잡도) | opus |
| 구현 | implementation-executor | sonnet |
| REFLECT | lint-fixer, code-reviewer | haiku, sonnet |

### 병렬 실행 패턴

독립 작업은 단일 메시지에서 병렬 호출:

```typescript
// READ 단계: 병렬 탐색
Task(subagent_type="explore", model="haiku", prompt="대상 도메인 분석")
Task(subagent_type="explore", model="haiku", prompt="관련 패키지 분석")

// REFLECT 단계: 병렬 검증
Task(subagent_type="lint-fixer", model="haiku", prompt="린트 수정")
Task(subagent_type="code-reviewer", model="sonnet", prompt="변경사항 리뷰")
```

---

## 참조 문서

| 문서 | 용도 |
|------|------|
| `.claude/instructions/multi-agent/coordination-guide.md` | 병렬 실행 원칙 |
| `.claude/instructions/validation/forbidden-patterns.md` | 금지 패턴 |
