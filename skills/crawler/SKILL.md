---
name: crawler
description: Playwright로 웹사이트를 직접 탐색하여 크롤링 흐름 설계. API/네트워크 분석, 문서화, 크롤러 코드 생성.
category: utility
user-invocable: false
---

# Crawler Skill

> Playwright exploration → API/Network analysis → Documentation → Code generation

**Templates:** [document-templates.md](rules/document-templates.md) · [code-templates.md](rules/code-templates.md)
**Checklists:** [pre-crawl-checklist.md](rules/pre-crawl-checklist.md) · [anti-bot-checklist.md](rules/anti-bot-checklist.md)
**References:** [playwriter-commands.md](rules/playwriter-commands.md) · [crawling-patterns.md](rules/crawling-patterns.md) · [selector-strategies.md](rules/selector-strategies.md) · [network-crawling.md](rules/network-crawling.md)

---

<trigger_conditions>

| 트리거 | 액션 |
|--------|------|
| Crawling, scraping, crawl, scrape | 즉시 실행 |
| 웹사이트 데이터 추출 | 즉시 실행 |
| API 리버스 엔지니어링 | API 인터셉션 시작 |
| Anti-bot 우회 요청 | Anti-Detect 가이드 확인 |

</trigger_conditions>

---

## 워크플로우

| Phase | 작업 | 명령/방법 |
|-------|------|----------|
| **1. Session** | 세션 생성 + 페이지 열기 | `playwriter session new` |
| **2. Explore** | 구조 파악 | `accessibilitySnapshot`, `screenshotWithAccessibilityLabels` |
| **3. Analyze** | API 인터셉트, 셀렉터 추출 | `page.on('response')`, `getLocatorStringForElement` |
| **4. Document** | `.forge/crawler/[site]/`에 저장 | Write |
| **5. Code** | 크롤러 코드 생성 | [code-templates.md](rules/code-templates.md) |

---

## Quick Commands

```bash
# 세션 생성 + 페이지 열기
playwriter session new
playwriter -s 1 -e "state.page = await context.newPage(); await state.page.goto('https://target.com')"

# 구조 파악
playwriter -s 1 -e "console.log(await accessibilitySnapshot({ page: state.page }))"

# API 응답 인터셉트
playwriter -s 1 -e $'
state.responses = [];
state.page.on("response", async res => {
  if (res.url().includes("/api/")) {
    try { state.responses.push({ url: res.url(), body: await res.json() }); } catch {}
  }
});
'

# 인증 자료 추출
playwriter -s 1 -e "console.log(JSON.stringify(await context.cookies(), null, 2))"
playwriter -s 1 -e "console.log(await state.page.evaluate(() => localStorage.getItem('token')))"

# 셀렉터 변환
playwriter -s 1 -e "console.log(await getLocatorStringForElement(state.page.locator('aria-ref=e14')))"
```

---

## 방법 선택

| 조건 | 방법 | 비고 |
|------|------|------|
| API 발견 + 단순 인증 | **fetch** | 가장 빠름 |
| API + 쿠키/토큰 필요 | **fetch + Cookie** | 만료 처리 필요 |
| 강한 봇 탐지 | **Nstbrowser** | Anti-Detect |
| API 없음 (SSR) | **Playwright DOM** | 직접 파싱 |

---

## 출력 구조

```
.forge/crawler/[site-name]/
├── ANALYSIS.md      # 사이트 구조
├── SELECTORS.md     # DOM 셀렉터
├── API.md           # API 엔드포인트
├── NETWORK.md       # 인증/네트워크 세부사항
└── CRAWLER.ts       # 생성된 크롤러 코드
```

---

## 검증

```text
✅ Playwright 세션 생성
✅ accessibilitySnapshot으로 구조 분석
✅ API 인터셉션 시도
✅ 셀렉터 추출 검증
✅ .forge/crawler/에 문서화
✅ 크롤러 코드 생성
```

---

## 금지 사항

| 카테고리 | 금지 |
|----------|------|
| 분석 | 구조 분석 없이 셀렉터 추측 |
| 접근 | API 확인 없이 DOM 전용 |
| 문서화 | 분석 결과 문서화 생략 |
| 네트워크 | Rate limiting 무시 |
