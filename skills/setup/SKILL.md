---
name: setup
description: profile.json을 읽어 CLAUDE.md를 자동 생성한다. 프로젝트 스택에 맞는 모듈을 조합하여 Claude Code 환경을 세팅한다. 세션 시작 시 "code-forge updated" 또는 "version mismatch" 메시지가 보이면 사용자에게 재실행 여부를 물어본 후 이 스킬을 실행한다.
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
$ARGUMENTS 없음     → .claude/profile.json 자동 탐색
$ARGUMENTS 있음     → 파일 경로로 인식 (예: /setup .claude/profile.json)
$ARGUMENTS --profile → 코딩 프로필 생성만 실행 (아래 "코딩 프로필" 섹션 참조)
```

---

## 코딩 프로필 (`/setup --profile`)

`/setup --profile` 또는 "코딩 스타일 분석해줘" 요청 시 실행. `/setup` 기본 흐름에서는 묻지 않는다.

**흐름:**
1. Step 1에서 감지한 스택 정보(또는 package.json 분석)를 기반으로 **분석 카테고리를 동적 선택**
2. 프로젝트 코드를 실제로 읽고 (주요 디렉토리에서 2-3개 파일 샘플링) 패턴 분석
3. 결과를 `.claude/coding-profile.md`에 저장
4. 사용자에게 결과 보여주고 수정 여부 확인

**스택별 분석 카테고리 (동적 선택):**

| 카테고리 | 적용 스택 | 분석 내용 |
|---------|----------|----------|
| **추상화 습관** | 모든 스택 | 중복 코드 추출 기준, 함수/모듈 분리 기준 |
| **모듈/컴포넌트 설계** | React/Vue → 컴포넌트, Python/Go → 모듈/클래스 | 분리 기준, 계층 구조 |
| **상태/데이터 관리** | React → hooks/Query, 백엔드 → ORM/캐시 | 데이터 흐름 |
| **타입/스키마** | TS → interface/type, Python → type hints, Go → struct | 엄격도 |
| **에러 처리** | 모든 스택 | try-catch 전략, 에러 계층 |
| **네이밍/스타일** | 모든 스택 | 네이밍, early return, 비동기 |
| **폴더 구조** | 모든 스택 | 기능별/레이어별 |
| **커밋 스타일** | 모든 스택 | git log 분석 |
| **테스트 전략** | 모든 스택 | 단위/통합/E2E 비율 |
| **프레임워크 특화** | 감지된 것만 | Next.js→SSR, Django→view, Go→interface 등 |

**감지 못한 스택이면:** 범용 카테고리(추상화, 에러, 네이밍, 폴더, 커밋)만 분석 + Claude가 코드를 읽고 해당 언어에 맞는 질문 동적 생성

**참조 템플릿:** `${CLAUDE_PLUGIN_ROOT}/.candidate/code-analysis-prompt.md` (React/TS 예시)

**생성 경로:** `.claude/coding-profile.md` (local) 또는 `~/.claude/coding-profile.md` (global)

---

## 선택 UI 규칙

**모든 선택은 방향키+엔터 형식으로 제시한다.** 숫자 입력이나 Y/n 텍스트 입력을 받지 않는다.

### 기본 형식

```
질문 텍스트

> 옵션 A               ← 커서 위치 (방향키로 이동)
  옵션 B
  옵션 C
  기타 (직접 입력)      ← Tab 누르면 자유 텍스트 입력 모드
```

- `>` 커서가 현재 선택을 표시한다
- 위/아래 방향키로 이동, Enter로 확정
- 감지된 항목이 있으면 해당 항목에 커서를 기본 위치로 놓는다
- **"기타 (직접 입력)"** 옵션에서 Tab을 누르면 자유 텍스트 입력 모드로 전환된다

### Yes/No 형식

```
질문 텍스트

> 사용                  ← 기본값이면 여기에 커서
  사용 안 함
```

### 구현 방식 (Claude가 따를 규칙)

Claude Code에서는 실제 TUI를 렌더링할 수 없으므로, 아래 방식으로 동일한 UX를 달성한다:

1. 옵션을 위 형식으로 보여준다 (`>` 커서로 기본값 표시)
2. 사용자가 **번호, 이름, 또는 자연어**로 응답하면 해당 옵션을 선택한 것으로 처리
3. Enter만 누르면 (빈 응답) 기본값(`>` 위치) 적용
4. 옵션에 없는 텍스트를 입력하면 "기타 (직접 입력)"으로 처리

**핵심: 한 번에 하나만 묻고, 응답을 받은 후 다음으로 넘어간다.**

---

## Step 1: 대화형 온보딩 (profile.json 없을 때)

`.claude/profile.json`이 없으면 아래 서브스텝을 순차 진행한다.
**한 번에 하나씩 질문하고, 사용자 응답을 받은 후 다음으로 넘어간다.**

### 1-0. 설치 위치 선택

```
code-forge 설정을 시작합니다.

이 설정을 어디에 적용할까요?

> 이 프로젝트에만 (.claude/)
  전역 설정 (~/.claude/)
```

| 선택 | installTarget | profile.json 경로 | CLAUDE.md 경로 |
|------|--------------|-------------------|---------------|
| 이 프로젝트에만 | `local` | `.claude/profile.json` | `./CLAUDE.md` |
| 전역 설정 | `global` | `~/.claude/profile.json` | `~/.claude/CLAUDE.md` |

### 1-1. package.json 자동 감지 + 프로젝트 유형 판별

`package.json`이 존재하면 dependencies를 분석하여 스택을 자동 추론한다.

**프로젝트 유형 판별:**

먼저 프로젝트가 프론트엔드 서비스인지 판별한다.

| 조건 | 유형 | 스택 설정 |
|------|------|----------|
| `react`, `next`, `vue`, `angular` 등 UI 프레임워크 존재 | **서비스** | 스택 설정 진행 |
| `bin` 필드 존재 + UI 프레임워크 없음 | **CLI/도구** | 스택 설정 건너뛰기 |
| `main`/`exports` 필드 + UI 프레임워크 없음 | **라이브러리** | 스택 설정 건너뛰기 |
| `package.json` 없음 | **기타** | 스택 설정 건너뛰기 |
| UI 프레임워크 없지만 판단 불확실 | **확인 필요** | 사용자에게 질문 |

**서비스가 아닌 경우:**

```
이 프로젝트는 프론트엔드 서비스가 아닌 것 같습니다.
(감지: CLI 도구 / 라이브러리 / 스택 미감지)

스택 모듈 설정이 필요한가요?

> 건너뛰기 (명령어 + 기능 설정만)
  아니요, 스택 설정도 할게요
```

→ "건너뛰기" 선택 시: 1-2, 1-3을 건너뛰고 1-4(프로젝트 정보)로 직행
→ "스택 설정도 할게요" 선택 시: 정상 진행

**감지 규칙 (서비스인 경우):**

| dependency / 파일 | 추론 모듈 |
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
| `fastapi` in requirements.txt/pyproject.toml | framework: `python-fastapi` |
| `django` in requirements.txt/pyproject.toml | framework: `python-django` |
| `express` in package.json | framework: `node-express` |
| `go.mod` 존재 | framework: `go-standard` |

**추가 감지:**

| 조건 | 추론 |
|------|------|
| `app/layout.tsx` 존재 | App Router |
| `pages/_app.tsx` 존재 | Pages Router |
| `tailwind.config.*` 존재 | styling: `tailwind` |
| `jest.config.*` 존재 | testing: `jest` |
| `vitest.config.*` 존재 | testing: `vitest` |

**미매칭 라이브러리 감지:**

감지 규칙에 매칭되지 않는 관련 라이브러리가 있으면 해당 카테고리의 "기타" 옵션으로 자동 추가한다.

예시:
- `recoil` 감지 → State 카테고리에 `recoil (감지됨)` 옵션 동적 추가
- `sass` 감지 → Styling 카테고리에 `sass (감지됨)` 옵션 동적 추가
- `@testing-library/react` 있지만 jest/vitest 없음 → Testing에 해당 정보 표시

**카테고리별 감지 확장 규칙:**

| 카테고리 | 추가 감지 대상 |
|---------|--------------|
| Framework | `vue`, `angular`, `svelte`, `solid-js`, `remix`, `gatsby` |
| State | `recoil`, `mobx`, `valtio`, `xstate`, `swr` (TanStack Query 대체) |
| Styling | `sass`/`scss`, `less`, `vanilla-extract`, `panda-css`, `linaria` |
| Design System | `chakra-ui`, `radix-ui`, `shadcn`, `mantine` |
| Testing | `playwright`, `cypress`, `storybook` |

감지되면 해당 카테고리 옵션 목록에 `{라이브러리명} (감지됨)` 형태로 자동 삽입한다.

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

> standard 프리셋으로 진행
  직접 선택할게요
```

→ "standard 프리셋으로 진행" 선택 시: 1-4로 건너뜀 (프로젝트 정보 확인)
→ "직접 선택할게요" 선택 시: 1-3으로 진행

**프리셋 매칭 안 될 때:**

```
사용 가능한 프리셋:

> standard — Pages Router + Jotai + Emotion + Jest
  modern-stack — MUI + App Router + Zustand + Tailwind + Vitest
  backend-api — Node.js Express + TypeScript + Jest
  직접 선택 (감지 결과 기반)
```

### 1-3. 카테고리별 순차 질문

직접 선택 시 한 번에 한 카테고리씩 질문한다.
자동 감지 결과가 있으면 해당 항목에 `>` 커서를 놓는다 (기본 선택).

**각 카테고리마다 "기타" 옵션이 있다.** 감지되었지만 옵션에 없는 라이브러리는 자동으로 옵션에 추가된다.

```
[1/5] Framework

> react-nextjs-app — Next.js App Router     ← 감지됨
  react-nextjs-pages — Next.js Pages Router
  react-spa — React SPA (Vite/CRA)
  기타 (직접 입력)
```

```
[2/5] Design System

> 없음
  mui — Material UI
  ant-design — Ant Design
  기타 (직접 입력)
```

```
[3/5] State Management

> jotai-tanstack — Jotai + TanStack Query   ← 감지됨
  zustand-tanstack — Zustand + TanStack Query
  redux-rtk — Redux Toolkit + RTK Query
  기타 (직접 입력)
```

감지되었지만 옵션에 없는 경우 (예: recoil 감지):

```
[3/5] State Management

> recoil — Recoil                            ← 감지됨
  jotai-tanstack — Jotai + TanStack Query
  zustand-tanstack — Zustand + TanStack Query
  redux-rtk — Redux Toolkit + RTK Query
  기타 (직접 입력)
```

```
[4/5] Styling

> emotion — Emotion (@emotion/styled)       ← 감지됨
  tailwind — Tailwind CSS
  styled-components — Styled Components
  기타 (직접 입력)
```

```
[5/5] Testing

> vitest — Vitest                            ← 감지됨
  jest — Jest
  기타 (직접 입력)
```

**"기타" 선택 시 동작:**

```
[3/5] State Management

사용 중인 상태 관리 라이브러리를 입력해 주세요:
> recoil
```

입력값은 `modules.state`에 문자열로 저장된다. 대응하는 모듈 SKILL.md가 없으면 규칙 참조에서 제외되지만, profile.json에는 기록되어 CLAUDE.md 스택 섹션에 표시된다.

### 1-4. 프로젝트 정보 확인

자동 감지된 명령어를 보여주고 확인받는다.

```
[프로젝트 정보]

  프로젝트명: my-app (package.json name)
  dev:   yarn dev
  build: yarn build
  lint:  yarn lint
  test:  yarn test

> 이대로 진행
  수정할게요
```

→ "수정할게요" 선택 시: 각 항목을 하나씩 다시 질문

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

> 생성
  처음부터 다시
```

→ "생성": profile.json 생성 후 Step 2로 진행
→ "처음부터 다시": 1-0부터 재시작

### 파일이 있는 경우 — 파싱

```jsonc
// .claude/profile.json 예시
{
  "installTarget": "local",          // "local" | "global" (기본: "local")
  "projectType": "service",          // "service" | "library" | "cli" | "other"
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

### 커스텀 모듈 처리

`modules`의 값이 알려진 모듈 목록에 없으면 (예: `"state": "recoil"`):
- 대응하는 SKILL.md가 없으므로 규칙 참조에서 제외
- CLAUDE.md 스택 섹션에는 입력값 그대로 표시 (예: `State: recoil`)
- 에러 없이 정상 진행

### 모듈 → SKILL.md 경로 매핑

| 모듈 키          | 값                  | SKILL.md 경로                                          |
| ---------------- | ------------------- | ------------------------------------------------------ |
| `framework`      | react-nextjs-pages  | `${CLAUDE_PLUGIN_ROOT}/modules/frameworks/react-nextjs-pages/SKILL.md` |
| `framework`      | react-nextjs-app    | `${CLAUDE_PLUGIN_ROOT}/modules/frameworks/react-nextjs-app/SKILL.md` |
| `framework`      | react-spa           | `${CLAUDE_PLUGIN_ROOT}/modules/frameworks/react-spa/SKILL.md` |
| `framework`      | python-fastapi      | `${CLAUDE_PLUGIN_ROOT}/modules/frameworks/python-fastapi/SKILL.md` |
| `framework`      | python-django       | `${CLAUDE_PLUGIN_ROOT}/modules/frameworks/python-django/SKILL.md` |
| `framework`      | node-express        | `${CLAUDE_PLUGIN_ROOT}/modules/frameworks/node-express/SKILL.md` |
| `framework`      | go-standard         | `${CLAUDE_PLUGIN_ROOT}/modules/frameworks/go-standard/SKILL.md` |
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

**projectType이 "service"가 아닌 경우:**
- 스택 섹션과 규칙 참조 섹션을 생략
- 명령어 섹션만 포함

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

매핑에 없는 값 (커스텀 입력)은 입력값 그대로 표시한다.

---

## Step 3-2: AGENTS.md 생성 (Codex/멀티툴 호환)

CLAUDE.md와 동일한 경로에 `AGENTS.md`를 생성한다.
Codex CLI, GitHub Copilot 등 AGENTS.md를 읽는 도구에 사고모델 핵심을 전파한다.

| installTarget | 경로 |
|--------------|------|
| `local` | `./AGENTS.md` |
| `global` | `~/.claude/AGENTS.md` |

기존 AGENTS.md가 있으면 **건드리지 않는다** (사용자 커스텀 존중).

### AGENTS.md 템플릿

```markdown
# {project.name} AGENTS.md

> 자동 생성: code-forge /setup | CLAUDE.md와 함께 사용

## Working Protocol

모든 코드 작업에 아래 규칙을 따른다:

1. **읽기 우선** — 수정 전 반드시 파일을 읽는다. 기억에서 추론하지 않는다
2. **패턴 준수** — 기존 코드의 구조, 네이밍, 스타일을 따른다
3. **정책 보존** — 비즈니스 로직을 임의 변경하지 않는다
4. **최소 변경** — 요청받은 것만 수정한다
5. **스코프 준수** — 대상 외 파일은 명시 요청 없이 수정하지 않는다

작업 루프: GROUND(맥락 파악) → APPLY(구현) → VERIFY(검증) → ADAPT(실패 시 조정)

## Project Conventions

Read CLAUDE.md for stack-specific rules, commands, and module references.
```

**projectType이 "service"가 아닌 경우에도 동일하게 생성한다** (사고모델은 스택 무관).

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
  AGENTS.md (사고모델 핵심 — Codex/멀티툴 호환)
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

## Step 6: 기능 선택 (옵셔널)

스택 설정 완료 후, code-forge의 옵셔널 기능을 대화형으로 설정한다.
**하나씩 순차적으로 묻는다. 한 번에 모두 보여주지 않는다.**

> 나중에 변경: `/smith-setup` (Smith on/off), 또는 `code-forge.local.md` 직접 수정

### 6-1. Smith

```
[1/3] Smith (에이전트 빌드 시스템)
프로젝트에 최적화된 전용 에이전트를 만들 수 있습니다.

> 사용
  사용 안 함
```

→ 응답을 받은 후 다음으로 넘어간다.

### 6-2. Whetstone

```
[2/3] Whetstone (코딩 연습)
/practice로 코딩 면접 시뮬레이션을 할 수 있습니다.

> 사용
  사용 안 함
```

### 6-3. Bellows

```
[3/3] Bellows (사용량 로깅)
어떤 에이전트/스킬을 얼마나 쓰는지 로컬 로그를 남깁니다.

  사용
> 사용 안 함
```

Bellows는 기본값이 "사용 안 함"이다.

### 설정 결과

설정 결과를 `code-forge.local.md`에 저장:

```yaml
plugins:
  smith:
    enabled: true    # 사용자 선택 반영
  whetstone:
    enabled: true
  bellows:
    enabled: false
```

### Smith를 켠 경우

```
Smith가 활성화되었습니다.

지금 바로 프로젝트 전용 에이전트를 만들까요?

> /smith-create-agent 실행
  나중에
```

→ "/smith-create-agent 실행" 선택 시: 자동 호출 (프로젝트 분석 → 에이전트 생성 → 빌드)
→ "나중에" 선택 시: 스킵

```
(나중에 하려면 /smith-create-agent를 실행하세요)
```

### 설정 완료 안내

```
설정이 완료되었습니다.

이 설정은 code-forge.local.md에 저장됩니다.
개별 프로젝트에서 나중에 변경하려면:
  /smith-setup        → Smith(에이전트 빌드) on/off
  code-forge.local.md → 직접 편집도 가능
```

---

## CLAUDE.md 백업 안내

기존 CLAUDE.md가 있는 경우:

```
기존 CLAUDE.md가 발견되었습니다.

> 백업 후 새로 생성 (기존 → .claude/CLAUDE.md.bak)
  기존 내용과 합치기 (하단에 code-forge 설정 추가)
  취소
```

| 선택 | 동작 |
|------|------|
| 백업 후 새로 생성 | 기존 파일을 `.claude/CLAUDE.md.bak`으로 이동 후 새로 생성 |
| 기존 내용과 합치기 | 기존 CLAUDE.md 하단에 `---` 구분선 + code-forge 설정 추가 |
| 취소 | 아무것도 하지 않고 종료 |

"기존 내용과 합치기" 선택 시 기존 내용을 보존하면서 스택/명령어/모듈 참조만 추가한다.

---

## 에러 처리

| 상황                          | 대응                                             |
| ----------------------------- | ------------------------------------------------ |
| package.json 없음             | 프로젝트 유형을 "기타"로 판별, 스택 설정 건너뛰기 제안 |
| package.json에서 스택 감지 불가 | "감지된 스택이 없습니다" 출력 후 수동 선택       |
| preset 파일 없음              | 오류 출력 후 알려진 프리셋 목록 안내             |
| 모듈 SKILL.md 없음            | 경고 출력 후 해당 모듈 참조 제외하고 계속 진행   |
| profile.json JSON 파싱 실패   | 오류 내용 출력 후 수정 요청                      |
| CLAUDE.md 이미 존재           | CLAUDE.md 백업 안내 참조 |
| 전역 profile.json 이미 존재   | 기존 설정 보여주고 덮어쓰기 확인                 |
| 로컬 + 전역 모두 존재         | 로컬 우선 적용, 전역은 fallback임을 안내         |
| 커스텀 모듈값 (옵션에 없는 값) | 정상 처리, SKILL.md 참조만 제외                  |

---

## 알려진 프리셋

| 프리셋명           | 스택                                          |
| ------------------ | --------------------------------------------- |
| standard           | Pages Router + Jotai + Emotion + Jest         |
| modern-stack       | MUI + App Router + Zustand + Tailwind + Vitest |
