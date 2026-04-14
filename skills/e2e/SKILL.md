---
name: e2e
description: 화면 단위 E2E 테스트 자동화. Figma/코드 기반 테스트 케이스 도출 → Playwright 코드 생성 → Forge Loop(에스컬레이션 기반 자율 실행).
---

# /e2e — E2E Forge Loop

화면 단위 E2E 테스트를 자동으로 도출, 생성, 실행합니다.
**Forge Loop**로 모든 테스트가 통과할 때까지 자율 반복하며,
단계별 에스컬레이션으로 다양한 전략을 시도합니다.

설계 문서: `@../../docs/e2e-forge-loop-design.md`

**[즉시 실행]** 아래 워크플로우를 바로 시작하세요.

---

## 사용법

```
/e2e src/pages/order/          # 페이지 경로 기반
/e2e --figma https://...       # Figma 디자인 기반
/e2e --all                     # 전체 라우트 스캔
/e2e e2e/order-flow.spec.ts    # 기존 spec 재실행 (Forge Loop)
```

| 옵션 | 설명 |
|------|------|
| `--figma [URL]` | Figma 화면에서 사용자 흐름 추출 |
| `--all` | 전체 라우트 스캔 → 화면별 spec 생성 |
| `--skip-gen` | 코드 생성 스킵, 기존 spec만 Forge Loop 실행 |
| `--max-retry N` | Stage별 최대 재시도 횟수 (기본 3) |

---

## 전제 조건

- Playwright 설치 필수. 미설치 시 → "`/setup-e2e`를 먼저 실행하세요" 안내
- 개발 서버 실행 중 (또는 `playwright.config.ts`에 `webServer` 설정)

```bash
# 전제 조건 체크
ls node_modules/@playwright/test 2>/dev/null || echo "NO_PLAYWRIGHT"
ls playwright.config.* 2>/dev/null || echo "NO_CONFIG"
```

---

## Phase 1: 테스트 케이스 도출

### Arguments: `$ARGUMENTS`

**입력 분기:**

| 입력 | 동작 |
|------|------|
| 페이지 경로 (`src/pages/...`) | 해당 페이지 컴포넌트 + 라우트 분석 |
| Figma URL (`--figma`) | Figma MCP로 화면 분석 → 사용자 흐름 추출 |
| `--all` | 전체 라우트 파일 스캔 → 화면 목록 도출 |
| 기존 spec 파일 (`e2e/*.spec.ts`) | Phase 1~2 스킵 → Phase 3 직행 |

### 1-1. 기존 E2E 케이스 확인

```bash
ls e2e/*.spec.ts 2>/dev/null | wc -l
```

- 있으면 → "기존 {N}개 spec이 있습니다. 기존 케이스로 실행할까요, 새로 도출할까요?"
- 없으면 → 도출 진행

### 1-2. Figma 기반 도출 (--figma 있을 때)

```
mcp__figma__get_metadata({ fileKey, nodeId })
mcp__figma__get_screenshot({ fileKey, nodeId })
```

스크린샷에서 추출:
- 화면 상태 (초기/로딩/에러/빈 상태/데이터 있음)
- 사용자 인터랙션 (버튼, 폼 입력, 네비게이션)
- 화면 간 전이 흐름

### 1-3. 코드 기반 도출 (경로만 있을 때)

```bash
# 라우트 구조 분석
grep -r "path:" src/routes/ 2>/dev/null || grep -r "getServerSideProps\|getStaticProps" src/pages/

# 페이지 컴포넌트 분석
# - 폼 필드, 버튼, 조건부 렌더링, API 호출 추출
```

### 1-4. BDD 시나리오 출력 (사용자 확인)

```markdown
## E2E 테스트 시나리오

### 페이지: 주문 목록 (/orders)

| # | 시나리오 | 사전 조건 | 기대 결과 |
|---|---------|----------|----------|
| 1 | 주문 목록이 정상 로드된다 | 로그인 상태 | 테이블에 주문 N건 표시 |
| 2 | 검색 필터로 주문을 찾는다 | 주문 데이터 존재 | 필터링된 결과 표시 |
| 3 | 주문 상세로 이동한다 | 주문 1건 이상 | 상세 페이지 렌더링 |
| 4 | 빈 상태가 올바르게 표시된다 | 주문 0건 | 빈 상태 메시지 표시 |

이 시나리오로 진행할까요? [Y/N/수정]
```

---

## Phase 2: Playwright 코드 생성

사용자 확인 후 코드를 생성합니다.

### 2-1. Page Object 생성

화면 단위로 PO 클래스를 생성합니다:

```typescript
// e2e/pages/order-list.page.ts
import { Page, Locator } from '@playwright/test';
import { BasePage } from './base.page';

export class OrderListPage extends BasePage {
  readonly searchInput: Locator;
  readonly orderTable: Locator;
  readonly emptyState: Locator;

  constructor(page: Page) {
    super(page);
    this.searchInput = page.getByPlaceholder('주문번호 검색');
    this.orderTable = page.getByRole('table');
    this.emptyState = page.getByText('주문 내역이 없습니다');
  }

  async search(keyword: string) {
    await this.searchInput.fill(keyword);
    await this.searchInput.press('Enter');
    await this.page.waitForLoadState('networkidle');
  }

  async clickOrder(index: number) {
    await this.orderTable.getByRole('row').nth(index + 1).click();
  }
}
```

### 2-2. Spec 파일 생성

시나리오별 `.spec.ts`를 생성합니다:

```typescript
// e2e/order-list.spec.ts
import { test, expect } from '@playwright/test';
import { OrderListPage } from './pages/order-list.page';

test.describe('주문 목록', () => {
  let orderPage: OrderListPage;

  test.beforeEach(async ({ page }) => {
    orderPage = new OrderListPage(page);
    await orderPage.navigate('/orders');
  });

  test('주문 목록이 정상 로드된다', async () => {
    await expect(orderPage.orderTable).toBeVisible();
  });

  test('검색 필터로 주문을 찾는다', async () => {
    await orderPage.search('ORD-001');
    await expect(orderPage.orderTable.getByRole('row')).toHaveCount(2); // header + 1 result
  });
});
```

### 2-3. Fixture 생성

인증이 필요한 테스트용 fixture:

```typescript
// e2e/fixtures/auth.fixture.ts
// 프로젝트 인증 방식에 맞게 자동 구성
// - 쿠키 기반: storageState 저장/로드
// - 토큰 기반: localStorage 주입
// - 세션 기반: 로그인 API 직접 호출
```

### 2-4. 생성 완료 확인

```bash
npx playwright test --list
```

테스트 목록이 표시되면 Phase 3 진입.

---

## Phase 3: Forge Loop — 에스컬레이션 기반 자율 실행

**spec 단위로 Ralph Loop를 실행합니다.** 각 spec은 독립적으로 Stage 1~4를 거칩니다.

```
for each spec in e2e/*.spec.ts:
  forge_loop(spec)
  if PASS → 다음 spec
  if SKIP → 스킵 목록에 추가, 다음 spec
```

---

### Stage 1: Self-Fix (시도 1~3)

**GAVA: VERIFY**

```bash
npx playwright test {spec} --reporter=json
```

**PASS → 다음 spec으로 이동.**

FAIL 시 에러 분류:

| 에러 유형 | 감지 방법 | 자동 수정 |
|----------|----------|----------|
| **Selector** | `locator.click: Error` / `strict mode violation` | DOM 재분석 → 선택자 수정 |
| **Timeout** | `Timeout 30000ms exceeded` | `waitFor` 조건 수정 / `networkidle` 추가 |
| **Assert** | `expect(received).toBe(expected)` | 기대값 vs 실제값 비교 → 테스트 or 구현 판단 |
| **Navigation** | `page.goto: net::ERR_CONNECTION_REFUSED` | 서버 상태 체크 → 재시작 안내 |

**수정 → 재실행. 3회 실패 시 Stage 2로.**

---

### Stage 2: Codex Pair Review (시도 4~6)

**GAVA: VERIFY + 다른 시각**

Claude가 혼자 3번 같은 식으로 실패 → blind spot 가능성. 다른 모델 투입.

```
Codex MCP 사용 가능 여부 체크:
  1. mcp__codex__codex 도구 사용 가능? → MCP 모드
  2. `which codex` 실행 가능? → CLI Headless 모드
  3. 둘 다 불가 → Self-Review 폴백
```

**MCP 모드:**
```typescript
mcp__codex__codex({
  prompt: `E2E 테스트 3회 실패. 원인 분석 요청.

테스트 코드:
{spec 파일 전체}

최근 3회 에러 로그:
{에러 로그}

대상 페이지 소스:
{페이지 컴포넌트 핵심 부분}

확인 요청:
1. 비동기 타이밍 이슈가 있는가?
2. 조건부 렌더링으로 DOM이 달라지는 구간이 있는가?
3. 네트워크 요청 타이밍에 의존하는 부분이 있는가?
4. 내가 놓친 선택자 전략이 있는가?`,
  working_directory: cwd
})
```

**CLI Headless 모드:**
```bash
codex exec -m o4-mini "E2E 테스트 실패 분석: {에러 요약}. 수정안 제시."
```

**Self-Review 폴백 (Codex 없을 때):**
- 전체 페이지 소스 재탐색 (이전에 읽지 않은 파일까지)
- 실제 브라우저 DOM 스냅샷 캡처 → 비교
- 네트워크 요청 패턴 분석 (`page.on('request')`)
- **다른 관점**: "이 테스트가 실패하는 가장 단순한 이유는?"

Codex/Self-Review 의견 반영 → 수정 → 재실행. **3회 실패 시 Stage 3로.**

---

### Stage 3: Debate + ADAPT (시도 7~9)

**GAVA: ADAPT — 접근법 자체를 전환**

6회 같은 방식으로 실패 = 단순 수정으로 안 됨. 질문을 바꿔야 함.

**Debate 실행 (인라인):**

```
주제: "E2E 테스트 {spec명}이 6회 실패한 근본 원인"

입장 A — 테스트가 잘못됐다:
  증거: {에러 로그에서 테스트 측 문제 근거}
  주장: 시나리오가 실제 흐름과 다르거나, 선택자 전략이 비현실적

입장 B — 구현이 잘못됐다:
  증거: {에러 로그에서 구현 측 문제 근거}
  주장: 구현이 요구사항을 충족하지 않거나, 비동기 버그 존재

3라운드 진행 → 합의 도출
```

**Codex 있으면 cross-model debate, 없으면 self-debate.**

**합의 결과에 따른 분기:**

| 합의 | 행동 |
|------|------|
| **accept A** (테스트 문제) | Phase 1 재진입 → 해당 시나리오 재도출 → Phase 2 재생성 |
| **accept B** (구현 문제) | deep-executor 호출 → 구현 수정 → Stage 1부터 재시도 |
| **compromise** | 테스트 범위 축소 + 구현 일부 수정 → Stage 1부터 재시도 |

```typescript
// accept B: 구현 수정이 필요한 경우
Task(subagent_type='deep-executor', prompt=`
  E2E 테스트가 지속 실패. Debate 결과 구현 수정 필요.

  실패 테스트: {spec명}
  근본 원인: {debate 합의 내용}
  수정 대상: {파일 목록}

  수정 후 반드시 lint + build 검증.
`)
```

**3회 실패 시 Stage 4로.**

---

### Stage 4: Human-in-the-Loop (10회+)

자동 해결 한계 도달. 사용자에게 **판단을 위임**하되, **루프를 중단하지 않음**.

```markdown
## Forge Loop — 자동 해결 한계 도달

**테스트:** {spec명} > "{시나리오명}"
**총 시도:** 9회 (Self-Fix 3 + Codex 3 + Debate 3)

### 단계별 분석 요약
| Stage | 시도 | 전략 | 결과 |
|-------|------|------|------|
| Self-Fix | 3회 | {에러유형} 수정 | {마지막 에러} |
| Codex | 3회 | {Codex 의견 요약} | {마지막 에러} |
| Debate | 3회 | {합의: accept A/B/compromise} | {마지막 에러} |

### 현재 에러
\`\`\`
{최종 에러 로그}
\`\`\`

### 선택해주세요
[1] **스킵** → 이 spec 건너뛰고 다음으로 (나중에 재시도)
[2] **힌트** → 원인을 알고 있다면 알려주세요 (루프 재진입)
[3] **케이스 수정** → 시나리오 자체를 조정
[4] **루프 중단** → 현재까지 결과 저장
```

**[1] 선택 시:** 스킵 목록에 추가 → 다음 spec으로 이동. 전체 루프 끝나면 스킵 항목 재시도 제안.

**[2] 선택 시:** 사용자 힌트를 반영해서 Stage 1부터 재시도.

**[3] 선택 시:** 사용자가 시나리오 수정 → Phase 2부터 재생성.

**[4] 선택 시:** 전체 루프 중단 → Phase 4 리포트 출력.

---

## Phase 4: 최종 리포트

```markdown
## E2E Forge Loop 결과

### 요약
| 항목 | 수 |
|------|---|
| 전체 spec | {N} |
| 통과 | {N} |
| 실패 | {N} |
| 스킵 | {N} |

### 상세
| Spec | 시나리오 | 결과 | 시도 | 최종 Stage |
|------|---------|------|------|-----------|
| order-list.spec.ts | 목록 로드 | PASS | 1 | Self-Fix |
| order-list.spec.ts | 검색 필터 | PASS | 4 | Codex |
| order-detail.spec.ts | 상세 로드 | SKIP | 9 | Human |

### 스킵 항목
{스킵된 spec 목록}
→ "스킵된 항목을 다시 시도할까요? [Y/N]"

### Playwright 리포트
`npx playwright show-report` 로 상세 확인
```

---

## 핵심 규칙

| 규칙 | 내용 |
|------|------|
| **Page Object 패턴** | 모든 화면 조작은 PO 클래스를 통해서만 (PageObjectPattern) |
| **선택자 우선순위** | getByRole → getByText → getByTestId → CSS (SelectorPriority) |
| **대기 전략** | 명시적 waitFor 사용, 하드코딩 sleep 금지 (ExplicitWait) |
| **독립 테스트** | 각 test는 독립 실행 가능, 순서 의존 금지 (IndependentTests) |
| **인증 재사용** | storageState로 로그인 상태 재사용 (AuthReuse) |
| **네트워크 격리** | 필요 시 route intercept, 실 API 우선 (NetworkFirst) |

---

## 금지 패턴

| 금지 | 이유 |
|------|------|
| `page.waitForTimeout(N)` | 하드코딩 대기 금지, `waitFor` 사용 |
| `page.locator('.css-1abc23')` | 해시 CSS 클래스 선택자 금지 |
| 테스트 간 데이터 공유 | 독립성 파괴 |
| `test.describe.serial` | 순서 의존 테스트 금지 (특수 사유 제외) |
| Stage 1에서 구현 수정 | Stage 1은 테스트만 수정, 구현 수정은 Stage 3 이후 |
