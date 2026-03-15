# Read Tool Parallelization

> 파일 읽기 작업을 병렬화하여 분석 시간 단축

---

## 핵심 원칙

**독립적인 파일 읽기는 항상 병렬로 실행한다.**

---

## 병렬 읽기 기준

| 조건 | 병렬 여부 |
|------|----------|
| **3개+ 독립 파일** | 필수 병렬 |
| **다른 디렉토리** | 권장 병렬 |
| **패턴 매칭 결과** | 권장 병렬 |
| **이전 Read 결과에 의존** | 순차 |
| **동일 파일 반복** | 순차 |

---

## 코드 예시

### ✅ 병렬 읽기 (단일 메시지)

```typescript
// 3개 이상 독립 파일은 반드시 병렬
Read({ file_path: "apps/{앱이름}/src/order/views/list/index.tsx" })
Read({ file_path: "packages/shared/queries/order/index.ts" })
Read({ file_path: "packages/shared/services/order/types.ts" })
```

### ❌ 순차 읽기 (의존성 있을 때만)

```typescript
// 1. 먼저 구조 파악
const result = Glob({ pattern: "apps/{앱이름}/src/order/**/*.tsx" })

// 2. 결과 기반으로 읽기 (의존성 있음 → 순차)
Read({ file_path: result[0] })
```

---

## 성능 개선

| 파일 수 | 순차 시간 | 병렬 시간 | 개선율 |
|---------|----------|----------|--------|
| 3개 | 3N | N | 67% |
| 5개 | 5N | N | 80% |
| 10개 | 10N | N | 90% |

---

## 적용 대상

| 에이전트 | 병렬 읽기 필수 시점 |
|----------|-------------------|
| **explore** | 탐색 결과 파일들 동시 읽기 |
| **analyst** | 관련 문서/코드 동시 읽기 |
| **architect** | 의존성 분석 대상 파일들 |
| **code-reviewer** | 변경된 파일들 동시 읽기 |
| **deep-executor** | 5-10개 파일 동시 읽기 |
| **implementation-executor** | 패턴 확인용 파일들 |
