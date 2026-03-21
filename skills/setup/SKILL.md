---
name: setup
description: profile.json을 읽어 CLAUDE.md를 자동 생성한다. 프로젝트 스택에 맞는 모듈을 조합하여 Claude Code 환경을 세팅한다.
category: setup
---

# /setup 스킬

프로젝트의 `.claude/profile.json`을 읽어 스택에 맞는 CLAUDE.md를 자동 생성한다.

---

## 동작 흐름

```
profile.json 존재 → Step 2로 바로 진행 (기존 파싱)
profile.json 없음 → Step 1 대화형 온보딩
```

---

## ARGUMENT 처리

```
$ARGUMENTS 없음 → .claude/profile.json 자동 탐색

$ARGUMENTS 있음 → 파일 경로로 인식
예: /setup .claude/profile.json
```

---

## Step 1: 대화형 온보딩 (profile.json 없을 때)

`.claude/profile.json`이 없으면 아래 서브스텝을 순차 진행한다.
**한 번에 하나씩 질문하고, 사용자 응답을 받은 후 다음으로 넘어간다.**

### 1-0. 설치 위치 선택

```
code-forge 설정을 시작합니다.

이 설정을 어디에 적용할까요?

  1. 이 프로젝트에만 (./CLAUDE.md + .claude/profile.json)
  2. 전역 설정 (~/.claude/CLAUDE.md + ~/.claude/profile.json)

> 대부분 1번을 선택합니다.
```

| 선택 | installTarget | profile.json 경로 | CLAUDE.md 경로 |
|------|--------------|-------------------|---------------|
| 1 | `local` | `.claude/profile.json` | `./CLAUDE.md` |
| 2 | `global` | `~/.claude/profile.json` | `~/.claude/CLAUDE.md` |

### 1-1. package.json 자동 감지

`package.json`이 존재하면 dependencies를 분석하여 스택을 자동 추론한다.

**감지 규칙:**

| dependency | 추론 모듈 |
|-----------|----------|
| `next` | framework: `react-nextjs-pages` 또는 `react-nextjs-app` |
| `react` (next 없음) | framework: `react-spa` |
| `jotai` + `@tanstack/react-query` | state: `jotai-tanstack` |
| `zustand` + `@tanstack/react-query` | state: `zustand-tanstack` |
| `@reduxjs/toolkit` | state: `redux-rtk` |
| `@emotion/styled` 또는 `@emotion/react` | styling: `emotion` |
| `tailwindcss` | styling: `tailwind` |
| `styled-components` | styling: `styled-components` |
| `@mui/material` | design-system: `mui` |
| `antd` | design-system: `ant-design` |
| `jest` | testing: `jest` |
| `vitest` | testing: `vitest` |

**추가 감지:**

| 조건 | 추론 |
|------|------|
| `app/layout.tsx` 존재 | App Router |
| `pages/_app.tsx` 존재 | Pages Router |
| `tailwind.config.*` 존재 | styling: `tailwind` |
| `jest.config.*` 존재 | testing: `jest` |
| `vitest.config.*` 존재 | testing: `vitest` |

**프로젝트 정보 자동 추출:**

`package.json`의 `scripts`에서 `dev`, `build`, `lint`, `test` 명령어를 추출한다.
패키지 매니저는 lock 파일로 판단: `yarn.lock` → yarn, `pnpm-lock.yaml` → pnpm, 그 외 → npm.

```
package.json을 분석합니다...

감지된 스택:
  Framework:     next (14.2.x) → react-nextjs-app
  State:         jotai (2.x) + @tanstack/react-query (5.x) → jotai-tanstack
  Styling:       @emotion/styled (11.x) → emotion
  Testing:       vitest (1.x) → vitest
  Design System: 감지 안 됨

감지된 명령어:
  dev:   yarn dev
  build: yarn build
  lint:  yarn lint
  test:  yarn test
```

package.json이 없으면 이 단계를 건너뛰고 1-3으로 직행한다.

### 1-2. 프리셋 매칭 및 제안

감지 결과를 기존 프리셋과 비교한다.

**매칭 알고리즘:**
- 감지된 modules와 preset.json의 modules를 비교
- 모든 필드 일치 → "일치합니다"
- 80%+ 일치 → "유사합니다 (차이: X)"
- 그 외 → "매칭 없음"

**프리셋 매칭 시:**

```
감지 결과가 "standard" 프리셋과 일치합니다.

  standard: Pages Router + Jotai + Emotion + Jest

이 프리셋을 사용할까요?
  1. 네, standard 프리셋으로 진행
  2. 아니요, 직접 선택할게요
```

→ 1번 선택 시: 1-4로 건너뜀 (프로젝트 정보 확인)
→ 2번 선택 시: 1-3으로 진행

**프리셋 매칭 안 될 때:**

```
사용 가능한 프리셋:
  1. standard — Pages Router + Jotai + Emotion + Jest
  2. modern-stack — MUI + App Router + Zustand + Tailwind + Vitest
  3. 직접 선택 (감지 결과 기반)
```

### 1-3. 카테고리별 순차 질문

직접 선택 시 한 번에 한 카테고리씩 질문한다.
자동 감지 결과가 있으면 `← 감지됨`으로 표시하고 기본값으로 설정한다.

```
[1/5] Framework

  1. react-nextjs-pages — Next.js Pages Router
  2. react-nextjs-app — Next.js App Router  ← 감지됨
  3. react-spa — React SPA (Vite/CRA)

선택 (기본: 2):
```

```
[2/5] Design System

  1. mui — Material UI
  2. ant-design — Ant Design
  3. 없음  ← 기본

선택 (기본: 3):
```

```
[3/5] State Management

  1. jotai-tanstack — Jotai + TanStack Query  ← 감지됨
  2. zustand-tanstack — Zustand + TanStack Query
  3. redux-rtk — Redux Toolkit + RTK Query

선택 (기본: 1):
```

```
[4/5] Styling

  1. emotion — Emotion (@emotion/styled)  ← 감지됨
  2. tailwind — Tailwind CSS
  3. styled-components

선택 (기본: 1):
```

```
[5/5] Testing

  1. jest — Jest
  2. vitest — Vitest  ← 감지됨

선택 (기본: 2):
```

### 1-4. 프로젝트 정보 확인

자동 감지된 명령어를 보여주고 확인받는다.

```
[프로젝트 정보]

  프로젝트명: my-app (package.json name)
  dev:   yarn dev
  build: yarn build
  lint:  yarn lint
  test:  yarn test

이대로 진행할까요? (수정이 필요하면 말씀해 주세요)
```

package.json이 없었으면 각 항목을 직접 물어본다:

```
[프로젝트 정보]

프로젝트 이름을 입력해 주세요:
>

개발 서버 명령어 (예: yarn dev):
>

빌드 명령어 (예: yarn build):
>

린트 명령어 (예: yarn lint):
>

테스트 명령어 (예: yarn test):
>
```

### 1-5. 최종 확인

```
설정 요약

  설치 위치:     이 프로젝트 (.claude/)
  프리셋:        없음 (커스텀)

  Framework:     react-nextjs-app     → Next.js App Router
  Design System: 없음
  State:         jotai-tanstack       → Jotai + TanStack Query v5
  Styling:       emotion              → Emotion (@emotion/styled)
  Testing:       vitest               → Vitest

  프로젝트명: my-app
  dev:   yarn dev
  build: yarn build
  lint:  yarn lint
  test:  yarn test

이대로 생성할까요? [Y/n]
```

→ Y: profile.json 생성 후 Step 2로 진행
→ N: 1-2부터 재시작

### 파일이 있는 경우 — 파싱

```jsonc
// .claude/profile.json 예시
{
  "installTarget": "local",          // "local" | "global" (기본: "local")
  "preset": "standard",              // 프리셋 사용 (선택)
  "modules": {                       // 개별 모듈 직접 선택 (선택)
    "framework": "react-nextjs-pages",
    "state": "jotai-tanstack",
    "styling": "emotion",
    "testing": "jest"
  },
  "project": {                       // 프로젝트 기본 정보 (선택)
    "name": "my-project",
    "dev": "yarn dev",
    "build": "yarn build",
    "lint": "yarn lint",
    "test": "yarn test"
  },
  "overrides": {}                    // 앱별 오버라이드 (선택)
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

---

## Step 3: CLAUDE.md 생성

아래 템플릿으로 50줄 이내의 CLAUDE.md를 생성한다.
`installTarget`에 따라 생성 경로가 달라진다.

모듈 컨벤션 상세는 CLAUDE.md에 포함하지 않는다.
에이전트는 `@${CLAUDE_PLUGIN_ROOT}/modules/...` 참조로 직접 읽는다.

| installTarget | CLAUDE.md 경로 |
|--------------|---------------|
| `local` | `./CLAUDE.md` |
| `global` | `~/.claude/CLAUDE.md` |

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
설치 위치: {installTarget}
스택:
  Framework:     react-nextjs-app   → Next.js App Router
  State:         jotai-tanstack     → Jotai + TanStack Query v5
  Styling:       emotion            → Emotion (@emotion/styled)
  Testing:       vitest             → Vitest

생성된 파일:
  CLAUDE.md (47줄)
  .claude/profile.json

참조 모듈 (4개):
  @{CLAUDE_PLUGIN_ROOT}/modules/frameworks/react-nextjs-app/SKILL.md
  @{CLAUDE_PLUGIN_ROOT}/modules/state/jotai-tanstack/SKILL.md
  @{CLAUDE_PLUGIN_ROOT}/modules/styling/emotion/SKILL.md
  @{CLAUDE_PLUGIN_ROOT}/modules/testing/vitest/SKILL.md

다음 단계:
  - CLAUDE.md 내용을 확인하세요
  - 빌드/린트 명령어가 올바른지 확인하세요
  - profile.json의 overrides로 앱별 설정을 추가할 수 있습니다
```

## Step 5: code-forge.local.md 생성

CLAUDE.md 생성 완료 후, 프로젝트 로컬 설정 파일을 생성한다.
이미 존재하면 `version` 필드만 업데이트한다.

`plugin.json`에서 현재 버전을 읽어온다: `${CLAUDE_PLUGIN_ROOT}/.claude-plugin/plugin.json` → `version` 필드.

| installTarget | 경로 |
|--------------|------|
| `local` | `.claude/code-forge.local.md` |
| `global` | `~/.claude/code-forge.local.md` |

```markdown
---
version: {plugin.json의 version}
plugins:
  smith:
    enabled: false
---
```

- `version`: 이 프로젝트에 적용된 code-forge 버전. 플러그인 업데이트 후 `/setup` 재실행 시 버전 차이를 감지하여 CLAUDE.md를 재생성한다.
- `plugins.smith`: `/smith-setup`에서 확장한다. 초기값은 `enabled: false`.

## Step 6: Smith 설정

`/smith-setup` 스킬을 자동 호출하여 Smith 활성화 여부를 설정한다.
`/smith-setup`은 Step 5에서 생성한 `code-forge.local.md`의 `plugins.smith` 섹션을 업데이트한다.

### Smith 에이전트 추가 안내

결과 요약 끝에 다음을 추가 출력한다:

```
/smith-create-agent 를 실행하면
   이 프로젝트에 최적화된 전용 에이전트를 자동 생성합니다.
   (프로젝트 분석 → Smith 인스턴스 생성 → 빌드타임 컴파일)
```

---

## 에러 처리

| 상황                          | 대응                                             |
| ----------------------------- | ------------------------------------------------ |
| package.json 없음             | 감지 건너뛰고 수동 선택으로 진행                 |
| package.json에서 스택 감지 불가 | "감지된 스택이 없습니다" 출력 후 수동 선택       |
| preset 파일 없음              | 오류 출력 후 알려진 프리셋 목록 안내             |
| 모듈 SKILL.md 없음            | 경고 출력 후 해당 모듈 참조 제외하고 계속 진행   |
| profile.json JSON 파싱 실패   | 오류 내용 출력 후 수정 요청                      |
| CLAUDE.md 이미 존재           | 덮어쓰기 전 기존 내용 백업 (.claude/CLAUDE.md.bak) |
| 전역 profile.json 이미 존재   | 기존 설정 보여주고 덮어쓰기 확인                 |
| 로컬 + 전역 모두 존재         | 로컬 우선 적용, 전역은 fallback임을 안내         |

---

## 알려진 프리셋

| 프리셋명           | 스택                                          |
| ------------------ | --------------------------------------------- |
| standard           | Pages Router + Jotai + Emotion + Jest         |
| modern-stack       | MUI + App Router + Zustand + Tailwind + Vitest |
