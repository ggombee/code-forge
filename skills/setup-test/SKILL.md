---
name: setup-test
description: 프론트엔드 프로젝트에 테스트 환경을 초기 세팅합니다. 프로젝트 구조를 자동 감지하여 jest/vitest 설정, customRender, MSW 등을 구성합니다.
---

# /setup-test

테스트 환경이 없는 프로젝트에 초기 세팅을 수행합니다.

## 실행 워크플로우

### Step 1: 프로젝트 분석

다음을 자동 감지합니다:

1. **프레임워크 감지:**
   - `next.config.*` -> Next.js
   - `vite.config.*` -> Vite
   - `react-scripts` in package.json -> CRA
   - 기타 -> 일반 React

2. **기존 테스트 환경 확인:**
   - `jest.config.*` / `vitest.config.*` 존재 여부
   - package.json에 test 스크립트 존재 여부
   - `@testing-library/react` 설치 여부
   - MSW 설치 여부

3. **상태 관리 / Provider 구조 분석:**
   - `_app.tsx` / `_app.js` 읽기 -> Provider 트리 파악
   - `Provider/` 디렉토리 탐색
   - package.json에서 jotai, recoil, zustand, react-query 등 확인

4. **사용자에게 분석 결과 보고 후 진행 여부 확인:**

   ```
   프로젝트 분석 결과:
   - 프레임워크: Next.js 13 (Pages Router)
   - 테스트 러너: 미설정 -> jest 권장
   - 상태 관리: jotai, react-query
   - Provider: QueryClientProvider, JotaiProvider

   다음 항목을 세팅하겠습니다:
   1. jest + @testing-library/react + MSW 패키지 설치
   2. jest.config.js 생성
   3. jest.setup.js 생성
   4. customRender 유틸리티 생성
   5. MSW 핸들러 구조 생성
   6. package.json test 스크립트 추가

   진행할까요?
   ```

### Step 2: 패키지 설치

**jest 기반 (Next.js, CRA):**

```bash
yarn add -D jest @testing-library/react @testing-library/jest-dom @testing-library/user-event jest-environment-jsdom @types/jest msw identity-obj-proxy
```

Next.js 프로젝트 추가:

```bash
yarn add -D jest-next-dynamic
```

**vitest 기반 (Vite):**

```bash
yarn add -D vitest @testing-library/react @testing-library/jest-dom @testing-library/user-event jsdom @types/jest msw
```

### Step 3: 설정 파일 생성

**jest.config.js** (Next.js 예시):

- moduleNameMapper: path alias (@/, @shared/ 등) 매핑
- testEnvironment: jsdom
- setupFilesAfterSetup: jest.setup.js
- transformIgnorePatterns: node_modules 중 ESM 모듈 처리
- moduleFileExtensions: js, jsx, ts, tsx

**jest.setup.js:**

- `@testing-library/jest-dom` import
- 전역 mock 설정 (next/router, next/dynamic, SVG, CSS 등)
- MSW server setup/teardown
- window.matchMedia mock

### Step 4: customRender 생성

`__tests__/utils/customRender.tsx` (또는 `src/test/customRender.tsx`):

프로젝트의 Provider 구조를 분석하여 생성합니다:

- QueryClientProvider (react-query 사용 시)
- RecoilRoot (recoil 사용 시)
- JotaiProvider (jotai 사용 시, 필요한 경우)
- FormProvider (react-hook-form 사용 시)
- 기타 프로젝트 커스텀 Provider

### Step 5: MSW 핸들러 구조 생성

```
src/mocks/
├── server.ts          # MSW setupServer
├── handlers/
│   └── index.ts       # 핸들러 모음
└── browser.ts         # (선택) 브라우저용 setupWorker
```

### Step 6: package.json 스크립트 추가

```json
{
  "scripts": {
    "test": "jest --watchAll",
    "test:ci": "jest --ci --coverage"
  }
}
```

### Step 7: 검증

간단한 샘플 테스트를 실행하여 환경이 올바르게 구성되었는지 확인합니다:

```bash
yarn test --watchAll=false
```

## 주의사항

- 이미 테스트 환경이 구성된 프로젝트에서는 기존 설정을 덮어쓰지 않고, 누락된 부분만 보완합니다.
- path alias 매핑은 프로젝트의 tsconfig.json / jsconfig.json을 참고하여 생성합니다.
- 패키지 매니저는 프로젝트의 lock 파일을 확인하여 자동 결정합니다 (yarn.lock -> yarn, package-lock.json -> npm, pnpm-lock.yaml -> pnpm).
