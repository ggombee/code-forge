# ggombee-agents

Claude Code 플러그인. 프로젝트 스택에 맞는 에이전트, 스킬, 규칙을 자동으로 제공한다.

## 이 플러그인의 역할

1. `/setup` 실행 → 프로젝트 스택 감지 또는 선택
2. `profile.json` + preset 기반으로 `CLAUDE.md` 자동 생성
3. 스택에 맞는 모듈(컨벤션)이 에이전트에 주입됨

## 플러그인 구조

```
ggombee-agents/
├── .claude-plugin/plugin.json   # 플러그인 매니페스트
├── agents/                      # 활성 에이전트 (심링크)
├── agents-default/    (14개)    # 기본 에이전트
├── plugins/
│   └── vas/                     # VAS (Vibe-Agent-System) 플러그인
│       ├── agents/
│       │   ├── _agents/ (14개)  # VAS 기본 instance
│       │   ├── interface/       # 구조 정의 (state-agent, act-agent)
│       │   ├── state/           # STATE class (role, language, framework, ...)
│       │   └── act/             # ACT class (analysis, dev, quality, ops)
│       ├── skills/              # /vas-activate, /vas-create-agent
│       └── rules/               # VAS 해석 규칙
├── skills/          (12개)      # 슬래시 스킬 (/start, /done 등)
├── modules/         (14개)      # 스택별 컨벤션 (framework, state, styling 등)
├── presets/         (2개)       # 프리셋 조합 (partner-standard, modern-stack)
├── hooks/                       # 이벤트 훅 (VAS 전환, lint 자동 수정, 위험 명령 가드 등)
├── commands/                    # 슬래시 커맨드
├── rules/                       # 핵심 규칙 (thinking-model, coding-standards)
├── instructions/                # 멀티에이전트 협업 가이드
└── docs/                        # 참고 문서
```

## 에이전트 시스템

### 기본 모드 (VAS off)

`agents-default/`의 14개 에이전트가 활성:

#### 분석 전용 (코드 수정 안 함)

| 에이전트 | 모델 | 용도 |
|---------|------|------|
| `explore` | haiku | 코드베이스 빠른 탐색 |
| `analyst` | opus | 요구사항 분석, 누락 사항 발견 |
| `architect` | opus | 아키텍처 분석, 설계 자문 |
| `researcher` | sonnet | 외부 문서/라이브러리 조사 |
| `code-reviewer` | sonnet | 코드 리뷰 (품질+보안) + 패턴 학습 |
| `refactor-advisor` | sonnet | 리팩토링 전략 분석 |
| `vision` | sonnet | 이미지/PDF/다이어그램 분석 |

#### 수정 전문 (코드 직접 수정)

| 에이전트 | 모델 | 용도 |
|---------|------|------|
| `lint-fixer` | haiku | ESLint/TypeScript 오류 자동 수정 |
| `build-fixer` | sonnet | 빌드/컴파일 오류 수정 |
| `testgen` | sonnet | 테스트 생성 (generate/tdd 모드) |
| `implementation-executor` | sonnet | 계획 기반 즉시 구현 |
| `deep-executor` | sonnet | 자율적 심층 구현 + Ralph Loop |

#### 특수

| 에이전트 | 모델 | 용도 |
|---------|------|------|
| `codex` | sonnet | Codex 페어 프로그래밍 (MCP/CLI 듀얼) |
| `git-operator` | sonnet | Git 커밋/브랜치 관리 |

### VAS 모드 (VAS on)

`plugins/vas/agents/_agents/`의 VAS instance가 활성. STATE(지식) + ACT(행동) 조합으로 정의된 에이전트.

#### 전환 메커니즘

- SessionStart 시 `session.sh`가 VAS 설정을 읽고 `agents/` 심링크를 전환
- VAS on → `agents/` 심링크가 `plugins/vas/agents/_agents/`를 가리킴
- VAS off → `agents/` 심링크가 `agents-default/`를 가리킴
- 모든 전환은 플러그인 내부에서 완결. 프로젝트 디렉토리를 건드리지 않음

#### 설정

```yaml
# ~/.claude/ggombee-agents.local.md (글로벌) 또는 .claude/ggombee-agents.local.md (프로젝트)
---
vas:
  enabled: true
---
```

프로젝트 설정이 글로벌 설정보다 우선.

#### 프로젝트 전용 에이전트

`/vas-create-agent`로 프로젝트의 `.agents/agents/`에 전용 instance를 생성할 수 있다. 프로젝트 전용 에이전트는 VAS 기본 에이전트보다 우선 적용된다.

## 스킬

### 기본 스킬

| 스킬 | 용도 |
|------|------|
| `/start` | 티켓 기반 작업 시작 (브랜치 생성, 컨텍스트 파악) |
| `/done` | 작업 완료 → 린트/빌드 검증 → 커밋 → PR 생성 |
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

### VAS 스킬

| 스킬 | 용도 |
|------|------|
| `/vas-activate` | VAS 에이전트 시스템 활성화 및 에이전트 로드 |
| `/vas-create-agent` | 프로젝트 분석 → VAS instance 에이전트 자동 생성 |

## 모듈 시스템

프로젝트 스택에 따라 해당 모듈의 컨벤션이 적용된다.

| 카테고리 | 사용 가능한 모듈 |
|---------|-----------------|
| Framework | `react-nextjs-pages`, `react-nextjs-app`, `react-spa` |
| Design System | `pds`, `mui`, `ant-design` |
| State | `jotai-tanstack`, `zustand-tanstack`, `redux-rtk` |
| Styling | `emotion`, `tailwind`, `styled-components` |
| Testing | `jest`, `vitest` |

## 프리셋

| 프리셋 | 조합 |
|--------|------|
| `partner-standard` | PDS + Pages Router + Jotai + Emotion + Jest |
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
