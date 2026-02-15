# Execution Patterns

> 작업 유형별 최적 실행 패턴

**모델 선택 기준**: `./coordination-guide.md` 참조 (단일 진실 공급원)

---

## 패턴 개요

| 패턴                        | 사용 시점               | 토큰 절감     |
| --------------------------- | ----------------------- | ------------- |
| **Agent Teams**             | 3개+ 에이전트 협업 필요 | 팀 기반 협업  |
| **Single-Message Parallel** | 독립 작업 동시 실행     | 50-70%        |
| **Fan-Out/Fan-In**          | 분할 → 병합             | 60-80%        |
| **Sequential Pipeline**     | 의존성 있는 작업        | -             |
| **Batching**                | 대량 파일 처리          | 70-90%        |
| **Background**              | 긴 작업 분리            | 컨텍스트 보호 |

---

## 0. Agent Teams (Claude Max 전용)

3개+ 에이전트 협업 시 TeamCreate → 팀원 spawn → 병렬 협업 → shutdown → TeamDelete.
Agent Teams 미가용 시 패턴 1(Single-Message Parallel)로 폴백.

---

## 1. Single-Message Parallel

**독립 작업을 단일 메시지에서 동시 호출.**

```typescript
// 단순 구조 탐색: haiku
Task(subagent_type="explore", model="haiku", prompt="src 폴더 구조 파악")
Task(subagent_type="explore", model="haiku", prompt="패키지 의존성 목록")

// 정책/로직 분석: sonnet
Task(subagent_type="explore", model="sonnet", prompt="필터 조건 분석 - disabled, 기본값")
Task(subagent_type="explore", model="sonnet", prompt="기간 계산 로직 분석")
```

---

## 2. Fan-Out/Fan-In

**하나의 작업을 여러 에이전트로 분할 후 결과 병합.**

```typescript
// Fan-Out: 도메인별 분석 → 파일 저장 (general-purpose는 Write 가능)
Task(subagent_type="general-purpose", model="sonnet",
  prompt="order 도메인 정책 분석 후 .claude/temp/order.md에 저장")
Task(subagent_type="general-purpose", model="sonnet",
  prompt="payment 도메인 정책 분석 후 .claude/temp/payment.md에 저장")

// Fan-In: 결과 수집
Read(".claude/temp/order.md")
Read(".claude/temp/payment.md")

// 통합 분석 (opus - 복잡한 관계 파악)
Task(subagent_type="planner", model="opus", prompt="도메인 간 정책 관계 분석")
```

> **주의**: `explore`는 Write 도구가 없으므로 파일 저장 불가. Fan-Out에서 결과 저장이 필요하면 `general-purpose` 사용.

---

## 3. Sequential Pipeline

**의존성이 있는 작업의 순차 실행.**

```typescript
// 1단계: 구조 탐색 (haiku)
Task(subagent_type="explore", model="haiku", prompt="파일 구조 파악")

// 2단계: 정책 분석 (sonnet/opus)
Task(subagent_type="explore", model="sonnet", prompt="비즈니스 로직 분석")

// 3단계: 계획 수립 (opus)
Task(subagent_type="planner", model="opus", prompt="분석 결과 기반 구현 계획")

// 4단계: 구현 (sonnet)
Task(subagent_type="implementation-executor", model="sonnet", prompt="계획대로 구현")

// 5단계: 검증 (병렬)
Task(subagent_type="lint-fixer", model="haiku", prompt="린트 수정")
Task(subagent_type="code-reviewer", model="sonnet", prompt="코드 리뷰")
```

---

## 4. Batching

**대량 파일을 청크로 분할하여 처리.**

```typescript
// 린트 수정: haiku (단순 수정)
Task(subagent_type="lint-fixer", model="haiku",
  prompt="파일 처리: file1.ts, file2.ts, file3.ts")

// 타입 수정: sonnet (타입 이해 필요)
Task(subagent_type="lint-fixer", model="sonnet",
  prompt="복잡한 타입 오류 수정: file4.ts, file5.ts")
```

---

## 5. Background

**긴 작업을 백그라운드로 분리.**

```typescript
// 테스트 실행: 백그라운드
Task(subagent_type="general-purpose", model="sonnet",
  run_in_background=true, prompt="전체 테스트 실행 및 결과 정리")
```

---

## 작업별 권장 모델

상세 모델 라우팅 전략: `./coordination-guide.md` (단일 진실 공급원)

---

## 참조 문서

| 문서                      | 용도          |
| ------------------------- | ------------- |
| `./coordination-guide.md` | 핵심 원칙     |
| `./agent-roster.md`       | 에이전트 상세 |
