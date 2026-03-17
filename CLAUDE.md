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
├── agents/          (14개)      # 컴파일된 에이전트 (/vas-build로 생성)
├── plugins/
│   └── vas/                     # VAS (Vibe-Agent-System) 플러그인
│       ├── agents/
│       │   ├── _agents/ (14개)  # VAS 기본 instance (컴파일 소스)
│       │   ├── interface/       # 구조 정의 (state-agent, act-agent)
│       │   ├── state/           # STATE class (role, language, framework, ...)
│       │   └── act/             # ACT class (analysis, dev, quality, ops)
│       ├── skills/              # /vas-build, /vas-create-agent
│       └── rules/               # VAS 해석 규칙 (reference-only)
├── skills/          (20개)      # 슬래시 스킬 (/setup, /bug-fix 등)
├── modules/         (13개)      # 스택별 컨벤션 (framework, state, styling 등)
├── presets/         (2개)       # 프리셋 조합 (standard, modern-stack)
├── hooks/                       # 이벤트 훅 (Mac 알림: notify.sh)
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

`agents/`에 `/vas-build`로 컴파일된 에이전트. 4단계 권한 기반 분류:

### READ-ONLY — Read/Grep/Glob만

| 에이전트 | 모델 | 용도 |
|---------|------|------|
| `analyst` | opus | 요구사항 분석, 누락 사항 발견 |
| `architect` | opus | 아키텍처 분석, 설계 자문 |
| `refactor-advisor` | sonnet | 리팩토링 전략 분석 |
| `vision` | sonnet | 이미지/PDF/다이어그램 분석 |

### SHELL-ACCESS — + Bash (Write/Edit 없음)

| 에이전트 | 모델 | 용도 | @참조 |
|---------|------|------|------|
| `scout` | haiku | 코드베이스 빠른 탐색 | parallel-execution |
| `code-reviewer` | sonnet | 코드 리뷰 (품질+보안) + 패턴 학습 | parallel-execution |
| `git-operator` | sonnet | Git 커밋/브랜치 관리 | — |
| `researcher` | sonnet | 외부 문서/라이브러리 조사 | — |

### EDIT-ONLY — + Edit (Write 없음)

| 에이전트 | 모델 | 용도 | @참조 |
|---------|------|------|------|
| `lint-fixer` | haiku | ESLint/TypeScript 오류 자동 수정 | coding-standards |
| `build-fixer` | sonnet | 빌드/컴파일 오류 수정 | coding-standards |

### READ-WRITE-FULL — Write 포함 전체

| 에이전트 | 모델 | 용도 | @참조 |
|---------|------|------|------|
| `implementor` | sonnet | 계획 기반 즉시 구현 | parallel-execution + coding-standards |
| `deep-executor` | sonnet | 자율적 심층 구현 + Ralph Loop | parallel-execution + coding-standards |
| `testgen` | sonnet | 테스트 생성 (generate/tdd 모드) | parallel-execution + coding-standards |
| `codex` | sonnet | Codex 페어 프로그래밍 (MCP/CLI 듀얼) | parallel-execution + coding-standards |

### VAS 빌드타임 컴파일

VAS(Vibe-Agent-System)는 STATE(지식) + ACT(행동) 조합으로 에이전트를 정의하는 시스템이다. `/vas-build` 스킬이 VAS 인스턴스를 정적 .md 파일로 컴파일한다.

- VAS 인스턴스 소스: `plugins/vas/agents/_agents/`
- 컴파일 출력: `agents/` (Claude Code 네이티브 포맷)
- 빌드 매니페스트: `agents/.vas-build-manifest.json`

#### 프로젝트 전용 에이전트

`/vas-create-agent`로 프로젝트를 분석하여 `.agents/agents/`에 전용 VAS 인스턴스를 생성하고 `/vas-build --project`로 `.claude/agents/`에 컴파일한다.

## 스킬 (20개)

### 기본 스킬

| 스킬 | 용도 |
|------|------|
| `/setup` | 프로젝트 스택 세팅 (profile.json → CLAUDE.md 자동 생성) |
| `/generate-test` | BDD 시나리오 기반 테스트 코드 자동 생성 |
| `/setup-test` | 테스트 환경 초기 세팅 (jest/vitest, MSW 등) |
| `/debate` | 교차 모델 토론으로 구현 방향 결정 |
| `/bug-fix` | 버그 분석 후 2-3가지 해결 옵션 제시 |
| `/refactor` | 리팩토링 분석 + 정책 보호 테스트 |
| `/figma-to-code` | Figma 디자인 → 코드 변환 |
| `/docs-creator` | 문서 작성 가이드 |
| `/codex` | Codex 페어 프로그래밍 (MCP opt-in) |
| `/setup-notifier` | Mac 알림 설정 (승인 요청 시 배너 알림) |
| `/setup-agent-teams` | Agent Teams 환경 설정 (Claude Max 전용) |
| `/crawler` | Playwright 기반 크롤링 흐름 설계 |
| `/elon-musk` | 제1원칙 사고법 문제 해결 |
| `/gemini` | Google Gemini CLI 래퍼 |
| `/genius-thinking` | 10가지 인지 공식 + TRIZ/SCAMPER 아이디어 발상 |
| `/research` | 구조화된 리서치 + 마크다운 리포트 |
| `/startup-validator` | Peter Thiel 7Q + YC PMF 스타트업 검증 |
| `/version-update` | 시맨틱 버전 업데이트 + 커밋 |

### VAS 스킬

| 스킬 | 용도 |
|------|------|
| `/vas-build` | VAS 인스턴스를 정적 .md로 컴파일 (전체/프로젝트/검증) |
| `/vas-create-agent` | 프로젝트 분석 → VAS instance 생성 → 자동 빌드 |

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
