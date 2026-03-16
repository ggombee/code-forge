# ggombee-agents

프로젝트 스택에 맞는 에이전트, 스킬, 컨벤션을 조합하는 Claude Code 플러그인.

---

## 이 플러그인이 해주는 것

| 기능 | 설명 |
|------|------|
| **자동 스택 세팅** | `/setup` 한 번으로 프로젝트 스택(Framework, DS, State 등)에 맞는 규칙 자동 적용 |
| **작업 흐름 자동화** | `/start`로 작업 시작 → `/done`으로 검증/커밋/PR까지 한 번에 |
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
# 마켓플레이스 등록 (최초 1회)
/plugin marketplace add https://github.com/ggombee/ggombee-marketplace

# 플러그인 설치
claude plugin install ggombee-agents
```

로컬 개발 시:
```bash
claude --plugin-dir ./ggombee-agents
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
  "preset": "partner-standard"
}
```

### 2. 작업 시작

```
/start TICKET-123
```

브랜치 생성, 티켓 분석, 작업 계획 수립까지 자동.

### 3. 작업 완료

```
/done
```

린트/빌드 검증 → 테스트 → 커밋 → PR 생성까지 한 번에.

---

## VAS (Vibe-Agent-System)

STATE(지식)와 ACT(행동)를 분리하여 에이전트를 정의하는 시스템. 세션 시작 시 VAS 활성화 여부를 선택할 수 있다.

### 활성화

세션 시작 시 자동으로 질문하거나, 설정 파일로 미리 지정:

```yaml
# ~/.claude/ggombee-agents.local.md (글로벌) 또는 .claude/ggombee-agents.local.md (프로젝트)
---
vas:
  enabled: true
---
```

프로젝트 설정이 글로벌 설정보다 우선.

### VAS on/off 차이

| | VAS off | VAS on |
|---|---------|--------|
| 에이전트 소스 | `agents-default/` | `plugins/vas/agents/_agents/` |
| 에이전트 형식 | Claude Code 네이티브 | VAS instance (STATE + ACT) |
| 프로젝트 전용 | - | `/vas-create-agent`로 `.agents/agents/`에 생성 |

### 프로젝트 전용 에이전트

```
/vas-create-agent
```

프로젝트를 분석하여 `.agents/agents/`에 맞춤 에이전트를 생성한다. 프로젝트 전용 에이전트는 VAS 기본 에이전트보다 우선 적용된다.

### VAS 스킬

| 스킬 | 설명 |
|------|------|
| `/vas-activate` | VAS 에이전트 시스템 활성화 및 에이전트 로드 |
| `/vas-create-agent` | 프로젝트 분석 → VAS instance 에이전트 자동 생성 |

---

## 프리셋

| 프리셋 | 스택 |
|--------|------|
| `partner-standard` | PDS + Next.js Pages Router + Jotai + Emotion + Jest |
| `modern-stack` | MUI + Next.js App Router + Zustand + Tailwind + Vitest |

개별 모듈 직접 선택도 가능:

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

## 스킬 (14개)

### 작업 흐름

| 스킬 | 설명 |
|------|------|
| `/start` | 티켓 기반 작업 시작 (브랜치 생성, 컨텍스트 파악) |
| `/done` | 작업 완료 → 검증 → 커밋 → PR 생성 |
| `/setup` | 프로젝트 스택 자동 세팅 |

### 코드 생성/수정

| 스킬 | 설명 |
|------|------|
| `/generate-test` | BDD 시나리오 기반 테스트 코드 자동 생성 |
| `/bug-fix` | 버그 분석 후 2-3가지 해결 옵션 제시 |
| `/refactor` | 리팩토링 분석 + 정책 보호 테스트 |
| `/figma-to-code` | Figma 디자인 → 코드 변환 |

### 분석/토론

| 스킬 | 설명 |
|------|------|
| `/debate` | 교차 모델 토론으로 구현 방향 결정 |
| `/docs-creator` | 문서 작성 가이드 |

### 환경 설정

| 스킬 | 설명 |
|------|------|
| `/setup-test` | 테스트 환경 초기 세팅 (jest/vitest, MSW 등) |
| `/setup-notifier` | Mac 알림 설정 (승인 요청 시 배너 알림) |
| `/codex` | Codex 페어 프로그래밍 (미설정 시 자동 설정 가이드 안내) |

### VAS

| 스킬 | 설명 |
|------|------|
| `/vas-activate` | VAS 에이전트 시스템 활성화 및 에이전트 로드 |
| `/vas-create-agent` | 프로젝트 분석 → VAS instance 에이전트 자동 생성 |

---

## 에이전트 (14개)

### 분석 전용 — 코드를 수정하지 않고 분석만 수행

| 에이전트 | 용도 |
|---------|------|
| `explore` | 코드베이스 빠른 탐색, 파일 구조 파악 |
| `analyst` | 요구사항 분석, 누락된 질문/엣지 케이스 발견 |
| `architect` | 아키텍처 분석, 설계 자문 |
| `researcher` | 외부 문서/라이브러리 조사 |
| `code-reviewer` | 코드 리뷰 (품질 + 보안) + 패턴 학습 |
| `refactor-advisor` | 리팩토링 전략 분석 |
| `vision` | 이미지/PDF/다이어그램 분석 |

### 수정 전문 — 코드를 직접 수정

| 에이전트 | 용도 |
|---------|------|
| `lint-fixer` | ESLint/TypeScript 오류 자동 수정 |
| `build-fixer` | 빌드/컴파일 오류 수정 |
| `testgen` | 테스트 코드 생성 (generate/tdd 모드) |
| `implementor` | 계획 기반 즉시 구현 |
| `deep-executor` | 자율적 심층 구현 + Ralph Loop |
| `codex` | Codex 페어 프로그래밍 (MCP/CLI 듀얼 모드) |
| `git-operator` | Git 커밋/브랜치 관리 |

---

## 모듈 시스템 (14개)

프로젝트 스택에 따라 해당 모듈의 컨벤션이 자동 적용된다.

| 카테고리 | 모듈 |
|---------|------|
| Framework | `react-nextjs-pages`, `react-nextjs-app`, `react-spa` |
| Design System | `pds`, `mui`, `ant-design` |
| State | `jotai-tanstack`, `zustand-tanstack`, `redux-rtk` |
| Styling | `emotion`, `tailwind`, `styled-components` |
| Testing | `jest`, `vitest` |

---

## 플러그인 구조

```
ggombee-agents/
├── .claude-plugin/plugin.json    # 플러그인 매니페스트
├── agents/                       # 활성 에이전트 (심링크 — VAS on/off에 따라 전환)
├── agents-default/               # 기본 에이전트 14개
├── plugins/
│   └── vas/                      # VAS (Vibe-Agent-System)
│       ├── agents/
│       │   ├── _agents/          #   VAS 기본 instance 14개
│       │   ├── interface/        #   구조 정의 (state-agent, act-agent)
│       │   ├── state/            #   STATE class (role, language, framework, ...)
│       │   └── act/              #   ACT class (analysis, dev, quality, ops)
│       ├── skills/               #   /vas-activate, /vas-create-agent
│       └── rules/                #   VAS 해석 규칙
├── skills/                       # 스킬 12개
├── modules/                      # 스택 모듈 14개
├── presets/                      # 프리셋 (partner-standard, modern-stack)
├── hooks/                        # 이벤트 훅 (VAS 전환, lint 자동 수정, 알림 등)
├── commands/                     # 슬래시 커맨드
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
