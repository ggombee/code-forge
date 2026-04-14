# E2E Forge Loop — 설계 문서

> 작성일: 2026-04-03
> 상태: 설계 완료 → 구현 → 검증 대기

---

## 1. 개요

E2E Forge Loop는 code-forge의 화면 단위 E2E 테스트 자동화 시스템이다.
기존 테스트(단위/컴포넌트)가 `assayer` 에이전트로 처리되는 것과 달리,
E2E는 실제 브라우저에서 사용자 흐름을 검증하며 **Playwright** 기반으로 동작한다.

### 핵심 원칙

- **멈추지 않는다** — 같은 방법으로 3번 실패하면 전략을 바꾼다 (에스컬레이션)
- **GAVA 사고모델 준수** — VERIFY(자동 수정) → ADAPT(접근법 전환) → Human(도메인 지식)
- **기존 자산 재활용** — assayer BDD, Codex 페어, Debate, Ralph Loop 패턴 조합

---

## 2. 스킬 구성

| 스킬 | 역할 |
|------|------|
| `/setup-e2e` | Playwright 환경 초기 세팅 |
| `/e2e` | E2E 테스트 워크플로우 (도출 → 생성 → Forge Loop) |

### 기존 스킬 수정

| 스킬 | 변경 내용 |
|------|----------|
| `/start` | 5단계 계획에 "E2E 전략" 섹션 추가 |
| `/done` | `--e2e` 옵션 추가, 테스트 전략에 E2E 케이스 포함 |

---

## 3. `/e2e` 전체 흐름

```
/e2e [페이지경로 or Figma URL or --all]

Phase 1: 테스트 케이스 도출
  ├─ e2e/*.spec.ts 존재? → "기존 케이스 사용?" 확인
  ├─ Figma URL → MCP 화면 분석 → BDD 시나리오
  ├─ 경로만 → 라우트 + 페이지 컴포넌트 분석 → 화면 흐름
  └─ 사용자 확인: "이 시나리오로 진행?"

Phase 2: Playwright 코드 생성
  ├─ Page Object 생성 (화면별)
  ├─ Spec 파일 생성 (시나리오별)
  └─ Fixture 생성 (인증, 데이터)

Phase 3: Forge Loop (spec 단위)
  ├─ spec 1 → [Stage 1~4] → PASS → 다음
  ├─ spec 2 → [Stage 1~4] → PASS → 다음
  └─ 전체 완료 or 스킵 목록

Phase 4: 최종 리포트
  ├─ 통과/실패/스킵 요약
  ├─ 스킵 항목 재시도 여부
  └─ HTML 리포트 경로
```

---

## 4. Forge Loop — 에스컬레이션 기반 루프

### 구조

```
┌─────────────────────────────────────────────────┐
│               Forge Loop (per spec)              │
│                                                  │
│  Stage 1: Self-Fix (시도 1~3)                    │
│    GAVA: VERIFY                                  │
│    에러 분류 → 선택자/타이밍/Assert 자동 수정       │
│    3회 실패 → 에스컬레이션 ↓                       │
│                                                  │
│  Stage 2: Codex Pair (시도 4~6)                   │
│    GAVA: VERIFY + 다른 시각                       │
│    Codex에 실패 맥락 전달 → 크로스 모델 분석         │
│    Claude가 놓친 blind spot 탐지                   │
│    3회 실패 → 에스컬레이션 ↓                       │
│                                                  │
│  Stage 3: Debate + ADAPT (시도 7~9)               │
│    GAVA: ADAPT                                   │
│    "테스트가 틀렸나 vs 구현이 틀렸나" 토론           │
│    합의 결과에 따라:                               │
│      accept A → 테스트 재도출 (Phase 1 재진입)      │
│      accept B → 구현 수정 (deep-executor)          │
│      compromise → 범위 조정 + 부분 수정             │
│    3회 실패 → 에스컬레이션 ↓                       │
│                                                  │
│  Stage 4: Human-in-the-Loop (10회+)               │
│    선택지 제시:                                    │
│    [1] 스킵 → 다음 spec (나중에 재시도)             │
│    [2] 힌트 제공 (사용자 도메인 지식)               │
│    [3] 테스트 케이스 수정                          │
│    [4] 전체 루프 중단                              │
│    → 선택 후 루프 재진입                           │
└─────────────────────────────────────────────────┘
```

### Stage별 상세

#### Stage 1: Self-Fix

```
에러 분류 기준:
├─ Selector 에러 → DOM 구조 재분석 → 선택자 수정
├─ Timeout → waitFor 조건 수정, networkidle 대기 추가
├─ Assert 실패 → 기대값 vs 실제값 비교
│   ├─ 기대값이 잘못됨 → 테스트 수정
│   └─ 실제값이 잘못됨 → 구현 버그 가능성 → Stage 2로
└─ 환경 에러 → baseURL, 서버 상태, 인증 토큰 체크
```

#### Stage 2: Codex Pair

```typescript
// Codex MCP 사용 가능 시
mcp__codex__codex({
  prompt: `E2E 테스트 3회 실패. 원인 분석 요청.
    테스트: {spec 내용}
    에러: {최근 3회 에러 로그}
    페이지: {URL}
    놓쳤을 수 있는: 비동기 타이밍, 조건부 렌더링, 네트워크 상태`,
  working_directory: cwd
})

// Codex 없으면 → self-review (Claude가 다른 관점에서 재분석)
// - 전체 페이지 소스 재탐색
// - 네트워크 요청 패턴 분석
// - 실제 DOM 스냅샷과 비교
```

#### Stage 3: Debate + ADAPT

```
Debate 주제: "E2E 테스트 {spec명}이 6회 실패한 근본 원인"

입장 A — 테스트가 잘못됐다:
  - 시나리오가 실제 사용자 흐름과 다르다
  - 선택자/대기 전략이 비현실적이다
  - 테스트 재작성 필요

입장 B — 구현이 잘못됐다:
  - 구현이 요구사항 미충족
  - 비동기 처리 버그
  - 구현 수정 필요

합의 결과 분기:
  accept A → Phase 1 재진입 (테스트 케이스 재도출)
  accept B → deep-executor로 구현 수정
  compromise → 테스트 범위 축소 + 구현 일부 수정
```

#### Stage 4: Human-in-the-Loop

```markdown
## Forge Loop — 자동 해결 한계 도달

**테스트:** {spec명} > "{시나리오명}"
**시도:** 9회 (Self-Fix 3 + Codex 3 + Debate 3)

**분석 요약:**
- Stage 1: {에러 유형} 수정 3회 → {결과}
- Stage 2: Codex 분석 — {핵심 의견}
- Stage 3: Debate 합의 — {결론}

**선택:**
[1] 스킵 → 다음 spec (전체 루프 끝나면 재시도)
[2] 힌트 → 원인 알면 알려주세요
[3] 케이스 수정 → 시나리오 자체 조정
[4] 루프 중단 → 현재까지 결과 저장
```

---

## 5. 에이전트 조합

새 에이전트 없이 기존 에이전트 조합으로 구성:

| Phase | 에이전트/스킬 | 역할 |
|-------|-------------|------|
| Phase 1 (도출) | assayer | BDD 시나리오 도출 패턴 재활용 |
| Phase 2 (생성) | /e2e 스킬 직접 | Playwright 코드 작성 |
| Phase 3 Stage 1 | /e2e 스킬 직접 | 에러 분석 + 자동 수정 |
| Phase 3 Stage 2 | codex 에이전트 | 크로스 모델 검증 |
| Phase 3 Stage 3 | debate 인라인 | 접근법 전환 판단 |
| 구현 수정 필요 시 | deep-executor | Ralph Loop로 구현 수정 |

---

## 6. `/start` · `/done` 연결

### /start 5단계 추가 블록

```markdown
### E2E 전략
- 기존 e2e 케이스: {있음 N개 / 없음}
- 이번 작업 영향 화면: {페이지 목록}
- E2E 필요 여부: {Y — 화면 흐름 변경 / N — 스타일만}
- 권장: `/e2e {페이지경로}` 실행
```

### /done --e2e 옵션

```
/done TICKET-123 --e2e

→ Forge Loop 실행
→ 전체 통과 시에만 커밋/PR 진행
→ 실패 시 "E2E 미통과 항목 있음. 진행?" 확인
```

---

## 7. 검증 체크리스트

구현 완료 후 아래 항목으로 검증:

### 환경 세팅 (/setup-e2e)

- [ ] `npx playwright install` 정상 실행
- [ ] `playwright.config.ts` 생성됨
- [ ] `e2e/` 디렉토리 구조 생성됨
- [ ] `package.json`에 `test:e2e` 스크립트 추가됨
- [ ] 샘플 테스트 (`e2e/sample.spec.ts`) 통과

### 테스트 케이스 도출 (Phase 1)

- [ ] Figma URL → BDD 시나리오 정상 변환
- [ ] 페이지 경로 → 화면 흐름 자동 도출
- [ ] 기존 spec 감지 → "사용할까요?" 프롬프트 표시
- [ ] 사용자 확인 후에만 Phase 2 진입

### 코드 생성 (Phase 2)

- [ ] Page Object 클래스 생성됨
- [ ] Spec 파일 BDD 시나리오와 1:1 매핑
- [ ] Fixture (인증/데이터) 분리됨
- [ ] `npx playwright test --list` 테스트 목록 표시됨

### Forge Loop (Phase 3)

- [ ] Stage 1: 에러 분류 정확 (selector/timeout/assert/환경)
- [ ] Stage 1: 자동 수정 후 재실행 동작
- [ ] Stage 1→2: 3회 실패 시 Codex 에스컬레이션 동작
- [ ] Stage 2: Codex MCP 호출 정상 (MCP 없으면 self-review 폴백)
- [ ] Stage 2→3: 6회 실패 시 Debate 에스컬레이션 동작
- [ ] Stage 3: Debate 합의 결과에 따른 분기 정상
- [ ] Stage 3 accept A: Phase 1 재진입 동작
- [ ] Stage 3 accept B: deep-executor 호출 동작
- [ ] Stage 4: 사용자 선택지 표시
- [ ] Stage 4 [1] 스킵: 다음 spec 이동
- [ ] Stage 4 [2] 힌트: 재시도 동작

### 파이프라인 연결

- [ ] `/start` 계획에 E2E 전략 섹션 표시됨
- [ ] `/done --e2e` 실행 시 Forge Loop 진입
- [ ] Forge Loop 통과 후 커밋/PR 진행됨
- [ ] 미통과 시 사용자 확인 프롬프트 표시

### 리포트

- [ ] 통과/실패/스킵 요약 테이블 출력
- [ ] 스킵 항목 재시도 프롬프트 표시
- [ ] `playwright-report/` 경로 안내

---

## 8. 향후 확장

| 항목 | 설명 |
|------|------|
| Visual Regression | Playwright 스크린샷 → Figma 디자인 비교 자동화 |
| CI 연동 | GitHub Actions에서 /e2e를 PR 체크로 실행 |
| Anvil 연결 | Slack에서 "이 페이지 E2E 돌려줘" → Anvil이 /e2e 실행 |
| 커버리지 | 어떤 화면이 E2E 미커버인지 대시보드 |
