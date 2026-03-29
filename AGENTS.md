# AGENTS.md — code-forge Agent Instructions

이 파일은 AAIF(Agent Architecture Instruction Format) 표준에 따라 작성되었다.
AI 에이전트가 이 저장소에서 작업할 때 반드시 준수해야 할 규칙을 정의한다.

---

## 프로젝트 구조 개요

```
code-forge/
├── agents/          # 컴파일된 에이전트 .md (직접 수정 금지 — smith-build 사용)
├── hooks/           # Claude Code 훅 스크립트
├── instructions/    # 멀티에이전트 협업 가이드
├── modules/         # 스택별 컨벤션 모듈
├── plugins/smith/   # Smith 빌드 시스템 (에이전트 소스)
│   └── agents/_agents/  # 에이전트 인스턴스 소스 (STATE + ACT)
├── presets/         # 스택 프리셋 (standard, modern-stack)
├── rules/           # 사고 모델 + 코딩 표준 (alwaysApply)
├── skills/          # 스킬 커맨드 (/start, /done 등)
├── CLAUDE.md        # 플러그인 메인 설명서
└── AGENTS.md        # 이 파일
```

---

## 에이전트 수정 규칙

**`agents/` 디렉토리를 직접 수정하지 말 것.**

`agents/` 파일은 Smith 빌드 시스템이 컴파일한 출력물이다.
소스는 `plugins/smith/agents/_agents/`에 있다.

에이전트를 수정하려면:

```
1. plugins/smith/agents/_agents/<agent-name>/ 소스 수정
2. /smith-build 실행 → agents/ 재컴파일
```

프로젝트 전용 에이전트를 만들려면:

```
1. /smith-create-agent → .agents/agents/ 에 생성
2. /smith-build --project → .agents/compiled/ 컴파일
```

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
| `deep-executor` | sonnet | 자율적 심층 구현 + Ralph Loop |
| `assayer` | sonnet | 테스트 생성 (generate/tdd 모드) |
| `codex` | sonnet | Codex 페어 프로그래밍 (MCP/CLI 듀얼) |

---

## 스킬 커맨드 (20개)

### 워크플로우

| 커맨드 | 동작 |
|--------|------|
| `/start` | MD 또는 텍스트 → 분석 → 구현 → 검증 → 커밋 → PR |
| `/done` | 구현 완료 후 검증 → 커밋 → PR |
| `/quality` | 포맷 → 린트 → 타입 체크 + 오류 자동 수정 |
| `/stats` | Bellows 사용량 통계 |

### 구현

| 커맨드 | 동작 |
|--------|------|
| `/bug-fix` | 버그 분석 후 2-3가지 옵션 제시 |
| `/refactor` | 리팩토링 + 정책 보호 테스트 |
| `/generate-test` | BDD 시나리오 기반 테스트 생성 |
| `/setup-test` | 테스트 환경 초기 세팅 |
| `/figma-to-code` | Figma 디자인 → 코드 변환 |

### 분석

| 커맨드 | 동작 |
|--------|------|
| `/debate` | 교차 모델 토론 |
| `/research` | 구조화된 리서치 |
| `/elon-musk` | 제1원칙 사고법 |
| `/genius-thinking` | TRIZ/SCAMPER 아이디어 발상 |
| `/startup-validator` | 스타트업 검증 |
| `/crawler` | Playwright 크롤링 설계 |

### 설정

| 커맨드 | 동작 |
|--------|------|
| `/setup` | 스택 감지 + CLAUDE.md 생성 + 기능 설정 |
| `/setup-agent-teams` | Agent Teams 설정 |

### 유틸 + Smith

| 커맨드 | 동작 |
|--------|------|
| `/version-update` | 시맨틱 버전 업데이트 |
| `/codex` | Codex 페어 프로그래밍 |
| `/gemini` | Gemini CLI 래퍼 |
| `/smith-build` | Smith 인스턴스 컴파일 |
| `/smith-create-agent` | 프로젝트 전용 에이전트 생성 |

---

## Hooks

| 이벤트 | 스크립트 | 동작 |
|--------|---------|------|
| `SessionStart` | `session-init.sh`, `bellows-log.sh` | 세션 초기화 + 사용 로깅 |
| `PreToolUse Bash` | `guard.sh` | 위험 명령 차단 (rm -rf, force push 등) |
| `PreToolUse Write` | `write-guard.sh` | .env/인증서/자격증명 파일 생성 차단 |
| `PostToolUse Edit\|Write\|MultiEdit` | `lint-fix.sh` | 자동 ESLint --fix + Prettier |
| `PostToolUse Agent\|Skill` | `bellows-log.sh` | Agent/Skill 사용 로깅 → ~/.code-forge/usage.jsonl |
| `Stop` | `quality-gate.sh`, `notify.sh` | 변경 파일 ESLint + TypeScript 검증 + Mac 알림 |
| `SubagentStop` | `subagent-stop.sh` | implementor/deep-executor/build-fixer 완료 시 tsc 검증 |
| `PreCompact` | `pre-compact.sh` | 컨텍스트 압축 전 브랜치·미커밋·스테이지 파일 스냅샷 주입 |
| `PermissionRequest` | `permission-guard.sh` | 권한 요청 검증 |

---

## 테스트 및 검증 커맨드

이 저장소는 플러그인 자체이므로 별도의 빌드/테스트 파이프라인이 없다.
아래 방법으로 플러그인 구성 요소를 검증한다.

```bash
# hooks.json 유효성 검증
cat /Users/ggombee/Desktop/ai/code-forge/hooks/hooks.json | python3 -m json.tool

# 훅 스크립트 실행 권한 확인
ls -la /Users/ggombee/Desktop/ai/code-forge/hooks/*.sh

# smith-build로 에이전트 컴파일 검증
# /smith-build (Claude Code 내에서 실행)

# 플러그인 로컬 로드 테스트
# claude --plugin-dir /Users/ggombee/Desktop/ai/code-forge
```

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

코드 작업 시 아래 규칙이 자동 적용된다:

| 파일 | 적용 범위 |
|------|----------|
| `rules/thinking-model.md` | GROUND→APPLY→VERIFY→ADAPT 루프. S/M/L 규모 분기. 불변 제약 5가지. |
| `rules/coding-standards.md` | 코딩 표준, 네이밍, 금지 패턴, import 순서 |
| `rules/build-guide.md` | React 패턴, Hook 규칙, TypeScript 패턴 |
| `rules/review-guide.md` | 설계 철학, 안티패턴, 성능 최적화, 리팩토링 패턴 |

---

## 멀티에이전트 협업

3개 이상 에이전트 협업 시 Agent Teams 사용:

```
TeamCreate → 팀원 spawn → 병렬 작업 → shutdown → TeamDelete
```

상세 가이드: `instructions/multi-agent/coordination-guide.md`
