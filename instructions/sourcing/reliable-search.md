# Reliable Search Guide

**목적**: 검색 결과의 최신성과 신뢰성 보장, 중복 검색 방지 및 효율적 검색 전략

---

## 중복 검색 방지

| 규칙 | 실행 |
|------|------|
| **같은 쿼리 금지** | 동일 쿼리 반복 실행 금지 (WebSearch + SearXNG 같은 쿼리 금지) |
| **이전 결과 확인** | 검색 전 이전 검색 결과 확인 |
| **유사 쿼리 병합** | 유사한 쿼리는 한 번에 실행 |
| **검색 종료 조건** | 목표 정보 획득, 교차 검증 완료, 검색 깊이 도달 |

### 허용/금지 패턴

```typescript
// ❌ 금지: 같은 쿼리 반복
WebSearch({ query: "React best practices 2026" })
WebSearch({ query: "React best practices 2026" })  // 중복!

// ❌ 금지: 다른 채널에 같은 쿼리
WebSearch({ query: "Next.js 15 features" })
SearXNG({ query: "Next.js 15 features" })  // 중복!

// ✅ 올바름: 다른 각도 쿼리
WebSearch({ query: "React best practices 2026" })
WebSearch({ query: "React performance optimization 2026" })

// ✅ 올바름: 채널별 특화 쿼리
WebSearch({ query: "Next.js 15 features overview" })
SearXNG({ query: "Next.js 15 breaking changes" })
```

---

## 검색 결과 캐싱

장기 세션 시 검색 결과를 파일로 저장:

```
.claude/research/[topic]/
├── sources.md    # URL + 발행일 + 요약
├── findings.md   # 핵심 발견사항
└── queries.md    # 실행한 쿼리 목록 (중복 방지)
```

---

## 검색 범위 사전 결정

| 깊이 | 쿼리 수 | 용도 |
|------|---------|------|
| **Quick** | 1-3개 | 개요 파악, 빠른 확인 |
| **Medium** | 4-6개 | 표준 조사, 비교 분석 |
| **Deep** | 7-10개 | 완전 분석, 심층 연구 |

### 우선순위 채널

```
1순위: Context7 (라이브러리 공식 문서)
2순위: GitHub (코드, 이슈, 릴리스)
3순위: WebSearch/SearXNG (웹 검색)
```

### 종료 조건

| 조건 | 기준 |
|------|------|
| 목표 정보 획득 | 필요한 정보 모두 확보 |
| 교차 검증 완료 | 핵심 주장 2+ 소스 확인 |
| 검색 깊이 도달 | Quick(3) / Medium(6) / Deep(10) |
| 중복 결과 반복 | 새로운 정보 없음 (3회 연속) |

---

## 날짜 인식 검색

| 규칙 | 실행 |
|------|------|
| **연도 포함** | 모든 검색 쿼리에 현재 연도 포함 |
| **기간 필터** | SearXNG: `time_range=year` |
| **한국어** | "2026년 기준", "최신" 키워드 |
| **영어** | "2025-2026", "latest", "current" 키워드 |

---

## 출처 신뢰도 등급

| 등급 | 소스 유형 | 예시 |
|------|----------|------|
| **S** | 공식 문서, 논문, 1차 데이터 | docs.prisma.io, arxiv.org |
| **A** | 공식 블로그, 주요 기술 미디어 | engineering.fb.com, infoq.com |
| **B** | 개인 기술 블로그, 커뮤니티 | dev.to, medium.com, reddit.com |
| **C** | AI 생성 의심, 오래된 문서 | 날짜 없는 블로그, SEO 스팸 |

### 검증 규칙

| 체크 | 기준 | 처리 |
|------|------|------|
| 날짜 확인 | 발행일 12개월 이내 | 초과 시 "⚠ 오래된 자료" |
| 저자 확인 | 실명/소속 확인 가능 | 익명 → 등급 1단계 하향 |
| 교차 검증 | 핵심 주장 2+ 소스 | 단일 소스 → "미검증" |
| 이해충돌 | 벤더 자사 제품 주장 | "벤더 출처" 명시 |

---

## Smart Tier Fallback

```
Tier 1 (MCP, ToolSearch로 감지):
  SearXNG MCP  → 메타검색 (246+ 엔진)
  Firecrawl MCP → 페이지→MD 변환
  GitHub MCP   → 코드/리포/이슈 검색
  Context7 MCP → 라이브러리 문서 즉시 조회

Tier 2 (내장, 항상 가용):
  WebSearch → 웹 검색 (연도 키워드 필수)
  WebFetch  → 페이지 직접 읽기
  Jina Reader → WebFetch('https://r.jina.ai/{URL}') 클린 MD 변환

Tier 3: Playwright → SPA/JS 렌더링 필요 시 (crawler skill)
```

**MCP는 main agent가 직접 실행** (subagent는 MCP 도구 사용 불가)

---

## Jina Reader (`r.jina.ai`)

URL → 클린 마크다운 변환 (JS 렌더링 지원, 광고/네비 제거)

```typescript
// 기본: URL을 클린 마크다운으로
WebFetch('https://r.jina.ai/https://react.dev/reference/react/use', '핵심 API 추출')

// WebFetch 실패 시 Jina 폴백
WebFetch('https://r.jina.ai/https://docs.example.com/guide', '가이드 내용 추출')
```

### 폴백 체인 (페이지 읽기)

```
Firecrawl scrape → Jina Reader → WebFetch (직접) → Playwright (최후 수단)
```

---

## 수집 후 검증

| 단계 | 검증 |
|------|------|
| 날짜 체크 | 핵심 소스 발행일 확인, 12개월 초과 시 표기 |
| 등급 분류 | 각 소스에 S/A/B/C 등급 부여 |
| 교차 검증 | 핵심 주장 2+ 소스 확인 |
| 편향 체크 | 벤더/광고 소스 식별, 독립 소스 보완 |

### researcher 에이전트 프롬프트 필수 포함

```
"검색 시 현재 연도 포함, 12개월 이내 자료 우선.
 각 출처: URL + 발행일 + 소스 유형.
 핵심 주장 2+ 소스 교차 검증.
 중복 검색 방지: 이전 쿼리 확인, 같은 쿼리 재실행 금지."
```
