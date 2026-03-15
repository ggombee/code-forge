# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

{프로젝트명} 웹 애플리케이션 ({모노레포 구조 설명})

## 명령어

```bash
# 개발
yarn dev                 # 개발 서버
# yarn dev:{앱이름}      # 특정 앱 개발 서버

# 빌드
yarn build               # 전체 빌드
# PROFILE=dev yarn build # 환경별 빌드 (dev|stage|release)

# 린트/포맷
yarn lint                # 린트 검사
yarn format              # Prettier 포맷팅

# 테스트
yarn test                # 전체 테스트

# 정리
yarn clean:caches        # 캐시 정리
```

## 구조

```
{project-name}/
├── apps/
│   ├── {app-1}/        # Next.js 14 Pages Router
│   │   ├── pages/      # 라우팅
│   │   └── src/        # 도메인별 소스
│   └── {app-2}/        # Next.js 14 Pages Router
│       ├── pages/
│       └── src/
└── packages/shared/     # 공유 코드
    ├── api/             # API 래퍼
    ├── atoms/           # 전역 상태 (Jotai)
    ├── queries/         # TanStack Query 훅
    ├── services/        # API 서비스 레이어
    ├── components/      # 공유 컴포넌트
    ├── hooks/           # 공유 훅
    ├── types/           # 공유 타입
    └── constants/       # 상수
```

## 경로/별칭

- `@/`는 각 앱의 `src` 기준 (예: `apps/{app-1}/src`)
- `@repo/shared`는 모노레포 공용 패키지

## 아키텍처

### 상태 관리 경계

- **서버 상태**: TanStack Query v5 (`packages/shared/queries/`)
- **전역 UI 상태**: Jotai (`packages/shared/atoms/`)
- **폼 상태**: React Hook Form
- **로컬 UI 상태**: useState/useReducer

### 쿼리/서비스 구조

```
queries/{도메인}/index.ts      # useXxxQuery, useXxxMutation 훅
queries/{도메인}/queryKeys.ts  # 쿼리 키 팩토리
services/{도메인}/index.ts     # API 호출
services/{도메인}/types.ts     # 요청/응답 타입
```

### 레이아웃 시스템

페이지 컴포넌트에 `pageInfo` static 속성으로 레이아웃 지정:

```typescript
Component.pageInfo = { routeKey: RouteKey.PAGE, layout: Layout.DEFAULT };
```

### API 프록시

- `/api/*` → `NEXT_PUBLIC_API_URL`로 프록시

## 주요 규칙

### Import 순서 (ESLint 강제)

1. 외부 라이브러리
2. `@repo/shared`
3. 상대 경로 (`@/` alias)

### 페이지 구조

- `pages/` 파일은 얇게 유지
- 로직은 `src/{도메인}/` 아래에 분리
- 컨테이너/뷰 패턴 사용

### 스타일링

- Emotion (`@emotion/styled`, `css` prop)
- 디자인 시스템 컴포넌트 우선 사용
- 간단한 스타일: 컴포넌트 파일 하단
- 복잡한 스타일: `*.styled.ts` 분리

## 환경

- 환경 파일: `.env.local`, `.env.dev`, `.env.stage`, `.env.release`
- 주요 변수: `NEXT_PUBLIC_ENV`, `NEXT_PUBLIC_API_URL`

## 탐색 팁

- 빠른 코드 검색은 `rg` 사용 (예: `rg "함수명" apps/{앱}/src`)
- 유사 구현은 `apps/{앱}/src` + `packages/shared`를 함께 확인

---

## 상세 규칙

프론트엔드 개발 시 아래 규칙 파일들을 참조:

| 규칙                 | 경로                                                    |
| -------------------- | ------------------------------------------------------- |
| 작업 절차           | `rules/thinking-model.md`                               |
| 코딩 표준            | `rules/coding-standards.md`                             |
| React/Next.js 컨벤션 | `modules/frameworks/react-nextjs-pages/SKILL.md`        |
| 상태 관리 경계       | `modules/state/jotai-tanstack/SKILL.md`                 |
| 스타일링             | `modules/styling/emotion/SKILL.md`                      |
| 유닛 테스트 규칙     | `modules/testing/jest/SKILL.md`                         |

---

## 스킬 & 에이전트

### 스킬

| 이름              | 용도                          |
| ----------------- | ----------------------------- |
| `start`           | 티켓 기반 작업 시작 플로우     |
| `done`            | 작업 완료 → 검증 → 커밋 → PR  |
| `generate-test`   | BDD 테스트 코드 자동 생성      |
| `setup-test`      | 테스트 환경 초기 세팅          |
| `setup`           | 프로젝트 스택 자동 세팅 (profile.json → CLAUDE.md) |
| `debate`          | 교차 모델 토론 (Claude vs Codex) |
| `docs-creator`    | 문서 작성 가이드              |
| `figma-to-code`   | Figma → 코드 변환             |
| `bug-fix`         | 버그 분석 + 2-3가지 옵션 제시 |
| `refactor`        | 리팩토링 + 정책 보호 테스트   |
| `codex`           | Codex 페어 프로그래밍 (opt-in, MCP 필요) |

### 에이전트 - 분석 전용 (READ-ONLY)

| 이름                | 모델   | 차단 도구          | 용도                       |
| ------------------- | ------ | ------------------ | -------------------------- |
| `explore`           | haiku  | Write, Edit        | 코드베이스 탐색            |
| `analyst`           | opus   | Write, Edit, Bash  | 요구사항 분석, 갭 식별     |
| `architect`         | opus   | Write, Edit, Bash  | 아키텍처 분석, 설계 자문   |
| `researcher`        | sonnet | Write, Edit        | 외부 문서/라이브러리 조사  |
| `code-reviewer`     | sonnet | Write, Edit        | 코드 리뷰 (품질+보안, mode: quality/security/both) + memory 학습 |
| `refactor-advisor`  | sonnet | Write, Edit, Bash  | 리팩토링 분석, 개선 전략   |
| `vision`            | sonnet | Write, Edit, Bash  | 미디어 파일 분석, 정보 추출 |

### 에이전트 - 수정 전문 (READ-WRITE)

| 이름                      | 모델   | 용도                          |
| ------------------------- | ------ | ----------------------------- |
| `lint-fixer`              | haiku  | 린트/타입 오류 수정           |
| `build-fixer`             | sonnet | 빌드/컴파일 오류 수정         |
| `testgen`                 | sonnet | 테스트 생성 (mode: generate/tdd) |
| `implementation-executor` | sonnet | 계획 기반 즉시 구현           |
| `deep-executor`           | sonnet | 자율적 심층 구현 + Ralph Loop |

### 에이전트 - Codex 협업 (MCP opt-in)

| 이름    | 모델   | 용도                                     |
| ------- | ------ | ---------------------------------------- |
| `codex` | sonnet | Codex 페어 프로그래밍, MCP/CLI 듀얼 모드 |

> codex-mcp MCP 서버 미설정 시 아무 영향 없음. 완전 opt-in.

### 에이전트 - Git 전용

| 이름           | 모델   | 차단 도구   | 용도                 |
| -------------- | ------ | ----------- | -------------------- |
| `git-operator` | sonnet | Write, Edit | Git 커밋/브랜치 관리 |

---

## 멀티 에이전트

> **Agent Teams 우선** (Claude Max 전용): 3개+ 에이전트 협업 시 TeamCreate → 팀원 spawn → 병렬 협업 → shutdown → TeamDelete
> Agent Teams 미가용 시 Task 병렬 호출로 폴백

병렬 실행 및 모델 선택 가이드:

| 문서                                                     | 용도                   |
| -------------------------------------------------------- | ---------------------- |
| `instructions/multi-agent/coordination-guide.md` | 병렬 실행, 모델 라우팅 |
| `instructions/multi-agent/execution-patterns.md` | 작업별 실행 패턴       |
| `instructions/multi-agent/agent-roster.md`       | 에이전트 목록          |

---

## Figma MCP 사용 규칙

Figma 작업 시 **figma MCP를 항상 우선 사용**한다.

### 강제 사용 규칙

- Figma 관련 정보(레이아웃/스타일/컴포넌트/텍스트/노드구조)가 필요하면 **추측하지 말고 반드시 MCP 호출**
- PAT(Personal Access Token) 방식이므로 OAuth 재인증 시도하지 않음
- 호출 에러 시: `/mcp` 슬래시 커맨드로 재연결 안내
- Figma URL이 주어지면 fileKey/nodeId 먼저 추출 후 MCP 호출

### URL에서 키 추출

```
https://www.figma.com/design/{fileKey}/{fileName}?node-id={nodeId}
→ nodeId의 하이픈(-)을 콜론(:)으로 변환
예: node-id=2040-47609 → nodeId: "2040:47609"
```

### MCP 호출 우선순위

| 순위 | 도구                 | 용도                      |
| ---- | -------------------- | ------------------------- |
| 1    | `get_metadata`       | 구조/스타일/컴포넌트 파악 |
| 2    | `get_screenshot`     | 시각적 디자인 확인        |
| 3    | `get_design_context` | 코드 변환 시              |

### 출력 규칙

- MCP 결과를 받은 **후에만** 분석/요약/가이드 작성
- MCP 호출 전에는 "무엇을 확인하기 위해 어떤 호출을 할지"만 말함