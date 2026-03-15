# Sub-agent 컨텍스트 분배 전략

> 메인 에이전트의 컨텍스트를 보호하기 위해 작업을 Sub-agent에 분산한다

---

## 핵심 원칙

| 원칙 | 설명 |
|------|------|
| **메인 보호** | 메인 에이전트는 조율만, 실행은 Sub-agent |
| **결과 압축** | Sub-agent는 전체가 아닌 요약만 반환 |
| **병렬 분산** | 독립 작업은 동시에 여러 Sub-agent에 위임 |

---

## 메인 vs Sub-agent 역할 분리

### 메인 에이전트가 해야 할 것

- 작업 분해 및 할당
- Sub-agent 결과 종합
- 사용자와의 커뮤니케이션
- 최종 판단 및 의사결정

### Sub-agent에 위임해야 할 것

- 코드베이스 탐색 (5개+ 파일)
- 패턴 분석
- 구현 작업
- 린트/빌드 검증
- 코드 리뷰

---

## 위임 패턴

### 패턴 1: 탐색 위임

```typescript
// ❌ 메인에서 직접 탐색 (컨텍스트 소비)
Glob("src/**/*.tsx")
Read("src/components/A.tsx")
Read("src/components/B.tsx")
Read("src/components/C.tsx")
// ... 10개 파일 읽기 → 컨텍스트 압박

// ✅ Sub-agent에 위임 (결과만 수신)
Task(subagent_type="explore", model="haiku",
  prompt="src/components/ 내 카드 컴포넌트 패턴 분석. 공통 패턴과 주요 차이점만 요약")
// → 압축된 분석 결과만 컨텍스트에 추가
```

### 패턴 2: 구현 위임

```typescript
// 메인에서 계획만 수립
// → 구현은 Sub-agent에 위임
Task(subagent_type="implementation-executor", model="sonnet",
  prompt=`
  구현 계획:
  1. OrderCard 컴포넌트 생성 (기존 ProductCard 패턴 참조)
  2. useOrderQuery 훅 작성
  3. 페이지에 연결

  기존 패턴: src/components/ProductCard/ 참조
`)
```

### 패턴 3: 검증 위임

```typescript
// 구현 후 검증을 병렬로 위임
Task(subagent_type="lint-fixer", model="haiku", prompt="tsc/eslint 오류 수정")
Task(subagent_type="code-reviewer", model="sonnet", prompt="변경사항 코드 리뷰")
```

---

## 컨텍스트 예산 관리

| 작업 규모 | 메인 컨텍스트 사용 | Sub-agent 위임 |
|-----------|-------------------|---------------|
| 소 (1-3파일) | 직접 처리 | 불필요 |
| 중 (4-8파일) | 계획 + 핵심 파일만 | 탐색 + 검증 위임 |
| 대 (9개+파일) | 계획만 | 탐색 + 구현 + 검증 모두 위임 |

---

## 결과 수신 규칙

Sub-agent 결과를 받을 때:

1. **전체 탐색 결과 전달 금지** - 요약만 수신
2. **파일 내용 그대로 전달 금지** - 패턴/구조만 전달
3. **구현 결과는 파일 목록만** - 코드 전체 아닌 변경 요약

```typescript
// ❌ Sub-agent에게 "모든 내용을 보고해" 지시
Task(prompt="모든 컴포넌트의 전체 코드를 분석 결과에 포함")

// ✅ Sub-agent에게 "요약만 보고해" 지시
Task(prompt="컴포넌트 패턴을 분석하고 공통점/차이점만 3줄로 요약")
```

---

## 참조

| 문서 | 용도 |
|------|------|
| `./redundant-exploration-prevention.md` | 중복 탐색 방지 |
| `./phase-based-execution.md` | Phase 기반 실행 |
| `../multi-agent/coordination-guide.md` | 에이전트 협업 원칙 |
