---
name: setup-e2e
description: 프로젝트에 Playwright E2E 테스트 환경을 세팅합니다. 프로젝트 구조 감지 → 패키지 설치 → 설정 파일 → 디렉토리 구조 → 샘플 테스트 검증.
---

# /setup-e2e

E2E 테스트 환경이 없는 프로젝트에 Playwright 기반 초기 세팅을 수행합니다.

설계 문서: `@../../docs/e2e-forge-loop-design.md`

## 사용법

```
/setup-e2e              # 자동 감지
/setup-e2e --baseUrl http://localhost:3000
```

---

## Step 1: 프로젝트 분석

다음을 자동 감지합니다:

### 1-1. 기존 E2E 환경 확인

```bash
# Playwright 설치 여부
ls node_modules/@playwright 2>/dev/null
cat package.json | grep playwright

# 기존 E2E 디렉토리
ls e2e/ 2>/dev/null || ls tests/ 2>/dev/null || ls __e2e__/ 2>/dev/null

# 기존 설정 파일
ls playwright.config.* 2>/dev/null
```

이미 Playwright가 설정된 경우 → "기존 E2E 환경이 감지됐습니다. 보완만 진행할까요?" 확인.

### 1-2. 프레임워크 & 서버 감지

| 감지 대상 | 방법 |
|----------|------|
| Next.js | `next.config.*` → `baseURL: http://localhost:3000` |
| Vite | `vite.config.*` → `baseURL: http://localhost:5173` |
| CRA | `react-scripts` → `baseURL: http://localhost:3000` |
| 커스텀 | package.json scripts에서 dev/start 포트 추출 |

### 1-3. 앱 구조 감지 (모노레포)

```bash
ls apps/ 2>/dev/null
```

모노레포인 경우 → "어떤 앱의 E2E를 세팅할까요?" 선택 요청.

### 1-4. 분석 결과 보고

```markdown
프로젝트 분석 결과:
- 프레임워크: Next.js 13 (Pages Router)
- 개발 서버: http://localhost:3000
- 기존 E2E: 없음
- 패키지 매니저: yarn

세팅할 항목:
1. @playwright/test 패키지 설치
2. playwright.config.ts 생성
3. e2e/ 디렉토리 구조 생성
4. 공통 fixtures (인증, 데이터) 생성
5. Page Object 베이스 클래스 생성
6. package.json에 test:e2e 스크립트 추가
7. .gitignore에 playwright 관련 항목 추가

진행할까요?
```

---

## Step 2: 패키지 설치

```bash
# 패키지 매니저 자동 감지
# yarn.lock → yarn, package-lock.json → npm, pnpm-lock.yaml → pnpm

{pm} add -D @playwright/test

# 브라우저 설치
npx playwright install chromium
```

> Firefox/WebKit은 기본 설치하지 않음 (Chromium만). 필요 시 사용자 요청으로 추가.

---

## Step 3: playwright.config.ts 생성

프레임워크에 맞게 생성:

```typescript
import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: [['html', { open: 'never' }]],

  use: {
    baseURL: '{감지된 baseURL}',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
  },

  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
  ],

  // 개발 서버 자동 시작 (감지된 dev 명령어)
  webServer: {
    command: '{감지된 dev 명령어}',
    url: '{감지된 baseURL}',
    reuseExistingServer: !process.env.CI,
    timeout: 120_000,
  },
});
```

---

## Step 4: 디렉토리 구조 생성

```
e2e/
├── fixtures/
│   ├── auth.fixture.ts       # 인증 상태 fixture
│   └── test-data.fixture.ts  # 테스트 데이터 fixture
├── pages/
│   └── base.page.ts          # Page Object 베이스 클래스
├── utils/
│   └── helpers.ts            # 공통 헬퍼 (waitForApi 등)
└── sample.spec.ts            # 환경 검증용 샘플 테스트
```

### fixtures/auth.fixture.ts

```typescript
import { test as base } from '@playwright/test';

type AuthFixtures = {
  authenticatedPage: Page;
};

export const test = base.extend<AuthFixtures>({
  authenticatedPage: async ({ page }, use) => {
    // 프로젝트 인증 방식에 맞게 수정 필요
    // 예: 로그인 페이지 → 토큰 저장 → 재사용
    await use(page);
  },
});
```

### pages/base.page.ts

```typescript
import { Page, Locator } from '@playwright/test';

export abstract class BasePage {
  constructor(protected readonly page: Page) {}

  async navigate(path: string) {
    await this.page.goto(path);
  }

  async waitForPageLoad() {
    await this.page.waitForLoadState('networkidle');
  }
}
```

---

## Step 5: 샘플 테스트 생성

```typescript
// e2e/sample.spec.ts
import { test, expect } from '@playwright/test';

test('메인 페이지가 정상 로드된다', async ({ page }) => {
  await page.goto('/');
  await expect(page).toHaveTitle(/.+/);
});
```

---

## Step 6: package.json 스크립트 추가

```json
{
  "scripts": {
    "test:e2e": "playwright test",
    "test:e2e:ui": "playwright test --ui",
    "test:e2e:report": "playwright show-report"
  }
}
```

---

## Step 7: .gitignore 추가

```
# Playwright
/test-results/
/playwright-report/
/blob-report/
/playwright/.cache/
```

---

## Step 8: 환경 검증

```bash
# 샘플 테스트 실행
npx playwright test e2e/sample.spec.ts
```

성공 시:
```markdown
## E2E 환경 세팅 완료

- Playwright: @playwright/test 설치됨
- 브라우저: Chromium
- 설정: playwright.config.ts
- 테스트 디렉토리: e2e/
- 샘플 테스트: PASS

다음 단계: `/e2e {페이지경로}` 로 E2E 테스트를 생성하세요.
```

실패 시:
- 에러 분석 → 자동 수정 (최대 3회)
- 서버 미기동: "개발 서버를 먼저 실행해주세요: `{dev 명령어}`"
- 포트 충돌: 다른 포트로 재설정 제안

---

## 주의사항

- 기존 E2E 환경이 있으면 덮어쓰지 않고 누락분만 보완
- Cypress 등 다른 E2E 도구가 있으면 "Playwright로 전환할까요, 병행할까요?" 확인
- CI 환경 설정은 이 스킬에서 다루지 않음 (향후 확장)
