# ggombee-agents

> Claude Code 플러그인 — 프로젝트 스택에 맞는 에이전트, 스킬, 컨벤션을 자동 제공

## Quick Start

```bash
# 설치
claude plugin install ggombee/ggombee-agents

# 프로젝트 스택 세팅
/setup

# 작업 시작 → 완료
/start TICKET-123
/done
```

## 핵심 기능

| 기능 | 설명 |
|------|------|
| `/setup` | 프로젝트 스택 자동 감지 → 규칙 적용 |
| `/start` → `/done` | 브랜치 생성 → 구현 → 검증 → PR 한 번에 |
| `/generate-test` | BDD 시나리오 기반 테스트 자동 생성 |
| `/bug-fix` | 버그 분석 + 2-3가지 해결 옵션 제시 |
| `/figma-to-code` | Figma 디자인 → 코드 변환 |
| **21개 전문 에이전트** | 분석/구현/검증 병렬 수행 |
| **VAS** | STATE+ACT 조합으로 프로젝트 맞춤 에이전트 생성 |

## 에이전트 (21개)

### 분석 전용 (READ-ONLY)

| 에이전트 | 모델 | 역할 |
|---------|------|------|
| `explore` | haiku | 코드베이스 탐색 |
| `analyst` | opus | 요구사항 분석, 엣지 케이스 발견 |
| `architect` | opus | 아키텍처 분석, 설계 자문 |
| `researcher` | sonnet | 외부 문서/라이브러리 조사 |
| `code-reviewer` | sonnet | 코드 리뷰 (품질+보안) |
| `refactor-advisor` | sonnet | 리팩토링 전략 |
| `vision` | sonnet | 이미지/PDF 분석 |
| `critic` | sonnet | 계획/구현 OKAY/REJECT 판정 |
| `planner` | sonnet | 전략적 계획 수립 |
| `security-reviewer` | sonnet | 보안 취약점 탐지 |

### 수정 전문 (READ-WRITE)

| 에이전트 | 모델 | 역할 |
|---------|------|------|
| `lint-fixer` | haiku | ESLint/TypeScript 오류 수정 |
| `build-fixer` | sonnet | 빌드/컴파일 오류 수정 |
| `testgen` | sonnet | 테스트 코드 생성 (generate/tdd) |
| `implementation-executor` | sonnet | 계획 기반 즉시 구현 |
| `deep-executor` | sonnet | 자율적 심층 구현 |
| `designer` | sonnet | UI/UX 디자인 설계 및 구현 |
| `document-writer` | sonnet | 기술 문서 작성 |
| `deployment-validator` | sonnet | 배포 전 검증 및 수정 |

### 특수

| 에이전트 | 모델 | 역할 |
|---------|------|------|
| `codex` | sonnet | OpenAI Codex 협업 (MCP opt-in) |
| `git-operator` | sonnet | Git 커밋/브랜치 관리 |
| `qa-tester` | sonnet | tmux 기반 CLI/서비스 테스팅 |

## 스킬 (20개)

### 워크플로우
`/start` · `/done` · `/setup`

### 코드 생성/수정
`/generate-test` · `/setup-test` · `/bug-fix` · `/refactor` · `/figma-to-code`

### 분석/사고
`/debate` · `/research` · `/elon-musk` · `/genius-thinking` · `/startup-validator`

### 도구
`/docs-creator` · `/codex` · `/setup-notifier` · `/crawler` · `/gemini` · `/version-update`

### VAS
`/vas-activate` · `/vas-create-agent`

## 모듈 시스템

프로젝트 스택에 맞는 컨벤션 자동 적용:

| 카테고리 | 선택지 |
|---------|--------|
| Framework | `react-nextjs-pages` · `react-nextjs-app` · `react-spa` |
| Design System | `pds` · `mui` · `ant-design` |
| State | `jotai-tanstack` · `zustand-tanstack` · `redux-rtk` |
| Styling | `emotion` · `tailwind` · `styled-components` |
| Testing | `jest` · `vitest` |

### 프리셋

```json
// .claude/profile.json
{ "preset": "partner-standard" }
```

| 프리셋 | 조합 |
|--------|------|
| `partner-standard` | PDS + Pages Router + Jotai + Emotion + Jest |
| `modern-stack` | MUI + App Router + Zustand + Tailwind + Vitest |

## VAS (Vibe-Agent-System)

STATE(지식) + ACT(행동)을 분리하여 프로젝트에 최적화된 에이전트를 조합하는 시스템.

```
# 활성화
/vas-activate

# 프로젝트 전용 에이전트 생성
/vas-create-agent
```

설정 파일로 자동 활성화:
```yaml
# ~/.claude/ggombee-agents.local.md (글로벌)
# .claude/ggombee-agents.local.md (프로젝트 — 우선)
---
vas:
  enabled: true
---
```

## 구조

```
ggombee-agents/
├── agents/              # 활성 에이전트 (심링크 — VAS on/off 전환)
├── agents-default/      # 기본 에이전트 21개
├── plugins/vas/         # VAS 에이전트 시스템
│   ├── agents/          #   STATE/ACT 템플릿 + 기본 인스턴스
│   ├── skills/          #   /vas-activate, /vas-create-agent
│   └── rules/           #   VAS 해석 규칙
├── skills/              # 슬래시 스킬 20개
├── modules/             # 스택별 컨벤션 14개
├── presets/             # 프리셋 조합
├── hooks/               # 이벤트 훅 (VAS 전환, 알림)
├── commands/            # 슬래시 커맨드
├── rules/               # 핵심 규칙 (작업 절차, 코딩 표준)
├── instructions/        # 멀티에이전트 협업 가이드
└── docs/                # MCP 설정 가이드
```

## MCP 연동 (opt-in)

기본 기능은 MCP 없이 모두 사용 가능. 추가 연동:

| MCP | 용도 |
|-----|------|
| Codex | `/codex` 페어 프로그래밍 |
| Figma | `/figma-to-code` 디자인 데이터 |
| Atlassian | Jira/Confluence 연동 |

> `/codex` 실행 시 미설정이면 자동 설정 가이드 안내

## License

MIT
