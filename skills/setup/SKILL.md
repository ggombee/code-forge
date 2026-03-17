---
name: setup
description: profile.json을 읽어 CLAUDE.md를 자동 생성한다. 프로젝트 스택에 맞는 모듈을 조합하여 Claude Code 환경을 세팅한다.
---

# /setup 스킬

프로젝트의 `.claude/profile.json`을 읽어 스택에 맞는 CLAUDE.md를 자동 생성한다.

---

## 동작 흐름

```
1. .claude/profile.json 읽기 (없으면 대화형 스택 선택 → 생성)
2. preset 있으면 → ${CLAUDE_PLUGIN_ROOT}/presets/{name}.json 로드
3. preset의 modules를 기본값으로 세팅
4. profile.json의 modules 명시값으로 오버라이드
5. overrides 병합 (있으면)
6. CLAUDE.md 생성 (50줄 이내, 프로젝트 정보 + 빌드/린트 명령어 + 모듈 참조)
7. 결과 요약 출력
```

---

## ARGUMENT 처리

```
$ARGUMENTS 없음 → .claude/profile.json 자동 탐색

$ARGUMENTS 있음 → 파일 경로로 인식
예: /setup .claude/profile.json
```

---

## Step 1: profile.json 읽기

`.claude/profile.json`이 존재하는지 확인한다.

### 파일이 없는 경우 — 대화형 스택 선택

```
profile.json이 없습니다. 프로젝트 스택을 선택해 주세요.

1. Framework
   a. react-nextjs-pages (Next.js Pages Router)
   b. react-nextjs-app (Next.js App Router)
   c. react-spa (React SPA)

2. Design System
   a. mui (Material UI)
   b. ant-design (Ant Design)
   c. none

3. State Management
   a. jotai-tanstack (Jotai + TanStack Query)
   b. zustand-tanstack (Zustand + TanStack Query)
   c. redux-rtk (Redux RTK)

4. Styling
   a. emotion (@emotion/styled)
   b. tailwind (Tailwind CSS)
   c. styled-components

5. Testing
   a. jest (Jest)
   b. vitest (Vitest)

또는 프리셋 사용:
   p1. standard (Pages Router + Jotai + Emotion + Jest)

선택 후 .claude/profile.json 생성 및 CLAUDE.md 생성으로 진행합니다.
```

### 파일이 있는 경우 — 파싱

```jsonc
// .claude/profile.json 예시
{
  "preset": "standard",   // 프리셋 사용 (선택)
  "modules": {                    // 개별 모듈 직접 선택 (선택)
    "framework": "react-nextjs-pages",
    "state": "jotai-tanstack",
    "styling": "emotion",
    "testing": "jest",
    "advanced": ["codex", "figma"] // opt-in 모듈
  },
  "project": {                    // 프로젝트 기본 정보 (선택)
    "name": "광고센터",
    "dev": "yarn dev:ad-web",
    "build": "yarn build",
    "lint": "yarn lint",
    "test": "yarn test"
  },
  "overrides": {}                 // 앱별 오버라이드 (선택)
}
```

---

## Step 2: 모듈 해석

### 프리셋 우선순위 규칙

1. `preset` 필드가 있으면 `${CLAUDE_PLUGIN_ROOT}/presets/{preset}.json` 로드
2. preset의 `modules`를 기본값으로 설정
3. profile.json의 `modules` 명시값으로 덮어씀
4. `overrides` 병합

### 모듈 → SKILL.md 경로 매핑

| 모듈 키          | 값                  | SKILL.md 경로                                          |
| ---------------- | ------------------- | ------------------------------------------------------ |
| `framework`      | react-nextjs-pages  | `${CLAUDE_PLUGIN_ROOT}/modules/frameworks/react-nextjs-pages/SKILL.md` |
| `framework`      | react-nextjs-app    | `${CLAUDE_PLUGIN_ROOT}/modules/frameworks/react-nextjs-app/SKILL.md` |
| `framework`      | react-spa           | `${CLAUDE_PLUGIN_ROOT}/modules/frameworks/react-spa/SKILL.md` |
| `design-system`  | mui                 | `${CLAUDE_PLUGIN_ROOT}/modules/design-systems/mui/SKILL.md` |
| `design-system`  | ant-design          | `${CLAUDE_PLUGIN_ROOT}/modules/design-systems/ant-design/SKILL.md` |
| `state`          | jotai-tanstack      | `${CLAUDE_PLUGIN_ROOT}/modules/state/jotai-tanstack/SKILL.md` |
| `state`          | zustand-tanstack    | `${CLAUDE_PLUGIN_ROOT}/modules/state/zustand-tanstack/SKILL.md` |
| `state`          | redux-rtk           | `${CLAUDE_PLUGIN_ROOT}/modules/state/redux-rtk/SKILL.md` |
| `styling`        | emotion             | `${CLAUDE_PLUGIN_ROOT}/modules/styling/emotion/SKILL.md` |
| `styling`        | tailwind            | `${CLAUDE_PLUGIN_ROOT}/modules/styling/tailwind/SKILL.md` |
| `styling`        | styled-components   | `${CLAUDE_PLUGIN_ROOT}/modules/styling/styled-components/SKILL.md` |
| `testing`        | jest                | `${CLAUDE_PLUGIN_ROOT}/modules/testing/jest/SKILL.md` |
| `testing`        | vitest              | `${CLAUDE_PLUGIN_ROOT}/modules/testing/vitest/SKILL.md` |
| `advanced`       | codex               | `${CLAUDE_PLUGIN_ROOT}/modules/advanced/codex/SKILL.md` |
| `advanced`       | figma               | `${CLAUDE_PLUGIN_ROOT}/modules/advanced/figma/SKILL.md` |

---

## Step 3: CLAUDE.md 생성

아래 템플릿으로 50줄 이내의 CLAUDE.md를 생성한다.

모듈 컨벤션 상세는 CLAUDE.md에 포함하지 않는다.
에이전트는 `@${CLAUDE_PLUGIN_ROOT}/modules/...` 참조로 직접 읽는다.

### CLAUDE.md 템플릿

```markdown
# {project.name} CLAUDE.md

> 자동 생성: /setup 스킬 | 수정 시 profile.json을 변경 후 /setup 재실행

## 스택

- Framework: {framework 설명}
- Design System: {design-system 설명}
- State: {state 설명}
- Styling: {styling 설명}
- Testing: {testing 설명}

## 명령어

```bash
# 개발
{project.dev}

# 빌드
{project.build}

# 린트
{project.lint}

# 테스트
{project.test}
```

## 규칙 참조

@{CLAUDE_PLUGIN_ROOT}/modules/frameworks/{framework}/SKILL.md
@{CLAUDE_PLUGIN_ROOT}/modules/design-systems/{design-system}/SKILL.md
@{CLAUDE_PLUGIN_ROOT}/modules/state/{state}/SKILL.md
@{CLAUDE_PLUGIN_ROOT}/modules/styling/{styling}/SKILL.md
@{CLAUDE_PLUGIN_ROOT}/modules/testing/{testing}/SKILL.md
```

### 스택 설명 매핑

| 모듈값              | 설명                          |
| ------------------- | ----------------------------- |
| react-nextjs-pages  | Next.js 14 Pages Router       |
| react-nextjs-app    | Next.js App Router            |
| react-spa           | React SPA (Vite/CRA)          |
| mui                 | Material UI                   |
| ant-design          | Ant Design                    |
| jotai-tanstack      | Jotai + TanStack Query v5     |
| zustand-tanstack    | Zustand + TanStack Query v5   |
| redux-rtk           | Redux Toolkit + RTK Query     |
| emotion             | Emotion (@emotion/styled)     |
| tailwind            | Tailwind CSS                  |
| styled-components   | Styled Components             |
| jest                | Jest                          |
| vitest              | Vitest                        |

---

## Step 4: 결과 요약 출력

```
/setup 완료

프로젝트: {project.name}
스택:
  Framework:     react-nextjs-pages  → Next.js 14 Pages Router
  State:         jotai-tanstack      → Jotai + TanStack Query v5
  Styling:       emotion             → Emotion (@emotion/styled)
  Testing:       jest                → Jest

생성된 파일:
  CLAUDE.md (47줄)

참조 모듈 (5개):
  @{CLAUDE_PLUGIN_ROOT}/modules/frameworks/react-nextjs-pages/SKILL.md
  @{CLAUDE_PLUGIN_ROOT}/modules/state/jotai-tanstack/SKILL.md
  @{CLAUDE_PLUGIN_ROOT}/modules/styling/emotion/SKILL.md
  @{CLAUDE_PLUGIN_ROOT}/modules/testing/jest/SKILL.md

다음 단계:
  - CLAUDE.md 내용을 확인하세요
  - 빌드/린트 명령어가 올바른지 확인하세요
  - profile.json의 overrides로 앱별 설정을 추가할 수 있습니다
```

### VAS 에이전트 추가 안내

결과 요약 끝에 다음을 추가 출력한다:

```
👉 /vas-create-agent 를 실행하면
   이 프로젝트에 최적화된 전용 에이전트를 자동 생성합니다.
   (프로젝트 분석 → VAS 인스턴스 생성 → 빌드타임 컴파일)
```

---

## 에러 처리

| 상황                          | 대응                                             |
| ----------------------------- | ------------------------------------------------ |
| preset 파일 없음              | 오류 출력 후 알려진 프리셋 목록 안내             |
| 모듈 SKILL.md 없음            | 경고 출력 후 해당 모듈 참조 제외하고 계속 진행   |
| profile.json JSON 파싱 실패   | 오류 내용 출력 후 수정 요청                      |
| CLAUDE.md 이미 존재           | 덮어쓰기 전 기존 내용 백업 (.claude/CLAUDE.md.bak) |

---

## 알려진 프리셋

| 프리셋명           | 스택                                          |
| ------------------ | --------------------------------------------- |
| standard   | Pages Router + Jotai + Emotion + Jest   |
| modern-stack       | MUI + App Router + Zustand + Tailwind + Vitest |
