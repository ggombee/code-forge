# Multi-Agent Coordination Guide

> 멀티 에이전트 병렬 실행으로 작업 효율 극대화

---

## 핵심 원칙

| 원칙           | 방법                                  | 효과               |
| -------------- | ------------------------------------- | ------------------ |
| **PARALLEL**   | 독립 작업은 단일 메시지에서 동시 호출 | 5-10배 속도 향상   |
| **BACKGROUND** | 긴 작업은 백그라운드로 실행           | 메인 컨텍스트 보호 |
| **DELEGATE**   | 전문 에이전트에 즉시 위임             | 품질 향상          |

```typescript
// ❌ 순차 실행 (120초)
Task(subagent_type="explore", prompt="파일 구조 분석")  // 60초
Task(subagent_type="explore", prompt="API 패턴 분석")   // 60초

// ✅ 병렬 실행 (60초) - 단일 메시지에서 호출
Task(subagent_type="explore", model="haiku", prompt="파일 구조 분석")
Task(subagent_type="explore", model="haiku", prompt="API 패턴 분석")
```

---

## 역할 기반 서브에이전트 원칙

### general-purpose + 역할 프롬프트

구현이 필요한 서브에이전트는 **항상 `general-purpose`로 spawn**한다.
역할별 전문 지식은 **프롬프트에서 스킬/규칙 파일 읽기를 지시**하여 주입한다.

```
general-purpose + "figma-to-code 스킬 읽어" = 디자이너 역할 + 전체 도구
general-purpose + "refactor 스킬 읽어"      = 리팩토러 역할 + 전체 도구
general-purpose + "bug-fix 스킬 읽어"       = 버그 수정 역할 + 전체 도구
```

**이유:**
- `explore`는 Read/Glob/Grep/Bash만 가능 (Write/Edit 없음 → 구현 불가)
- `lint-fixer`는 Bash/Read/Edit만 가능 (단순 수정 전용)
- `general-purpose`는 Read, Write, Edit, Bash, Grep, Glob 모두 가능
- 프롬프트에서 스킬 파일을 읽게 하면 전문 지식 + 전체 도구를 동시에 확보

### 에이전트 타입 선택 기준

| 작업 유형          | 에이전트 타입       | 이유                        |
| ------------------ | ------------------- | --------------------------- |
| 읽기 전용 탐색     | `explore`           | 빠르고 가볍다               |
| 린트/타입 수정만   | `lint-fixer`        | 규칙 기반 단순 수정         |
| 구현이 필요한 작업 | **general-purpose** | Write/Edit/Bash 필요        |
| 스킬 지식 필요     | **general-purpose** | 스킬 파일 읽기 + 구현 동시  |

### 규칙/스킬 참조 범위

| 항목                 | 자동 로드 | 비고                             |
| -------------------- | :-------: | -------------------------------- |
| CLAUDE.md            |     O     | 프로젝트 전체 규칙               |
| .claude/rules/       |     O     | 코딩 표준, 컨벤션 등             |
| .claude/agents/*.md  |     O     | 해당 subagent_type 정의만 적용   |
| Skill 도구 (/start)  |     X     | 메인 에이전트 전용                |
| MCP 도구             |     X     | 메인 에이전트 전용                |

---

## 역할별 프롬프트 템플릿

### 퍼블리싱 (디자이너)

```typescript
Task(subagent_type="general-purpose", model="sonnet",
  prompt=`
  ## 역할: 퍼블리싱 담당

  ### 사전 준비 (필수)
  1. .claude/skills/figma-to-code/SKILL.md를 읽고 규칙을 숙지해
  2. .claude/rules/frontend/ 관련 규칙도 읽어

  ### 디자인 분석 결과
  {레이아웃, 색상, 타이포그래피, 컴포넌트 구조 등}

  ### 작업 내용
  {구체적 구현 지시}
`)
```

### API 연동

```typescript
Task(subagent_type="general-purpose", model="sonnet",
  prompt=`
  ## 역할: API 연동 담당

  ### 사전 준비 (필수)
  1. .claude/rules/backend/ 관련 규칙 읽어
  2. 기존 서비스/쿼리 패턴 분석

  ### 작업 내용
  {API 스펙, 엔드포인트, 타입 정보 등}
`)
```

### 리팩토링

```typescript
Task(subagent_type="general-purpose", model="opus",
  prompt=`
  ## 역할: 리팩토링 담당

  ### 사전 준비 (필수)
  1. .claude/skills/refactor/SKILL.md를 읽고 정책 보호 원칙 숙지

  ### 작업 내용
  {리팩토링 대상, 목표, 제약 조건}
`)
```

### 버그 수정

```typescript
Task(subagent_type="general-purpose", model="sonnet",
  prompt=`
  ## 역할: 버그 수정 담당

  ### 사전 준비 (필수)
  1. .claude/skills/bug-fix/SKILL.md를 읽고 분석 → 옵션 → 수정 흐름 숙지

  ### 작업 내용
  {에러 증상, 발생 조건, 관련 파일}
`)
```

---

## 모델 라우팅 전략

### 기본 복잡도 기준

| 복잡도     | 모델   | 사용 케이스                               |
| ---------- | ------ | ----------------------------------------- |
| **LOW**    | haiku  | 파일 탐색, 단순 검색, 린트 수정           |
| **MEDIUM** | sonnet | 코드 리뷰, 테스트 생성, 구현              |
| **HIGH**   | opus   | 아키텍처 설계, 복잡한 버그, 리팩토링 분석 |

### 정책 키워드 = 모델 상향

**비즈니스 로직/정책 키워드가 포함되면 sonnet 이상:**

| 정책 키워드                | 최소 모델  | 이유               |
| -------------------------- | ---------- | ------------------ |
| 날짜 계산, 기간 로직       | **opus**   | 비즈니스 규칙 복잡 |
| disabled, readonly 조건    | **sonnet** | 상태 의존성        |
| 필터 조건, 상태 연쇄       | **sonnet** | 연쇄 영향          |
| 가격, 할인, 계산 로직      | **opus**   | 정확성 중요        |
| 상태 전이, 워크플로우      | **opus**   | 상태 머신 이해     |

### 모델 선택 예시

```typescript
// haiku - 단순 구조 탐색만
Task(subagent_type="explore", model="haiku", prompt="src 폴더 구조 파악")

// sonnet - 로직 분석, 컴포넌트 이해
Task(subagent_type="explore", model="sonnet", prompt="필터 disabled 조건 분석")

// opus - 정책/비즈니스 로직 분석
Task(subagent_type="explore", model="opus", prompt="날짜 계산 로직 분석")
```

---

## 에이전트 조합 패턴

상세 조합 패턴 및 에이전트 선택 가이드: `./agent-roster.md`

---

## 컨텍스트 보존 전략

### 1. 파일 기반 핸드오프

에이전트 간 컨텍스트는 파일로 전달 (Write 가능한 에이전트만):

```typescript
// Agent 1: 분석 결과를 파일에 저장 (general-purpose는 Write 가능)
Task(subagent_type="general-purpose", model="haiku", prompt="코드 분석 후 .claude/temp/analysis.md에 저장")

// Agent 2: 파일 읽어서 작업 수행
Task(subagent_type="implementation-executor", prompt=".claude/temp/analysis.md 읽고 구현")
```

> **주의**: `explore`는 Write 도구가 없으므로 파일 저장 불가. 파일 핸드오프가 필요하면 `general-purpose` 사용.

### 2. 프롬프트 내 컨텍스트 명시

```typescript
Task(subagent_type="implementation-executor",
  prompt=`
  대상: src/components/TrackingCard.tsx
  기존 패턴: src/components/OrderCard.tsx 참조
  규칙: .claude/rules/frontend/ 참조
`)
```

---

## 에러 핸들링

| 전략              | 설명                          | 적용         |
| ----------------- | ----------------------------- | ------------ |
| **실패 격리**     | 에이전트 실패가 전체에 영향 X | 병렬 실행 시 |
| **모델 에스컬레이션** | haiku 실패 → sonnet → opus | 복잡도 오판  |
| **재시도**        | 최대 3회, 지수 백오프         | 일시적 실패  |
| **범위 축소**     | 타임아웃 시 작업 범위 축소    | 대규모 탐색  |

```typescript
// 병렬 실행 중 일부 실패해도 나머지 결과 활용
Task(...)  // 성공 → 결과 사용
Task(...)  // 실패 → 무시하고 진행
Task(...)  // 성공 → 결과 사용
```

---

## 참조 문서

| 문서              | 경로                                  |
| ----------------- | ------------------------------------- |
| 에이전트 목록     | `./agent-roster.md`                   |
| 금지 패턴         | `../validation/forbidden-patterns.md` |
| 필수 행동         | `../validation/required-behaviors.md` |
