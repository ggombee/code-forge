# code-forge

프로젝트 스택에 맞는 에이전트, 스킬, 규칙을 자동으로 제공하는 Claude Code 플러그인.
설치 후 `/setup` 한 번이면 프로젝트에 맞는 CLAUDE.md + AGENTS.md가 자동 생성되고, 14개 에이전트와 17개 스킬이 바로 동작한다.

## 설치

```bash
# 마켓플레이스 등록 (최초 1회) → 설치
claude plugin marketplace add https://github.com/ggombee/forge-market.git
claude plugin install code-forge
```

또는 로컬: `claude --plugin-dir /path/to/code-forge`

설치 후 `/setup` 실행 → 상세 가이드: README.md 참조

## 대장간 체계

인지적 도제이론(Cognitive Apprenticeship) 기반 대장간 메타포:

| 이름 | 역할 | 위치 |
|------|------|------|
| **Forge** (대장간) | 전체 플랫폼 | code-forge |
| **Smith** (대장장이) | 에이전트 빌드 (STATE+ACT → 컴파일) | `plugins/smith/` |
| **Anvil** (작업대) | 사용자 인터페이스 | CLI, 스킬, 커맨드 |
| **Whetstone** (숫돌) | 코딩 실력 연마 | [coding-practice](https://github.com/ggombee/coding-practice) (별도 레포) |
| **Assayer** (감정사) | 테스트 생성/검증 | `agents/assayer.md` |
| **Bellows** (풀무) | 사용량 로깅 | `hooks/bellows-log.sh` |
| **Blueprint** (설계도) | 사고모델 + 규칙 | `rules/` |

## 이 플러그인의 역할

1. `/setup` → 스택 감지 → CLAUDE.md + AGENTS.md 자동 생성
2. 스택에 맞는 모듈(컨벤션)이 에이전트에 주입
3. `/smith-create-agent` → 프로젝트 전용 에이전트에 사고모델(Blueprint) 임베딩
4. `/setup --profile` → 프로젝트 코딩 스타일 분석 → `.claude/coding-profile.md` 생성

## 핵심 워크플로우

```
/start feature.md       → 분석 → 구현 → 검증 → 커밋 → PR (원큐)
/done                   → 이미 구현된 코드 검증 → 커밋 → PR
/bug-fix "에러 메시지"   → 2-3 옵션 → 선택 → 수정
/setup                  → 스택 감지 → CLAUDE.md + AGENTS.md 생성
/setup --profile        → 코딩 스타일 분석 → coding-profile.md 생성
```

## 에이전트 (14개, 4단계 권한)

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
| `code-reviewer` | sonnet | 코드 리뷰 (품질+보안) |
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
| `deep-executor` | sonnet | 자율적 심층 구현 |
| `assayer` | sonnet | 테스트 생성 (generate/tdd 모드) |
| `codex` | sonnet | Codex 페어 프로그래밍 (MCP/CLI 듀얼) |

### Smith 빌드타임 컴파일

프로젝트 전용 에이전트를 STATE(지식) + ACT(행동) 조합으로 정의하고 컴파일.
Blueprint(사고모델)가 인라인 임베딩되어 플러그인 없이도 핵심 규칙이 동작한다.

- 플러그인 에이전트: `agents/` (직접 편집)
- 프로젝트 전용: `/smith-create-agent` → `.agents/agents/` → `/smith-build --project` → `.claude/agents/`
- STATE/ACT 부품: `plugins/smith/agents/state/`, `plugins/smith/agents/act/`

## Hooks

| 이벤트 | 훅 | 동작 |
|--------|------|------|
| SessionStart | `session-init.sh`, `bellows-log.sh` | 세션 초기화 + 버전 체크 + 로깅 |
| PreToolUse Bash | `guard.sh` + prompt | 위험 명령 차단 |
| PreToolUse Write | `write-guard.sh` | .env/인증서/자격증명 파일 차단 |
| PreToolUse Write (SKILL.md) | `skill-dedup.sh` + prompt | 새 스킬 생성 시 기존 스킬과 중복 검사 |
| PostToolUse Edit\|Write | `lint-fix.sh` | 자동 ESLint --fix + Prettier |
| PostToolUse Agent\|Skill | `bellows-log.sh` | 사용 로깅 → ~/.code-forge/usage.jsonl |
| Stop | `quality-gate.sh`, `notify.sh` | ESLint + TypeScript 검증 + Mac 알림 |
| SubagentStop | `subagent-stop.sh` | 구현 에이전트 완료 시 tsc 검증 |
| PreCompact | `pre-compact.sh` | 컨텍스트 압축 전 상태 스냅샷 |
| PermissionRequest | `permission-guard.sh` | 권한 요청 검증 |

## quality-gate 확장 (v4.0)

`hooks/quality-gate.sh`는 Stop 훅에서 7블록 검증을 수행한다 (비차단, 항상 exit 0):

| # | 블록 | 조건 |
|---|------|------|
| 1 | ESLint + tsc | `node_modules/.bin/` 존재 시 |
| 2 | scope 체크 | `.claude/temp/plan.md` 있을 때 |
| 3 | test-trigger | 변경 파일 → 단위 TC 자동 실행 (`.policy/` 자동 탐색) |
| 4 | policy-sync-check | `.policy/` 있을 때 (문서-코드 동기화) |
| 5 | REFLECT flag | 실패 시 `.claude/state/reflect.flag` 생성 → 다음 세션 ADAPT 강제 |
| 6 | scope-type-check | opt-in `[type:tag]` 태그 기반 위반 감지 |
| 7 | design-refs 정리 | git clean 시 |

관찰 로그는 `.claude/state/quality.jsonl`에 append. 계약: `docs/contracts/state-schema.md`.

## State Layer (v4.0)

`.claude/state/` 하위 파일이 세션 간 영속 상태를 저장:

| 파일 | 역할 |
|------|------|
| `reflect.flag` | quality-gate 실패 시 다음 세션 ADAPT 강제 |
| `quality.jsonl` | 검증 이벤트 로그 (forge-glow 등 외부 도구 소비) |
| `notepad.md` | (옵션) 사용자 작업 메모 |
| `decisions.md` | (옵션) 설계 결정 누적 |

외부 도구는 파일 직독 금지. `bin/forge status --json` surface 경유 (Phase H 예정).

## 스킬 (19개 — v4.1)

### 핵심 워크플로우 (사용자 직접 호출)

| 스킬 | 용도 |
|------|------|
| `/start` | MD/Jira/텍스트 → 분석 → 구현 → 검증 → 커밋 → PR. `--auto` 비블로킹 |
| `/test` | 테스트 통합 진입점 (유닛/E2E/세팅 자동 라우팅) |
| `/cleanup` | 산출물 정리 (design-refs, test-results, .claude/state) |
| `/generate-test` | BDD 시나리오 기반 테스트 생성 (`/test`가 위임) |
| `/debate` | 교차 모델 토론 |
| `/research` | 구조화된 리서치 |
| `/setup` | 스택 감지 + CLAUDE.md + AGENTS.md 생성 |
| `/codex` | Codex 페어 프로그래밍 |

### 자동 호출 스킬 (user-invocable: false)

| 스킬 | 용도 |
|------|------|
| `/stats` | 사용량 통계 (관리자용) |
| `/setup-test` | 테스트 환경 초기 세팅 |
| `/setup-agent-teams` | Agent Teams 설정 |
| `/figma-to-code` | Figma 디자인 → 코드 변환 |
| `/crawler` | Playwright 크롤링 설계 |
| `/startup-validator` | 새 서비스 아이디어 검증 |
| `/gemini` | Gemini CLI 래퍼 |

### v4.0 폐지 스킬 (규칙/훅으로 흡수)

| 폐지 | 대체 |
|------|------|
| `/done` | `/start` + 시스템 프롬프트 커밋 절차 |
| `/quality` | hooks(lint-fix.sh + quality-gate.sh) 자동 실행 |
| `/bug-fix` | `thinking-model.md` GROUND "버그 수정 시 2-3 옵션 제시" 규칙 |
| `/refactor` | `thinking-model.md` GROUND "정책 보호 테스트 먼저" 규칙 |

## 모듈 (17개)

| 카테고리 | 모듈 |
|---------|------|
| Framework (Frontend) | `react-nextjs-pages`, `react-nextjs-app`, `react-spa` |
| Framework (Backend) | `python-fastapi`, `python-django`, `node-express`, `go-standard` |
| Design System | `mui`, `ant-design` |
| State | `jotai-tanstack`, `zustand-tanstack`, `redux-rtk` |
| Styling | `emotion`, `tailwind`, `styled-components` |
| Testing | `jest`, `vitest` |

## 프리셋

| 프리셋 | 조합 |
|--------|------|
| `standard` | Pages Router + Jotai + Emotion + Jest |
| `modern-stack` | MUI + App Router + Zustand + Tailwind + Vitest |
| `backend-api` | Node.js Express + Jest |

## 상세 규칙 (alwaysApply)

| 규칙 | 핵심 |
|------|------|
| `rules/thinking-model.md` | GROUND→APPLY→VERIFY→ADAPT 루프. 불변 제약 5가지. 가정 분류(A/B/C). |
| `rules/coding-standards.md` | 코딩 표준, 네이밍, 금지 패턴, import 순서 |
| `rules/build-guide.md` | React 패턴, Hook 규칙, TypeScript 패턴 |
| `rules/review-guide.md` | 설계 철학, 안티패턴, 성능 최적화 |
| `rules/candidate-profile.md` | 프로젝트 코딩 프로필 참조 규칙 |

## 멀티에이전트 협업

3개+ 에이전트 협업 시 Agent Teams 사용:

```
TeamCreate → 팀원 spawn → 병렬 작업 → shutdown → TeamDelete
```

가이드: `instructions/multi-agent/coordination-guide.md`

## v4.1 추가 (원격/관찰)

| 스킬 | 용도 |
|------|------|
| `/setup-channels` | Telegram/Discord Channels 셋업 (폰에서 원격 접근) |
| `/forge-status` | 상태 대시보드 (REFLECT flag + quality + state) |

### bin/forge CLI

외부 도구(forge-glow, CI, 슬랙봇)가 `.claude/state/`에 접근할 때 **직독 금지**. 대신:

```bash
$CLAUDE_PLUGIN_ROOT/bin/forge status --json   # JSON Schema v1
$CLAUDE_PLUGIN_ROOT/bin/forge version
```

계약: `docs/contracts/state-schema.md`.

### forge-glow 연동 (L3)

별도 플러그인: https://github.com/ggombee/forge-glow
- bellows-log v2 필드 (session_id, model, duration_ms, success) 소비
- `bin/forge status --json` surface 경유 (파일 직독 안 함)
