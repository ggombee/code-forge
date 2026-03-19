# code-forge

Claude Code 플러그인. 프로젝트 스택에 맞는 에이전트, 스킬, 규칙을 자동으로 제공한다.

## 이 플러그인의 역할

1. `/setup` 실행 → 프로젝트 스택 감지 또는 선택
2. `profile.json` + preset 기반으로 `CLAUDE.md` 자동 생성
3. 스택에 맞는 모듈(컨벤션)이 에이전트에 주입됨

## 플러그인 구조

```
code-forge/
├── .claude-plugin/plugin.json   # 플러그인 매니페스트
├── agents/          (14개)      # 컴파일된 에이전트 (/anvil-build로 생성)
├── plugins/
│   └── anvil/                   # Anvil (Agent Anvil System) 플러그인
│       ├── agents/
│       │   ├── _agents/ (15개)  # Anvil 기본 instance (컴파일 소스)
│       │   ├── interface/       # 구조 정의 (state-agent, act-agent)
│       │   ├── state/           # STATE class (role, language, framework, ...)
│       │   └── act/             # ACT class (analysis, dev, quality, ops)
│       ├── skills/              # /anvil-build, /anvil-create-agent
│       └── rules/               # Anvil 해석 규칙 (reference-only)
├── skills/          (22개)      # 슬래시 스킬 (/start, /done, /setup 등)
├── modules/         (13개)      # 스택별 컨벤션 (framework, state, styling 등)
├── presets/         (2개)       # 프리셋 조합 (standard, modern-stack)
├── hooks/                       # 이벤트 훅 (guard.sh, lint-fix.sh, notify.sh)
├── commands/                    # 슬래시 커맨드 (git-all, git-merge, git-session, lint-fix, pre-deploy)
├── rules/                       # 핵심 규칙 (thinking-model, coding-standards)
├── instructions/                # 멀티에이전트 협업 가이드
└── docs/                        # 참고 문서
```

## 작업 절차 (thinking-model)

모든 코드 작업에 적용되는 루프:

```
GROUND → APPLY → VERIFY
  ↑                 ↓
  └─── ADAPT ←──────┘ (실패 시만)
```

- **GROUND**: 대상 파일 Read + 패턴 Grep → 규모(S/M/L) 판단
- **APPLY**: 관찰한 패턴으로 구현. 불변 제약(읽기 우선 / 패턴 준수 / 정책 보존 / 최소 변경 / 스코프 준수) 준수
- **VERIFY**: `tsc --noEmit` + lint + 테스트 실행

## 에이전트 시스템 (14개)

`agents/`에 `/anvil-build`로 컴파일된 에이전트. 4단계 권한 기반 분류:

### READ-ONLY — Read/Grep/Glob만

| 에이전트 | 모델 | 용도 |
|---------|------|------|
| `analyst` | opus | 요구사항 분석, 누락 사항 발견 |
| `architect` | opus | 아키텍처 분석, 설계 자문 |
| `refactor-advisor` | sonnet | 리팩토링 전략 분석 |
| `vision` | sonnet | 이미지/PDF/다이어그램 분석 |

### SHELL-ACCESS — + Bash (Write/Edit 없음)

| 에이전트 | 모델 | 용도 |
|---------|------|------|
| `scout` | haiku | 코드베이스 빠른 탐색 |
| `code-reviewer` | sonnet | 코드 리뷰 (품질+보안) + 패턴 학습 |
| `git-operator` | sonnet | Git 커밋/브랜치 관리 |
| `researcher` | sonnet | 외부 문서/라이브러리 조사 |

### EDIT-ONLY — + Edit (Write 없음)

| 에이전트 | 모델 | 용도 |
|---------|------|------|
| `lint-fixer` | haiku | ESLint/TypeScript 오류 자동 수정 |
| `build-fixer` | sonnet | 빌드/컴파일 오류 수정 |

### READ-WRITE-FULL — Write 포함 전체

| 에이전트 | 모델 | 용도 |
|---------|------|------|
| `implementor` | sonnet | 계획 기반 즉시 구현 |
| `deep-executor` | sonnet | 자율적 심층 구현 + Ralph Loop |
| `testgen` | sonnet | 테스트 생성 (generate/tdd 모드) |
| `codex` | sonnet | Codex 페어 프로그래밍 (MCP/CLI 듀얼) |

### Anvil 빌드타임 컴파일

Anvil(Agent Anvil System)은 STATE(지식) + ACT(행동) 조합으로 에이전트를 정의하는 시스템이다. `/anvil-build` 스킬이 Anvil 인스턴스를 정적 .md 파일로 컴파일한다.

- Anvil 인스턴스 소스: `plugins/anvil/agents/_agents/`
- 컴파일 출력: `agents/` (Claude Code 네이티브 포맷)
- 빌드 매니페스트: `agents/.anvil-build-manifest.json`

#### 프로젝트 전용 에이전트

`/anvil-create-agent`로 프로젝트를 분석하여 `.agents/agents/`에 전용 Anvil 인스턴스를 생성하고 `/anvil-build --project`로 `.claude/agents/`에 컴파일한다.

## Hooks

| 이벤트 | 훅 | 설명 |
|--------|------|------|
| `SessionStart` | `session-init.sh` | 플러그인 버전 체크 (hooks.json 참조) |
| `PostToolUse` | `lint-fix.sh` | Edit/Write 후 린트 자동 수정 (stub) |
| `PreToolUse` | `guard.sh` | Bash 실행 전 위험 명령 가드 (stub) |

> guard.sh, lint-fix.sh는 현재 stub 상태. v3.0에서 구현 예정.

## 스킬 (22개)

### 워크플로우

| 스킬 | 용도 |
|------|------|
| `/start` | MD 파일 또는 텍스트로 작업 정의 → 분석 → 구현 → 검증 → 커밋 → PR (원큐) |
| `/done` | 구현 완료 후 검증 → 테스트 → 커밋 → PR 생성 |
| `/commit` | staged 변경사항 분석 → 커밋 메시지 생성 → 커밋 |
| `/quality` | 포맷(Prettier) → 린트(ESLint) → 타입 체크(tsc) 순서로 실행 + 오류 자동 수정 |

### 구현

| 스킬 | 용도 |
|------|------|
| `/bug-fix` | 버그 분석 후 2-3가지 해결 옵션 제시 후 구현 |
| `/refactor` | 리팩토링 분석 + 정책 보호 테스트 |
| `/generate-test` | BDD 시나리오 기반 테스트 코드 자동 생성 |
| `/setup-test` | 테스트 환경 초기 세팅 (jest/vitest, MSW 등) |
| `/figma-to-code` | Figma 디자인 → 코드 변환 |

### 분석

| 스킬 | 용도 |
|------|------|
| `/debate` | 교차 모델 토론으로 구현 방향 결정 |
| `/elon-musk` | 제1원칙 사고법 문제 해결 |
| `/genius-thinking` | 10가지 인지 공식 + TRIZ/SCAMPER 아이디어 발상 |
| `/research` | 구조화된 리서치 + 마크다운 리포트 |
| `/startup-validator` | Peter Thiel 7Q + YC PMF 스타트업 검증 |
| `/crawler` | Playwright 기반 크롤링 흐름 설계 |

### 설정

| 스킬 | 용도 |
|------|------|
| `/setup` | 프로젝트 스택 세팅 (profile.json → CLAUDE.md 자동 생성) |
| `/setup-notifier` | Mac 알림 설정 (승인 요청 시 배너 알림) |
| `/setup-agent-teams` | Agent Teams 환경 설정 (Claude Max 전용) |

### 유틸

| 스킬 | 용도 |
|------|------|
| `/version-update` | 시맨틱 버전 업데이트 + 커밋 |
| `/docs-creator` | 문서 작성 가이드 |
| `/codex` | Codex 페어 프로그래밍 (MCP opt-in) |
| `/gemini` | Google Gemini CLI 래퍼 |

### Anvil

| 스킬 | 용도 |
|------|------|
| `/anvil-build` | Anvil 인스턴스를 정적 .md로 컴파일 (전체/프로젝트/검증) |
| `/anvil-create-agent` | 프로젝트 분석 → Anvil instance 생성 → 자동 빌드 |

## 모듈 시스템 (13개)

프로젝트 스택에 따라 해당 모듈의 컨벤션이 적용된다.

| 카테고리 | 사용 가능한 모듈 |
|---------|-----------------|
| Framework | `react-nextjs-pages`, `react-nextjs-app`, `react-spa` |
| Design System | `mui`, `ant-design` |
| State | `jotai-tanstack`, `zustand-tanstack`, `redux-rtk` |
| Styling | `emotion`, `tailwind`, `styled-components` |
| Testing | `jest`, `vitest` |

## 프리셋

| 프리셋 | 조합 |
|--------|------|
| `standard` | Pages Router + Jotai + Emotion + Jest |
| `modern-stack` | MUI + App Router + Zustand + Tailwind + Vitest |

## 멀티에이전트 협업

3개+ 에이전트 협업 시 Agent Teams 사용:

```
TeamCreate → 팀원 spawn → 병렬 작업 → shutdown → TeamDelete
```

상세 가이드:

| 문서 | 용도 |
|------|------|
| `instructions/multi-agent/coordination-guide.md` | 병렬 실행, 모델 선택 |
| `instructions/multi-agent/execution-patterns.md` | 작업별 실행 패턴 |
| `instructions/multi-agent/agent-roster.md` | 에이전트 전체 목록 |
