# Complexity Judgment

LOW/MEDIUM/HIGH 기준, Plan 에이전트 위임 조건, Agent Teams 사용 조건.

---

## /start — 복잡도 기준

| 복잡도 | 기준 | 전략 |
|--------|------|------|
| **LOW** | 1개 파일, 스타일/텍스트 변경 | 바로 구현 |
| **MEDIUM** | 2-5개 파일, 기존 패턴 | 패턴 확인 후 구현 |
| **HIGH** | 5개+ 파일, 새 아키텍처 | Plan 에이전트 호출 |

### HIGH 복잡도 시 Plan 에이전트 활용

```typescript
Task(
  (subagent_type = 'Plan'),
  (model = 'opus'),
  (prompt = `
  티켓: $ARGUMENTS
  요구사항: {요약된 요구사항}
  Figma 분석: {분석 결과}
  기존 패턴: {확인된 패턴}

  구현 계획 수립 요청
`)
);
```

---

## /bug-fix — 복잡도 기준

| 복잡도 | 기준 | 접근 |
|--------|------|------|
| **LOW** | 단일 파일, 명확한 에러, 재현 쉬움 | 바로 수정 |
| **MEDIUM** | 2-3개 파일, 원인 후보 2-3개 | 옵션 제시 |
| **HIGH** | 5개+ 파일, 근본 원인 불명/간헐적 | 상세 분석 후 옵션 제시 |

> 복잡도가 불확실하면 한 단계 높게 판단.

---

## /refactor — 복잡도 기준

| 복잡도 | 기준 | 접근 |
|--------|------|------|
| **LOW** | 변수명 변경, 단순 추출 | 바로 실행 |
| **MEDIUM** | 함수 분리, 파일 구조화 | 계획 후 실행 |
| **HIGH** | 아키텍처 변경, 패턴 도입 | Plan 에이전트 활용 |

### HIGH 복잡도 시 Plan 에이전트 활용 (refactor)

```typescript
Task(
  (subagent_type = 'Plan'),
  (model = 'opus'),
  (prompt = `
  대상: {리팩토링 대상}
  목표: {개선 목표}
  제약: 기존 정책 유지

  단계별 계획 수립 요청
`)
);
```

---

## 서브태스크 분리 기준 (/start)

| 작업 유형 | 분리 | 예시 |
|-----------|------|------|
| 새 컴포넌트 | O | TabsV2, FilterV2 |
| API 연동 | O | 목록 조회 API |
| 상태 관리 | O | filterAtom |
| 로직 변경 | O | 기간 계산 |
| 스타일 수정 | X | 색상, 간격 수정 |
| 텍스트 변경 | X | 라벨 수정 |

**분리 체크리스트:**
- 새로 만드는 컴포넌트 → 각각 티켓
- API 연동 → 별도 티켓
- 상태 관리 변경 → 별도 티켓
- 로직 변경 → 별도 티켓
- 200줄 이상 변경 → 분리

---

## Agent Teams 사용 조건

### /my-tickets — 병렬 처리 시

**Agent Teams 가능 시 (Claude Max):**
```
TeamCreate → 그룹별 팀원 spawn → 병렬 분석+구현 → 품질 검증 → shutdown
```

**Agent Teams 불가 시 (일반 플랜) — Task 병렬 호출:**
```
독립 티켓을 Task()로 동시 호출:
  Task(subagent_type='general-purpose', prompt='/start QA-52339 분석+구현')
  Task(subagent_type='general-purpose', prompt='/start QA-52316 분석+구현')
  → 동시 실행, 각각 독립적으로 분석+구현
```

---

## 리팩토링 필요 여부 판단

| 리팩토링 필요 | 리팩토링 불필요 |
|--------------|----------------|
| 동일 로직 3곳+ 중복 | 1-2곳 유사 코드 |
| 명백한 책임 분리 위반 | 단순 가독성 개선 |
| 테스트 불가능한 구조 | 취향 차이 수준 |
| 500줄+ 파일 | 200줄 이하 파일 |

---

## Debate 연계 조건

| 상황 | 연계 방식 |
|------|----------|
| **GROUND (복잡도 L)** | 단순 분석으로 결론이 나지 않을 때 debate 호출 |
| **ADAPT (2회 실패)** | 기존 접근 실패 시 debate로 대안 탐색 |
| **설계 분기점** | 2개 이상 동등한 옵션 존재 시 자동 제안 |

---

## MAJOR 변경 — 코어 모듈 터치 시 처리

코어 로직 변경 감지 (`.code-forge/config.json`의 `corePaths` 기준):

```
⚠️ 코어 로직 변경 감지

변경된 코어 파일:
  • packages/shared/utils/payment.ts (QA-52372)
  • packages/ui/components/Modal/index.tsx (QA-52339)

코어 담당자에게 알림을 보낼까요? [Y/N]
  → Y: config.json의 coreOwners에게 Slack DM
  → "⚠️ 코어 모듈 변경: packages/shared/utils/payment.ts
     티켓: QA-52372 | 변경자: @ggombee
     PR: {URL} | 리뷰 부탁드립니다"
```

- 코어 변경이 포함된 PR은 **자동으로 Draft**로 생성
- 코어 담당자를 리뷰어로 지정

MAJOR 변경 확인 대화:
```
"⚠️ packages/shared 변경이 포함됩니다.
 코어 개발자 확인 후 진행할까요?"
  [Y] → 진행 (PR에 needs-core-approval 라벨)
  [N] → 보류
```
