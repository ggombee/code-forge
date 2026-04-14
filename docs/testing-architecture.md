# 테스트 아키텍처 설계 (Policy-Driven Testing)

> 언어/프레임워크 무관한 범용 설계. 프론트엔드(React, Vue)부터 백엔드(Spring, NestJS, Go)까지.
> 광고센터에서 검증 후 다른 프로젝트로 확장 가능한 구조.
> code-forge 플러그인과 프로젝트 내 인프라의 역할을 명확히 분리.

## 변경 이력

| ver | date | description |
|-----|------|-------------|
| 1.0 | 2026-04-07 | 초기 설계 |

---

## 1. 테스트 카테고리

| 카테고리 | 무엇을 검증하나 | 예시 | 도구 | 실행 시점 |
|---------|--------------|------|------|----------|
| **유틸** | 순수 함수의 입출력 | 날짜 파싱, 할인 계산, enum 매핑 | Jest | 수정 즉시 |
| **훅/로직** | 상태 관리 + API 분기 | useCTA notificationSent 분기 | Jest + mock | 수정 즉시 |
| **UI/디자인** | 색상, 폰트, 간격, 레이아웃 | 광고중 컬러 = supportOngoing | Playwright 스냅샷 + 정적 검증 | 배포 전 |
| **플로우** | 사용자 시나리오 흐름 | 결제방법 설정 → 알림톡 발송 → 토스트 | Playwright E2E | 배포 전 |
| **통합** | 페이지 전체 렌더링 + API | 주문 목록 로드 → 필터 → 상세 이동 | Playwright E2E | 배포 전 |
| **런타임 에러** | 빌드에서 못 잡는 에러 | mixpanel init 전 track 호출 | try/catch 방어 + E2E 콘솔 에러 감지 | 수정 즉시 + 배포 전 |

---

## 2. 현재 상태 → 목표 상태

### 현재 (v1)

```
프로젝트 (ad-center)              code-forge 플러그인
├── .policy/ (정책 매트릭스)        ├── /generate-test (무거움)
├── scripts/ (policy-check)        ├── /e2e (무거움)
├── src/**/__tests__/ (유닛)       ├── /quality (lint+tsc)
├── e2e/ (E2E spec)                └── /setup-test, /setup-e2e
├── jest.config.cjs
└── playwright.config.ts
```

**문제점:**
- 카테고리 구분 없이 뒤섞임
- 디자인 TC 없음 (test:qa:design 패턴은 있지만 실제 TC 0개)
- E2E 콘솔 에러 감지 없음
- code-forge 스킬이 프로젝트 구조를 모름 (.policy/ 활용 안 함)

### 목표 (v2)

```
프로젝트 (ad-center)                  code-forge 플러그인
├── .policy/                          ├── /generate-test
│   ├── {page}.json (정책 매트릭스)    │     → .policy/ 참조하여 TC 생성
│   ├── design-config.json (디자인)    ├── /e2e
│   └── policy-schema.json            │     → .policy/ 참조하여 시나리오 도출
├── scripts/                          ├── /quality
│   ├── policy-check.sh               │     → lint + tsc + 관련 TC 실행
│   └── policy-check.py               └── /policy-sync (신규 예정)
├── src/**/__tests__/                       → 정책 MD ↔ JSON 동기화 검증
│   ├── {유틸}.test.ts
│   ├── {훅}.test.tsx
│   └── design/{컴포넌트}.design.test.ts  ← 신규
├── e2e/
│   ├── {page}.spec.ts (플로우)
│   ├── {page}.design.spec.ts (디자인)  ← 신규
│   └── {page}.error.spec.ts (런타임)  ← 신규
└── test:qa:{카테고리} (스크립트)
```

---

## 3. 카테고리별 TC 전략

### 3-1. 유틸 (Jest)

```
위치: src/{도메인}/utils/__tests__/{파일명}.test.ts
예시: discountValidation.test.ts, periodHelpers.test.ts
생성: /generate-test 또는 수동
실행: yarn test:qa:unit
```

**원칙:** 순수 함수만. mock 없이 입력→출력 검증.

### 3-2. 훅/로직 (Jest + mock)

```
위치: src/{도메인}/hooks/__tests__/{훅명}.test.tsx
예시: useCTA.test.tsx
생성: /generate-test --policy (정책 기반 시나리오 자동 도출)
실행: yarn test:qa:flow
```

**원칙:** API mock으로 분기 로직 검증. 정책 매트릭스의 `branches`와 1:1 매핑.

### 3-3. UI/디자인 (Jest + Playwright)

**레벨 A: 정적 토큰 검증 (Jest)**

```
위치: src/{도메인}/__tests__/design/{컴포넌트}.design.test.ts
방식: 소스 코드에서 semanticColor/typography 사용을 정적 분석
예시: Table 컴포넌트가 AD_STATUS_COLORS.progress = supportOngoing 사용하는지
실행: yarn test:qa:design
```

```typescript
// 예시: order-list.design.test.ts
describe('주문 목록 테이블 디자인 규칙', () => {
  it('광고중 컬러는 supportOngoing', () => {
    // 소스 파일에서 AD_STATUS_COLORS.progress 값 확인
    expect(AD_STATUS_COLORS.progress).toBe(semanticColor.supportOngoing);
  });

  it('태그 크기는 lg', () => {
    // 렌더링 결과에서 태그 크기 확인 (선택적)
  });
});
```

**레벨 B: 스크린샷 비교 (Playwright)**

```
위치: e2e/{page}.design.spec.ts
방식: 이전 스크린샷과 픽셀 비교 (toHaveScreenshot)
오차: design-config.json의 threshold 적용
실행: yarn test:qa:design:visual
```

```typescript
// 예시: order-list.design.spec.ts
test('주문 목록 테이블 스냅샷', async ({ page }) => {
  await page.goto('/orders');
  await expect(page.locator('table')).toHaveScreenshot('order-list-table.png', {
    maxDiffPixelRatio: 0.01, // 1% 허용
  });
});
```

**레벨 C: Figma 비교 (수동/스킬)**

```
방식: /figma-to-code 스킬로 Figma 스크린샷 ↔ 실제 스크린샷 비교
시점: 디자인 QA 시에만 수동 실행
```

### 3-4. 플로우 (Playwright E2E)

```
위치: e2e/{page}.spec.ts
방식: 사용자 시나리오 재현 (클릭 → API 모킹 → 결과 확인)
예시: 결제 알림톡 발송 → notificationSent 분기 → 토스트/모달
실행: yarn test:e2e
```

### 3-5. 런타임 에러 (Playwright 콘솔 감지)

```
위치: e2e/{page}.error.spec.ts
방식: 페이지 로드 후 console.error 감지
예시: mixpanel init 전 track 호출 → TypeError 감지
실행: yarn test:qa:runtime
```

```typescript
// 예시: order-list.error.spec.ts
test('주문 목록 페이지 콘솔 에러 없음', async ({ page }) => {
  const errors: string[] = [];
  page.on('pageerror', (error) => errors.push(error.message));

  await page.goto('/orders');
  await page.waitForLoadState('networkidle');

  expect(errors).toEqual([]);
});
```

---

## 4. 실행 시점 매트릭스

| 시점 | 유틸 | 훅/로직 | 디자인(정적) | 디자인(시각) | 플로우 | 런타임 |
|------|------|---------|------------|------------|--------|--------|
| **PostEdit 훅** (자동) | ✅ | ✅ | - | - | - | - |
| **커밋 전** (수동) | ✅ | ✅ | ✅ | - | - | - |
| **배포 전** (yarn test:qa) | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **디자인 QA** (수동) | - | - | ✅ | ✅ | - | - |
| **전체 회귀** (정기) | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |

---

## 5. yarn 스크립트 체계

```json
{
  "test": "jest --config jest.config.cjs",
  "test:qa": "전체 (유닛 + E2E)",
  "test:qa:unit": "유닛 전체 (유틸 + 훅)",
  "test:qa:flow": "훅/로직 TC (useCTA 등)",
  "test:qa:design": "디자인 정적 검증",
  "test:qa:design:visual": "디자인 스냅샷 비교",
  "test:qa:runtime": "런타임 에러 감지",
  "test:e2e": "E2E 플로우 전체",
  "test:e2e:ui": "E2E UI 모드 (브라우저 표시)",
  "test:policy": "정책 매트릭스 전체 검증"
}
```

---

## 6. code-forge 플러그인 연동

### 현재 스킬 → 개선 방향

| 스킬 | 현재 | 개선 |
|------|------|------|
| `/generate-test` | 소스 코드 분석 → BDD → TC 생성 | `.policy/` 참조하여 정책 기반 시나리오 자동 도출 |
| `/e2e` | 페이지 분석 → spec 생성 | `.policy/` flows 기반으로 플로우 시나리오 도출 |
| `/quality` | lint + tsc | + 관련 TC 실행 (policy-check.sh 연동) |
| `/start` | 코드 분석 + 구현 | 구현 완료 후 "관련 TC 실행 권장" 안내 |

### 신규 스킬 (예정)

| 스킬 | 역할 |
|------|------|
| `/policy-sync` | 정책 MD ↔ JSON 동기화 검증. MD 변경 시 JSON 업데이트 필요 안내 |
| `/design-qa` | Figma ↔ 스크린샷 비교. 차이 영역 감지 + DOM 요소 특정 + uiRules 대조 |

### 플러그인에 두는 것 vs 프로젝트에 두는 것

| 구분 | 플러그인 (code-forge) | 프로젝트 (ad-center) |
|------|---------------------|---------------------|
| **역할** | TC를 **생성/분석/실행**하는 도구 | TC **코드 자체** + 정책 + 설정 |
| **예시** | /generate-test, /e2e, /design-qa | .policy/, __tests__/, e2e/, scripts/ |
| **이식성** | 어떤 프로젝트든 사용 가능 | 프로젝트별로 다름 |
| **변경 빈도** | 드물게 (도구 개선 시) | 자주 (기능 변경마다) |

---

## 7. 다른 프로젝트 이식 가이드

### 공통 파일 (그대로 복사)

```
.policy/
  ├── policy-schema.json      ← 정책 매트릭스 스키마
  ├── config-schema.json      ← 프로젝트 설정 스키마
scripts/
  ├── policy-check.sh         ← 매칭 + TC 실행 셸 스크립트
  └── policy-check.py         ← 매칭 로직 (언어 무관)
```

### 프로젝트별 작성

```
.policy/
  ├── config.json             ← 테스트 러너 설정 (stack별 명령어)
  └── {모듈}.json             ← 정책 매트릭스 (affectedFiles, flows, testFiles)
.claude/docs/{모듈}.md        ← 정책 문서
테스트 파일                    ← 프로젝트 컨벤션에 따라
```

### 스택별 config.json 예시

**Next.js (프론트엔드)**
```json
{ "stack": "nextjs", "testRunner": { "unit": { "command": "yarn test", "runSingle": "yarn test -- --testPathPattern=\"{basename}\"" }, "e2e": { "command": "npx playwright test", "runSingle": "npx playwright test {file}" } } }
```

**Spring Boot (백엔드)**
```json
{ "stack": "spring-boot", "testRunner": { "unit": { "command": "mvn test", "runSingle": "mvn test -Dtest={basename}" }, "integration": { "command": "mvn verify -Pintegration", "runSingle": "mvn verify -Dtest={basename}" } } }
```

**Go (백엔드)**
```json
{ "stack": "go-fiber", "testRunner": { "unit": { "command": "go test ./...", "runSingle": "go test -run {basename} ./..." } } }
```

**NestJS (백엔드)**
```json
{ "stack": "nestjs", "testRunner": { "unit": { "command": "yarn test", "runSingle": "yarn test -- --testPathPattern={basename}" }, "e2e": { "command": "yarn test:e2e", "runSingle": "yarn test:e2e -- --testPathPattern={basename}" } } }
```

### code-forge 스킬 연동 (공통)

```
/generate-test    → .policy/ 있으면 정책 기반 시나리오 자동 도출
/e2e              → .policy/ 있으면 flows 기반 시나리오 도출
/quality          → policy-check.sh 있으면 관련 TC 실행 연동
/start            → 구현 완료 시 "관련 TC 실행 권장" 안내
```

---

## 8. 우선순위 로드맵

| 순서 | 작업 | 효과 | 난이도 |
|------|------|------|--------|
| ✅ 완료 | 유틸/훅 유닛 TC (150개) | 로직 분기 검증 | - |
| ✅ 완료 | 정책 매트릭스 + PostEdit 훅 | 수정 시 자동 경고 | - |
| ✅ 완료 | E2E scaffolding (3개 페이지) | 플로우 기본 검증 | - |
| 1 | 런타임 에러 감지 spec 추가 | console.error 사전 차단 | LOW |
| 2 | 디자인 정적 검증 TC | 색상/폰트 실수 방지 | LOW |
| 3 | 스크린샷 스냅샷 기준선 | 레이아웃 변경 감지 | MED |
| 4 | /generate-test .policy/ 연동 | TC 자동 도출 고도화 | MED |
| 5 | /design-qa 스킬 신설 | Figma 비교 자동화 | HIGH |
