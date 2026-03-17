# code-forge

프로젝트 스택에 맞는 에이전트, 스킬, 컨벤션을 조합하는 Claude Code 플러그인.

---

## Quick Start

```
/setup         # 프로젝트 스택 세팅 (최초 1회)
/bug-fix       # 버그 분석 + 해결 옵션 제시
/generate-test # BDD 기반 테스트 코드 생성
/debate        # 구현 방향 교차 토론
```

---

## 이 플러그인이 해주는 것

| 기능 | 설명 |
|------|------|
| **자동 스택 세팅** | `/setup` 한 번으로 프로젝트 스택(Framework, DS, State 등)에 맞는 규칙 자동 적용 |
| **테스트 자동 생성** | `/generate-test`로 BDD 시나리오 기반 테스트 코드 생성 + 실행 |
| **버그 수정 옵션** | `/bug-fix`로 버그 분석 후 2-3가지 해결 방안 제시 |
| **Figma → 코드** | `/figma-to-code`로 Figma 디자인을 코드로 변환 |
| **코드 리뷰 자동화** | `code-reviewer` 에이전트가 품질 + 보안 리뷰, 패턴 학습 |
| **멀티에이전트 협업** | 14개 전문 에이전트가 분석/구현/검증을 병렬 수행 |
| **VAS 에이전트 시스템** | STATE(지식) + ACT(행동) 조합으로 프로젝트에 최적화된 에이전트 생성 |
| **Mac 알림** | `/setup-notifier`로 승인 요청 시 배너 알림 설정 |
| **Codex 페어 프로그래밍** | `/codex`로 Codex와 협업 (미설정 시 자동 설정 가이드 안내) |

---

## 설치

```bash
# 플러그인 설치
claude plugin install code-forge
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

대화형으로 스택을 선택하거나, `.claude/profile.json`을 미리 만들어두면 자동 세팅:

```json
{
  "preset": "standard"
}
```

### 2. Agent Teams 설정 (선택, Claude Max 전용)

```
/setup-agent-teams
```

3개+ 에이전트 병렬 협업이 필요한 경우 설정. 설정 후 14개 전문 에이전트를 팀으로 활용 가능.

---

## 에이전트 (14개)

`/vas-build`로 컴파일된 에이전트. 권한에 따라 4단계로 분류된다.

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
| `code-reviewer` | sonnet | 코드 리뷰 (품질 + 보안) + 패턴 학습 |
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

## VAS (Vibe-Agent-System)

STATE(지식)와 ACT(행동)를 분리하여 에이전트를 정의하는 시스템. `/vas-build`가 VAS 인스턴스를 빌드타임에 정적 .md로 컴파일하므로, 런타임 해석 비용 없이 Claude Code 네이티브 포맷으로 동작한다.

```
VAS 인스턴스 (_agents/*.md) → /vas-build → 플랫 .md (agents/)
```

### 프로젝트 전용 에이전트 생성

```
/vas-create-agent
```

프로젝트를 분석하여 `.agents/agents/`에 VAS 인스턴스를 생성하고 `/vas-build --project`로 `.claude/agents/`에 컴파일한다.

### VAS 스킬

| 스킬 | 설명 |
|------|------|
| `/vas-build` | VAS 인스턴스를 정적 .md로 컴파일 (전체/프로젝트/검증) |
| `/vas-create-agent` | 프로젝트 분석 → VAS instance 생성 → 자동 빌드 |

---

## 스킬 (20개)

### 작업 흐름

| 스킬 | 설명 |
|------|------|
| `/setup` | 프로젝트 스택 자동 세팅 |
| `/setup-agent-teams` | Agent Teams 환경 설정 (Claude Max 전용) |

### 코드 생성/수정

| 스킬 | 설명 |
|------|------|
| `/generate-test` | BDD 시나리오 기반 테스트 코드 자동 생성 |
| `/bug-fix` | 버그 분석 후 2-3가지 해결 옵션 제시 |
| `/refactor` | 리팩토링 분석 + 정책 보호 테스트 |
| `/figma-to-code` | Figma 디자인 → 코드 변환 |
| `/version-update` | 시맨틱 버전 업데이트 + 커밋 |

### 분석/토론/리서치

| 스킬 | 설명 |
|------|------|
| `/debate` | 교차 모델 토론으로 구현 방향 결정 |
| `/docs-creator` | 문서 작성 가이드 |
| `/research` | 구조화된 리서치 + 마크다운 리포트 |
| `/elon-musk` | 제1원칙 사고법 문제 해결 |
| `/genius-thinking` | 10가지 인지 공식 + TRIZ/SCAMPER 아이디어 발상 |
| `/startup-validator` | Peter Thiel 7Q + YC PMF 스타트업 검증 |

### 환경 설정

| 스킬 | 설명 |
|------|------|
| `/setup-test` | 테스트 환경 초기 세팅 (jest/vitest, MSW 등) |
| `/setup-notifier` | Mac 알림 설정 (승인 요청 시 배너 알림) |
| `/codex` | Codex 페어 프로그래밍 (미설정 시 자동 설정 가이드 안내) |
| `/gemini` | Google Gemini CLI 래퍼 |
| `/crawler` | Playwright 기반 크롤링 흐름 설계 |

### VAS

| 스킬 | 설명 |
|------|------|
| `/vas-build` | VAS 인스턴스를 정적 .md로 컴파일 (전체/프로젝트/검증) |
| `/vas-create-agent` | 프로젝트 분석 → VAS instance 생성 → 자동 빌드 |

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
├── agents/                       # 컴파일된 에이전트 14개 (/vas-build로 생성)
├── plugins/
│   └── vas/                      # VAS (Vibe-Agent-System)
│       ├── agents/
│       │   ├── _agents/          #   VAS 기본 instance 14개 (컴파일 소스)
│       │   ├── interface/        #   구조 정의 (state-agent, act-agent)
│       │   ├── state/            #   STATE class (role, language, framework, ...)
│       │   └── act/              #   ACT class (analysis, dev, quality, ops)
│       ├── skills/               #   /vas-build, /vas-create-agent
│       └── rules/                #   VAS 해석 규칙 (reference-only)
├── skills/                       # 스킬 20개
├── modules/                      # 스택 모듈 13개
├── presets/                      # 프리셋 (standard, modern-stack)
├── hooks/                        # 이벤트 훅 (Mac 알림: notify.sh)
├── commands/                     # 슬래시 커맨드 (git-all, git-merge, git-session, lint-fix, pre-deploy)
├── rules/                        # 핵심 규칙 (작업 절차, 코딩 표준)
├── instructions/                 # 멀티에이전트 협업 가이드
└── docs/                         # MCP 설정 가이드
```

---

## MCP 연동 (opt-in)

플러그인 설치만으로 기본 기능은 모두 사용 가능. 아래는 추가 연동:

| MCP 서버 | 용도 | 설정 가이드 |
|----------|------|------------|
| Codex | Codex 페어 프로그래밍 | `docs/codex-mcp-setup-guide.md` |
| Figma | 디자인 데이터 자동 fetch | `docs/codex-mcp-setup-guide.md` 하단 |
| Atlassian | Jira/Confluence 연동 | `docs/codex-mcp-setup-guide.md` 하단 |

> `/codex` 스킬 실행 시 Codex가 미설정이면 설정 가이드를 자동으로 안내한다.

---

## 라이센스

MIT
