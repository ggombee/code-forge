# 중복 탐색 방지

> 반복적인 코드베이스 탐색은 가장 큰 컨텍스트 낭비 원인이다

---

## 핵심 규칙

### 같은 파일 반복 읽기 금지

| 허용 | 금지 |
|------|------|
| 파일 수정 후 결과 확인을 위한 재읽기 | 동일 파일을 3회 이상 읽기 |
| 다른 섹션을 읽기 위한 offset 변경 | 이미 읽은 내용 확인을 위한 재읽기 |

### "이미 안다" 원칙

한 번 탐색한 정보는 기억하고 재활용한다:

```
❌ Read("Button.tsx") → 분석 → ... 다른 작업 → Read("Button.tsx") 다시 읽기
✅ Read("Button.tsx") → 분석 결과 기억 → 이후 작업에서 기억 기반 진행
```

---

## 탐색 효율화 전략

### 1. 목적 있는 탐색

```typescript
// ❌ 나쁜 예: 무작위 탐색
Glob("src/**/*")  // 너무 넓음
Read("src/components/index.ts")  // 왜 읽는지 불명확

// ✅ 좋은 예: 목적 기반 탐색
Grep("OrderCard", "src/components/")  // "OrderCard 구현 찾기"
Read("src/components/OrderCard/index.tsx")  // "기존 패턴 확인"
```

### 2. 계층적 탐색 (넓은 → 좁은)

```
1단계: Glob으로 파일 구조 파악
2단계: Grep으로 관련 파일 필터
3단계: Read로 핵심 파일만 상세 확인
```

### 3. 병렬 탐색

독립적인 탐색은 병렬로 수행:

```typescript
// ✅ 병렬 탐색
Task(subagent_type="explore", model="haiku", prompt="컴포넌트 구조 분석")
Task(subagent_type="explore", model="haiku", prompt="API 서비스 패턴 분석")
```

---

## Sub-agent 위임 기준

메인 에이전트가 직접 탐색하면 컨텍스트를 소비한다.
**탐색 결과만 필요한 경우 Sub-agent에 위임:**

| 직접 탐색 | Sub-agent 위임 |
|-----------|---------------|
| 1-2개 파일 확인 | 5개+ 파일 탐색 필요 |
| 이미 위치를 아는 파일 | 위치를 모르는 파일 검색 |
| 단순 내용 확인 | 패턴 분석이 필요한 탐색 |

---

## 안티패턴

| 안티패턴 | 결과 | 대안 |
|---------|------|------|
| 같은 Glob 패턴 반복 실행 | 컨텍스트 낭비 | 결과 기억 |
| 전체 파일 읽고 일부만 사용 | 토큰 낭비 | offset/limit 활용 |
| 탐색과 구현을 같은 에이전트에서 | 컨텍스트 압박 | 탐색은 Sub-agent 위임 |

---

## 참조

| 문서 | 용도 |
|------|------|
| `./sub-agent-distribution.md` | 컨텍스트 분배 전략 |
| `./phase-based-execution.md` | Phase 기반 실행 |
