# code-forge

프로젝트 스택에 맞는 에이전트, 스킬, 컨벤션을 조합하는 Claude Code 플러그인.

---

## 설치

```bash
# 플러그인 클론
git clone https://github.com/ggombee/code-forge.git

# Claude Code에서 플러그인 추가
/install-plugin /path/to/code-forge
```

로컬 개발 시:
```bash
claude --plugin-dir ./code-forge
```

---

## 시작하기

### 1. 프로젝트 스택 세팅

```
/setup
```

`package.json` 자동 감지 → 스택 추천 → 프리셋 또는 커스텀 선택 → `CLAUDE.md` 자동 생성.

`.claude/profile.json`을 미리 만들어두면 바로 세팅:

```json
{
  "preset": "standard"
}
```

### 2. Agent Teams 설정 (선택, Claude Max 전용)

```
/setup-agent-teams
```

3개+ 에이전트 병렬 협업이 필요한 경우 설정.

---

## 핵심 워크플로우

```
/start feature.md              # 분석 → 구현 → 검증 → 커밋 → PR (원큐)
/start feature.md --plan-only  # 분석+계획만 출력하고 멈춤
/done                          # 이미 구현된 코드 검증 → 커밋 → PR
/done --skip-test              # 테스트 스킵 (스타일 변경 등)
/bug-fix "에러 메시지"          # 2-3 옵션 제시 → 선택 → 수정
/quality                       # 포맷 → 린트 → 타입 체크
```

---

## 이 플러그인이 해주는 것

| 기능 | 설명 |
|------|------|
| **원큐 워크플로우** | `/start`로 분석부터 PR까지 한 번에 |
| **자동 스택 세팅** | `/setup` 한 번으로 스택에 맞는 규칙 자동 적용 |
| **테스트 자동 생성** | `/generate-test`로 BDD 시나리오 기반 테스트 코드 생성 |
| **버그 수정 옵션** | `/bug-fix`로 2-3가지 해결 방안 제시 |
| **Figma → 코드** | `/figma-to-code`로 Figma 디자인을 코드로 변환 |
| **코드 리뷰 자동화** | `code-reviewer` 에이전트가 품질+보안 리뷰 |
| **멀티에이전트 협업** | 14개 전문 에이전트가 분석/구현/검증 병렬 수행 |
| **Smith 에이전트 시스템** | 프로젝트에 최적화된 에이전트 생성 |
| **Mac 알림** | `/setup-notifier`로 승인 요청 시 배너 알림 설정 |

---

## 에이전트 (14개)

`/smith-build`로 컴파일된 에이전트. 권한에 따라 4단계로 분류된다.

### READ-ONLY — 분석만, 파일 수정 없음

| 에이전트 | 모델 | 용도 |
|---------|------|------|
| `analyst` | opus | 요구사항 분석, 누락된 질문/엣지 케이스 발견 |
| `architect` | opus | 아키텍처 분석, 설계 자문 |
| `refactor-advisor` | sonnet | 리팩토링 전략 분석 |
| `vision` | sonnet | 이미지/PDF/다이어그램 분석 |

### SHELL-ACCESS — Bash 포함, Write/Edit 없음

| 에이전트 | 모델 | 용도 |
|---------|------|------|
| `scout` | haiku | 코드베이스 빠른 탐색, 파일 구조 파악 |
| `code-reviewer` | sonnet | 코드 리뷰 (품질+보안) + 패턴 학습 |
| `git-operator` | sonnet | Git 커밋/브랜치 관리 |
| `researcher` | sonnet | 외부 문서/라이브러리 조사 |

### EDIT-ONLY — Edit 포함, Write 없음

| 에이전트 | 모델 | 용도 |
|---------|------|------|
| `lint-fixer` | haiku | ESLint/TypeScript 오류 자동 수정 |
| `build-fixer` | sonnet | 빌드/컴파일 오류 수정 |

### READ-WRITE-FULL — Write 포함 전체 권한

| 에이전트 | 모델 | 용도 |
|---------|------|------|
| `implementor` | sonnet | 계획 기반 즉시 구현 |
| `deep-executor` | sonnet | 자율적 심층 구현 + Ralph Loop |
| `testgen` | sonnet | 테스트 코드 생성 (generate/tdd 모드) |
| `codex` | sonnet | Codex 페어 프로그래밍 (MCP/CLI 듀얼 모드) |

---

## Smith (Agent Smith System)

STATE(지식)와 ACT(행동)를 분리하여 에이전트를 정의하는 시스템. `/smith-build`가 Smith 인스턴스를 빌드타임에 정적 .md로 컴파일하므로, 런타임 해석 비용 없이 Claude Code 네이티브 포맷으로 동작한다.

```
Smith 인스턴스 (_agents/*.md) → /smith-build → 플랫 .md (agents/)
```

### 프로젝트 전용 에이전트 생성

```
/smith-create-agent
```

프로젝트를 분석하여 `.agents/agents/`에 Smith 인스턴스를 생성하고 `/smith-build --project`로 `.claude/agents/`에 컴파일한다.

### Smith 스킬

| 스킬 | 설명 |
|------|------|
| `/smith-build` | Smith 인스턴스를 정적 .md로 컴파일 (전체/프로젝트/검증) |
| `/smith-create-agent` | 프로젝트 분석 → Smith instance 생성 → 자동 빌드 |

---

## 스킬 (22개)

### 워크플로우

| 스킬 | 설명 |
|------|------|
| `/start` | MD 파일 또는 텍스트로 작업 정의 → 분석 → 구현 → 검증 → 커밋 → PR |
| `/done` | 구현 완료 후 검증 → 테스트 → 커밋 → PR 생성 |
| `/commit` | staged 변경사항 분석 → 커밋 메시지 생성 → 커밋 |
| `/quality` | 포맷(Prettier) → 린트(ESLint) → 타입 체크(tsc) + 오류 자동 수정 |

### 구현

| 스킬 | 설명 |
|------|------|
| `/bug-fix` | 버그 분석 후 2-3가지 해결 옵션 제시 후 구현 |
| `/refactor` | 리팩토링 분석 + 정책 보호 테스트 |
| `/generate-test` | BDD 시나리오 기반 테스트 코드 자동 생성 |
| `/setup-test` | 테스트 환경 초기 세팅 (jest/vitest, MSW 등) |
| `/figma-to-code` | Figma 디자인 → 코드 변환 |

### 분석

| 스킬 | 설명 |
|------|------|
| `/debate` | 교차 모델 토론으로 구현 방향 결정 |
| `/elon-musk` | 제1원칙 사고법 문제 해결 |
| `/genius-thinking` | 10가지 인지 공식 + TRIZ/SCAMPER 아이디어 발상 |
| `/research` | 구조화된 리서치 + 마크다운 리포트 |
| `/startup-validator` | Peter Thiel 7Q + YC PMF 스타트업 검증 |
| `/crawler` | Playwright 기반 크롤링 흐름 설계 |

### 설정

| 스킬 | 설명 |
|------|------|
| `/setup` | 프로젝트 스택 세팅 (package.json 자동 감지 + 대화형 온보딩) |
| `/setup-notifier` | Mac 알림 설정 (승인 요청 시 배너 알림) |
| `/setup-agent-teams` | Agent Teams 환경 설정 (Claude Max 전용) |

### 유틸

| 스킬 | 설명 |
|------|------|
| `/version-update` | 시맨틱 버전 업데이트 + 커밋 |
| `/docs-creator` | 문서 작성 가이드 |
| `/codex` | Codex 페어 프로그래밍 (미설정 시 설정 가이드 안내) |
| `/gemini` | Google Gemini CLI 래퍼 |

---

## 프리셋

| 프리셋 | 스택 |
|--------|------|
| `standard` | Next.js Pages Router + Jotai + Emotion + Jest |
| `modern-stack` | MUI + Next.js App Router + Zustand + Tailwind + Vitest |

개별 모듈 직접 선택:

```json
{
  "modules": {
    "framework": "react-nextjs-app",
    "design-system": "mui",
    "state": "zustand-tanstack",
    "styling": "tailwind",
    "testing": "vitest"
  }
}
```

---

## 모듈 시스템 (13개)

| 카테고리 | 모듈 |
|---------|------|
| Framework | `react-nextjs-pages`, `react-nextjs-app`, `react-spa` |
| Design System | `mui`, `ant-design` |
| State | `jotai-tanstack`, `zustand-tanstack`, `redux-rtk` |
| Styling | `emotion`, `tailwind`, `styled-components` |
| Testing | `jest`, `vitest` |

---

## 플러그인 구조

```
code-forge/
├── .claude-plugin/plugin.json    # 플러그인 매니페스트
├── agents/                       # 컴파일된 에이전트 14개 (/smith-build로 생성)
├── plugins/
│   └── smith/                    # Smith (Agent Smith System)
│       ├── agents/
│       │   ├── _agents/          #   Smith 기본 instance 15개 (컴파일 소스)
│       │   ├── interface/        #   구조 정의 (state-agent, act-agent)
│       │   ├── state/            #   STATE class (role, language, framework, ...)
│       │   └── act/              #   ACT class (analysis, dev, quality, ops)
│       ├── skills/               #   /smith-build, /smith-create-agent
│       └── rules/                #   Smith 해석 규칙 (reference-only)
├── skills/                       # 스킬 22개
├── modules/                      # 스택 모듈 13개
├── presets/                      # 프리셋 (standard, modern-stack)
├── hooks/                        # 이벤트 훅 (guard.sh, lint-fix.sh, notify.sh)
├── commands/                     # 슬래시 커맨드 (git-all, git-merge, git-session, lint-fix, pre-deploy)
├── rules/                        # 핵심 규칙 (thinking-model, coding-standards)
├── instructions/                 # 멀티에이전트 협업 가이드
└── docs/                         # 참고 문서
```

---

## MCP 연동 (opt-in)

플러그인 설치만으로 기본 기능은 모두 사용 가능. 아래는 추가 연동:

| MCP 서버 | 용도 | 설정 가이드 |
|----------|------|------------|
| Codex | Codex 페어 프로그래밍 | `docs/codex-mcp-setup-guide.md` |
| Figma | 디자인 데이터 자동 fetch | `docs/codex-mcp-setup-guide.md` 하단 |

> `/codex` 스킬 실행 시 Codex가 미설정이면 설정 가이드를 자동으로 안내한다.

---

## 라이센스

MIT
