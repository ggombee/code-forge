# AGENTS.md — code-forge Agent Instructions

이 파일은 AAIF(Agent Architecture Instruction Format) 표준에 따라 작성되었다.
AI 에이전트가 이 저장소에서 작업할 때 반드시 준수해야 할 규칙을 정의한다.

---

## 프로젝트 구조 개요

```
code-forge/
├── agents/          # 컴파일된 에이전트 .md (직접 수정 금지 — smith-build 사용)
├── docs/            # 설계 원칙, 가이드 문서
├── hooks/           # Claude Code 훅 스크립트
├── instructions/    # 멀티에이전트 협업 가이드
├── modules/         # 스택별 컨벤션 모듈
├── plugins/smith/   # Smith 빌드 시스템 (에이전트 소스)
├── presets/         # 스택 프리셋 (standard, modern-stack)
├── rules/           # 사고 모델 + 코딩 표준 (alwaysApply)
├── skills/          # 스킬 커맨드 (/start, /done 등)
├── CLAUDE.md        # 플러그인 메인 설명서
└── AGENTS.md        # 이 파일
```

---

## 설계 원칙

이 플러그인을 수정/확장할 때 `docs/design-principles.md`를 반드시 참조한다.
모든 변경은 설계 원칙에 위배되지 않아야 한다.

---

## 에이전트 수정 규칙

### 플러그인 에이전트 (`agents/`)

`agents/` 파일은 직접 편집한다. Smith 빌드 불필요.

### 프로젝트 전용 에이전트

```
1. /code-forge:smith-create-agent → .agents/agents/ 에 생성 (STATE+ACT 조합, setup에서 자동 호출됨)
2. /code-forge:smith-build --project → .claude/agents/ 컴파일
```

Smith 빌드는 프로젝트 에이전트 전용. STATE/ACT 부품은 `plugins/smith/agents/state/`, `plugins/smith/agents/act/`에 있다.

---

## 에이전트 목록 (14개, 4단계 권한)

### READ-ONLY (Read/Grep/Glob만 허용)

| 에이전트 | 모델 | 용도 |
|---------|------|------|
| `analyst` | opus | 요구사항 분석, 누락 사항 발견 |
| `architect` | opus | 아키텍처 분석, 설계 자문 |
| `refactor-advisor` | sonnet | 리팩토링 전략 분석 |
| `vision` | sonnet | 이미지/PDF/다이어그램 분석 |

### SHELL-ACCESS (+ Bash, Write/Edit 없음)

| 에이전트 | 모델 | 용도 |
|---------|------|------|
| `scout` | haiku | 코드베이스 빠른 탐색 |
| `code-reviewer` | sonnet | 코드 리뷰 (품질+보안) |
| `git-operator` | sonnet | Git 커밋/브랜치 관리 |
| `researcher` | sonnet | 외부 문서/라이브러리 조사 |

### EDIT-ONLY (+ Edit, Write 없음)

| 에이전트 | 모델 | 용도 |
|---------|------|------|
| `lint-fixer` | haiku | ESLint/TypeScript 오류 자동 수정 |
| `build-fixer` | sonnet | 빌드/컴파일 오류 수정 |

### READ-WRITE-FULL (Write 포함 전체)

| 에이전트 | 모델 | 용도 |
|---------|------|------|
| `implementor` | sonnet | 계획 기반 즉시 구현 |
| `deep-executor` | sonnet | 자율적 심층 구현 |
| `assayer` | sonnet | 테스트 생성 (generate/tdd 모드) |
| `codex` | sonnet | Codex 페어 프로그래밍 (MCP/CLI 듀얼) |

---

## 스킬 (17개)

### 사용자 직접 호출

| 커맨드 | 동작 |
|--------|------|
| `/start` | MD 또는 텍스트 → 분석 → 구현 → 검증 → 커밋 → PR |
| `/done` | 구현 완료 후 검증 → 커밋 → PR |
| `/bug-fix` | 버그 분석 후 2-3가지 옵션 제시 |
| `/refactor` | 리팩토링 + 정책 보호 테스트 |
| `/generate-test` | BDD 시나리오 기반 테스트 생성 |
| `/debate` | 교차 모델 토론 |
| `/research` | 구조화된 리서치 |
| `/setup` | 스택 감지 + CLAUDE.md + AGENTS.md 생성 |
| `/codex` | Codex 페어 프로그래밍 |

### 자동 호출 (user-invocable: false)

| 커맨드 | 동작 |
|--------|------|
| `/quality` | 포맷 → 린트 → 타입 체크 (훅 백업용) |
| `/stats` | 사용량 통계 (관리자용) |
| `/setup-test` | 테스트 환경 초기 세팅 |
| `/setup-agent-teams` | Agent Teams 설정 |
| `/figma-to-code` | Figma 디자인 → 코드 변환 |
| `/crawler` | Playwright 크롤링 설계 |
| `/startup-validator` | 새 서비스 아이디어 검증 |
| `/gemini` | Gemini CLI 래퍼 |

---

## Hooks

| 이벤트 | 스크립트 | 동작 |
|--------|---------|------|
| `SessionStart` | `session-init.sh`, `bellows-log.sh` | 세션 초기화 + 버전 체크 + 로깅 |
| `PreToolUse Bash` | `guard.sh` + prompt | 위험 명령 차단 |
| `PreToolUse Write` | `write-guard.sh` | .env/인증서/자격증명 파일 차단 |
| `PreToolUse Write (SKILL.md)` | `skill-dedup.sh` + prompt | 새 스킬 생성 시 중복 검사 |
| `PostToolUse Edit\|Write` | `lint-fix.sh` | 자동 ESLint --fix + Prettier |
| `PostToolUse Agent\|Skill` | `bellows-log.sh` | 사용 로깅 → ~/.code-forge/usage.jsonl |
| `Stop` | `quality-gate.sh`, `notify.sh` | ESLint + TypeScript 검증 + Mac 알림 |
| `SubagentStop` | `subagent-stop.sh` | 구현 에이전트 완료 시 tsc 검증 |
| `PreCompact` | `pre-compact.sh` | 컨텍스트 압축 전 상태 스냅샷 |
| `PermissionRequest` | `permission-guard.sh` | 권한 요청 검증 |

---

## 금지 작업

| 금지 | 이유 |
|------|------|
| `agents/` 직접 수정 | Smith 빌드 출력물 — 다음 컴파일 시 덮어씌워짐 |
| `hooks/hooks.json` 수동 수정 후 검증 생략 | JSON 파싱 오류로 훅 전체 비활성화됨 |
| `rules/` 파일 삭제 | `alwaysApply` 규칙 — 모든 에이전트 동작에 영향 |
| `presets/` 스키마 변경 | `/setup` 스킬 파싱 오류 유발 |
| 민감한 파일(.env, credentials) 커밋 | `write-guard.sh`가 차단하지만 직접 커밋은 차단 안 됨 |

---

## 규칙 (alwaysApply)

| 파일 | 적용 범위 |
|------|----------|
| `rules/thinking-model.md` | GROUND→APPLY→VERIFY→ADAPT 루프. 불변 제약 5가지. 가정 분류(A/B/C). |
| `rules/coding-standards.md` | 코딩 표준, 네이밍, 금지 패턴, import 순서 |
| `rules/build-guide.md` | React 패턴, Hook 규칙, TypeScript 패턴 |
| `rules/review-guide.md` | 설계 철학, 안티패턴, 성능 최적화 |
| `rules/candidate-profile.md` | 프로젝트 코딩 프로필 참조 규칙 |

---

## 멀티에이전트 협업

3개 이상 에이전트 협업 시 Agent Teams 사용:

```
TeamCreate → 팀원 spawn → 병렬 작업 → shutdown → TeamDelete
```

상세 가이드: `instructions/multi-agent/coordination-guide.md`
