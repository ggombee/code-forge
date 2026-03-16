# ggombee-agents

Claude Code 플러그인. 프로젝트 스택에 맞는 에이전트, 스킬, 규칙을 자동 제공한다.

## 동작 방식

1. `/setup` → 프로젝트 스택 감지/선택 → `profile.json` + preset 기반 `CLAUDE.md` 자동 생성
2. 스택에 맞는 모듈(컨벤션)이 에이전트에 주입됨

## 에이전트 (21개)

`agents/` 디렉토리의 심링크를 통해 활성화. VAS on/off에 따라 소스가 전환된다.

### 분석 전용 (READ-ONLY)

| 에이전트 | 모델 | 용도 |
|---------|------|------|
| `explore` | haiku | 코드베이스 빠른 탐색 |
| `analyst` | opus | 요구사항 분석, 누락/엣지 케이스 발견 |
| `architect` | opus | 아키텍처 분석, 설계 자문 |
| `researcher` | sonnet | 외부 문서/라이브러리 조사 |
| `code-reviewer` | sonnet | 코드 리뷰 (품질+보안) + 패턴 학습 |
| `refactor-advisor` | sonnet | 리팩토링 전략 분석 |
| `vision` | sonnet | 이미지/PDF/다이어그램 분석 |
| `critic` | sonnet | 계획/구현 OKAY/REJECT 판정 |
| `planner` | sonnet | 전략적 계획 수립 |
| `security-reviewer` | sonnet | OWASP Top 10 기반 보안 스캔 |

### 수정 전문 (READ-WRITE)

| 에이전트 | 모델 | 용도 |
|---------|------|------|
| `lint-fixer` | haiku | ESLint/TypeScript 오류 자동 수정 |
| `build-fixer` | sonnet | 빌드/컴파일 오류 수정 |
| `testgen` | sonnet | 테스트 생성 (generate/tdd 모드) |
| `implementation-executor` | sonnet | 계획 기반 즉시 구현 |
| `deep-executor` | sonnet | 자율적 심층 구현 |
| `designer` | sonnet | UI/UX 디자인 설계 및 구현 |
| `document-writer` | sonnet | 기술 문서 작성 |
| `deployment-validator` | sonnet | 배포 전 검증 및 자동 수정 |

### 특수

| 에이전트 | 모델 | 용도 |
|---------|------|------|
| `codex` | sonnet | OpenAI Codex 페어 프로그래밍 (MCP opt-in) |
| `git-operator` | sonnet | Git 커밋/브랜치 관리 |
| `qa-tester` | sonnet | tmux 기반 CLI/서비스 테스팅 |

## 스킬

| 스킬 | 용도 |
|------|------|
| `/start` | 티켓 기반 작업 시작 (브랜치 생성, 컨텍스트 파악) |
| `/done` | 작업 완료 → 검증 → 커밋 → PR 생성 |
| `/setup` | 프로젝트 스택 세팅 (profile.json → CLAUDE.md) |
| `/generate-test` | BDD 시나리오 기반 테스트 자동 생성 |
| `/setup-test` | 테스트 환경 초기 세팅 (jest/vitest, MSW) |
| `/bug-fix` | 버그 분석 + 2-3가지 해결 옵션 |
| `/refactor` | 리팩토링 분석 + 정책 보호 테스트 |
| `/figma-to-code` | Figma 디자인 → 코드 변환 |
| `/debate` | 교차 모델 토론 |
| `/research` | 구조화된 리서치 + 마크다운 리포트 |
| `/docs-creator` | 문서 작성 가이드 |
| `/codex` | Codex 페어 프로그래밍 (MCP opt-in) |
| `/setup-notifier` | Mac 알림 설정 |
| `/crawler` | Playwright 기반 크롤링 흐름 설계 |
| `/elon-musk` | 제1원칙 사고법 문제 해결 |
| `/genius-thinking` | 10가지 인지 공식 + TRIZ/SCAMPER 아이디어 발상 |
| `/startup-validator` | Peter Thiel 7Q + YC PMF 스타트업 검증 |
| `/gemini` | Google Gemini CLI 래퍼 |
| `/version-update` | 시맨틱 버전 업데이트 + 커밋 |
| `/vas-activate` | VAS 에이전트 시스템 활성화 |
| `/vas-create-agent` | 프로젝트 분석 → 맞춤 에이전트 생성 |

## 모듈 시스템

| 카테고리 | 선택지 |
|---------|--------|
| Framework | `react-nextjs-pages` · `react-nextjs-app` · `react-spa` |
| Design System | `pds` · `mui` · `ant-design` |
| State | `jotai-tanstack` · `zustand-tanstack` · `redux-rtk` |
| Styling | `emotion` · `tailwind` · `styled-components` |
| Testing | `jest` · `vitest` |

### 프리셋

| 프리셋 | 조합 |
|--------|------|
| `partner-standard` | PDS + Pages Router + Jotai + Emotion + Jest |
| `modern-stack` | MUI + App Router + Zustand + Tailwind + Vitest |

## VAS (Vibe-Agent-System)

STATE(지식) + ACT(행동)을 분리하여 프로젝트에 최적화된 에이전트를 조합한다.

- **전환**: SessionStart 시 `session.sh`가 `agents/` 심링크를 자동 전환
- **설정**: `~/.claude/ggombee-agents.local.md` (글로벌) 또는 `.claude/ggombee-agents.local.md` (프로젝트, 우선)
- **프로젝트 전용**: `/vas-create-agent`로 `.agents/agents/`에 맞춤 에이전트 생성

## 멀티에이전트 협업

3개+ 에이전트 병렬 협업 시 Agent Teams 사용. 상세 가이드:

| 문서 | 용도 |
|------|------|
| `instructions/multi-agent/coordination-guide.md` | 병렬 실행, 모델 선택 |
| `instructions/multi-agent/execution-patterns.md` | 작업별 실행 패턴 |
| `instructions/multi-agent/agent-roster.md` | 에이전트 전체 목록 |

## 구조

```
ggombee-agents/
├── agents/              # 활성 에이전트 (심링크)
├── agents-default/      # 기본 에이전트 21개
├── plugins/vas/         # VAS 에이전트 시스템
├── skills/              # 슬래시 스킬 20개
├── modules/             # 스택별 컨벤션 14개
├── presets/             # 프리셋 조합
├── hooks/               # 이벤트 훅 (VAS 전환, 알림)
├── commands/            # 슬래시 커맨드
├── rules/               # 핵심 규칙
├── instructions/        # 멀티에이전트 가이드
└── docs/                # MCP 설정 가이드
```
