# Phase 기반 실행

> Context Window 초과를 방지하기 위한 대규모 작업 분리 전략

---

## Phase 분리 기준

| 조건 | 판단 | 행동 |
|------|------|------|
| 10개+ 파일 수정 예상 | **필수 분리** | Phase별 5-8개 파일로 제한 |
| 컨텍스트 50% 초과 예상 | **필수 위임** | Sub-agent에 위임 |
| 30분+ 작업 예상 | **권장 분리** | 체크포인트 설정 |
| 3개+ 도메인 걸침 | **권장 분리** | 도메인별 Phase 분리 |

---

## Phase 구조

```
Phase 1: 탐색 + 분석
  → 결과 정리 (.claude/temp/ 또는 프롬프트 내)
  → 검증: 영향 범위 확인

Phase 2: 핵심 구현
  → 가장 중요한 변경부터
  → 검증: tsc --noEmit

Phase 3: 연관 수정
  → Phase 2에 의존하는 파일 수정
  → 검증: tsc + lint

Phase 4: 정리 + 최종 검증
  → import 정리, 불필요 코드 제거
  → 검증: tsc + lint + build
```

---

## Phase 간 컨텍스트 전달

### 파일 기반 핸드오프

```typescript
// Phase 1 결과를 파일로 저장
Task(subagent_type="general-purpose", model="haiku",
  prompt="분석 결과를 .claude/temp/phase1-result.md에 저장")

// Phase 2에서 파일 읽어서 진행
Task(subagent_type="implementation-executor", model="sonnet",
  prompt=".claude/temp/phase1-result.md 읽고 핵심 구현 진행")
```

### 프롬프트 내 컨텍스트 압축

```typescript
// 이전 Phase 결과를 요약하여 전달
Task(subagent_type="implementation-executor", model="sonnet",
  prompt=`
  [Phase 1 결과 요약]
  - 대상 파일: A.tsx, B.tsx, C.ts
  - 기존 패턴: XxxCard 컴포넌트 구조
  - 제약: disabled 조건 유지 필수

  [Phase 2 작업]
  위 분석 기반으로 구현 진행
`)
```

---

## 체크포인트 전략

각 Phase 완료 시:

1. **검증** - tsc/lint 통과 확인
2. **기록** - 변경 파일 목록 정리
3. **판단** - 다음 Phase 진행 가능 여부 확인

```
Phase 완료 → 검증 PASS → 다음 Phase
Phase 완료 → 검증 FAIL → 수정 후 재검증
```

---

## 참조

| 문서 | 용도 |
|------|------|
| `./redundant-exploration-prevention.md` | 중복 탐색 방지 |
| `./sub-agent-distribution.md` | 컨텍스트 분배 |
