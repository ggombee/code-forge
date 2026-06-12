# code-forge — 하니스 레퍼런스 (단일 소스)

> 에이전트/스킬/훅/상태/규칙 카탈로그의 **유일본**. CLAUDE.md와 AGENTS.md는 이 문서를 가리키는 포인터만 유지한다 (2026-06-12 H1/H2 context trim — 매 세션 자동 주입 부담 제거).
> 개수는 손으로 세지 않는다 — 산출 명령을 표기하고 디스크를 신뢰할 것.

---

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

---

## 에이전트 (산출: `ls agents/*.md | wc -l`, 4단계 권한)

> `model:` 핀은 비용 통제 수단 — 티어 별칭은 main 모델이 아니라 **해당 티어의 최신**으로 해석된다 (2026-06-11 실측, `docs/contracts/event-schema.md` §5).

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

프로젝트 전용 에이전트를 STATE(지식) + ACT(행동) 조합으로 정의하고 컴파일. Blueprint(사고모델)가 인라인 임베딩되어 플러그인 없이도 핵심 규칙이 동작한다.

- 플러그인 에이전트: `agents/` (직접 편집)
- 프로젝트 전용: `/code-forge:smith-create-agent` → `.agents/agents/` → `/code-forge:smith-build --project` → `.claude/agents/`
- STATE/ACT 부품: `plugins/smith/agents/state/`, `plugins/smith/agents/act/`

---

## 스킬 (산출: `ls skills/*/SKILL.md | wc -l` — 2026-06-12 디스크 기준 재생성)

> ⚠️ `/done` `/bug-fix` `/refactor` `/quality`는 **v4.0에서 폐지** — 규칙/훅으로 흡수됨. 대체 매핑은 [`docs/CATALOG.md`](CATALOG.md) 참조. 문서에 다시 추가하지 말 것.

### 사용자 직접 호출

| 스킬 | 용도 |
|------|------|
| `/start` | MD/Jira/텍스트 → 분석 → 구현 → 검증 → 커밋 → PR. `--auto` 비블로킹 |
| `/handoff` | 세션 핸드오프 — 중요 맥락 → progress.md 갱신 + 킥오프 프롬프트 클립보드 복사 |
| `/test` | 테스트 통합 진입점 (유닛/E2E/세팅 자동 라우팅) |
| `/e2e` | 화면 단위 E2E 자동화 (Figma/코드 → Playwright → Forge Loop) |
| `/setup-e2e` | Playwright E2E 환경 세팅 |
| `/cleanup` | 산출물 정리 (design-refs, test-results, .claude/state) |
| `/generate-test` | BDD 시나리오 기반 테스트 생성 (`/test`가 위임) |
| `/debate` | 교차 모델 토론 |
| `/research` | 구조화된 리서치 |
| `/setup` | 스택 감지 + CLAUDE.md + AGENTS.md 생성. `--profile`로 .candidate/profile.md 생성 |
| `/codex` | Codex 페어 프로그래밍 |
| `/voice` | Forge Voice — 손목 보호 음성 입력 셋업/관리 (`docs/voice-input.md`) |
| `/smith-create-agent` | 프로젝트 분석 → Smith 에이전트 생성 (setup이 자동 호출) |
| `/smith-build` | Smith 인스턴스 컴파일 → 플랫 .md |
| `/setup-channels` | Telegram/Discord Channels 셋업 (폰 원격 접근) |
| `/forge-status` | 상태 대시보드 (REFLECT flag + quality + state) |

### 자동 호출 (user-invocable: false)

| 스킬 | 용도 |
|------|------|
| `/stats` | 사용량 통계 (관리자용) |
| `/setup-test` | 테스트 환경 초기 세팅 |
| `/setup-agent-teams` | Agent Teams 설정 (Claude Max 전용) |
| `/figma-to-code` | Figma 디자인 → 코드 변환 |
| `/crawler` | Playwright 크롤링 설계 |
| `/startup-validator` | 새 서비스 아이디어 검증 |

폐지 스킬 / 모듈 17개 / 프리셋 → [`docs/CATALOG.md`](CATALOG.md)

---

## Hooks

| 이벤트 | 훅 | 동작 |
|--------|------|------|
| SessionStart | `session-init.sh`, `bellows-log.sh` | 세션 초기화 + 버전 체크 + 로깅 |
| PreToolUse Bash | `guard.sh` + prompt | 위험 명령 차단 |
| PreToolUse Write | `write-guard.sh` | .env/인증서/자격증명 파일 차단 (2026-06-11 stdin 수리) |
| PreToolUse Write (SKILL.md) | `skill-dedup.sh` + prompt | 새 스킬 생성 시 기존 스킬과 중복 검사 |
| PostToolUse Edit\|Write | `lint-fix.sh` | 자동 ESLint --fix + Prettier |
| PostToolUse Agent\|Skill | `bellows-log.sh` | 사용 로깅 → ~/.code-forge/usage.jsonl |
| Stop | `quality-gate.sh`, `notify.sh` | ESLint + TypeScript 검증 + Mac 알림 |
| SubagentStop | `subagent-stop.sh` | 구현 에이전트 완료 시 tsc 검증 |
| PreCompact | `pre-compact.sh` | 컨텍스트 압축 전 상태 스냅샷 |
| PermissionRequest | `permission-guard.sh` | 권한 요청 검증 |

### quality-gate 7블록 (Stop 훅, 비차단, 항상 exit 0)

| # | 블록 | 조건 |
|---|------|------|
| 1 | ESLint + tsc | `node_modules/.bin/` 존재 시 |
| 2 | scope 체크 | `.claude/temp/plan.md` 있을 때 |
| 3 | test-trigger | 변경 파일 → 단위 TC 자동 실행 (`.policy/` 자동 탐색) |
| 4 | policy-sync-check | `.policy/` 있을 때 (문서-코드 동기화) |
| 5 | REFLECT flag | 실패 시 `.claude/state/reflect.flag` 생성 → 다음 세션 ADAPT 강제 |
| 6 | scope-type-check | opt-in `[type:tag]` 태그 기반 위반 감지 |
| 7 | design-refs 정리 | git clean 시 |

관찰 로그: `.claude/state/quality.jsonl` append. 계약: `docs/contracts/state-schema.md`.

---

## State Layer

`.claude/state/` 하위 파일이 세션 간 영속 상태를 저장:

| 파일 | 역할 |
|------|------|
| `reflect.flag` | quality-gate 실패 시 다음 세션 ADAPT 강제 |
| `quality.jsonl` | 검증 이벤트 로그 (외부 도구 소비) |
| `progress.md` | 작업 이어가기 + 의사결정 누적 (`/start` append, `/handoff` 갱신, session-init 주입) |
| `route.json` | (예정) 실시간 라우팅 스냅샷 — `event-schema.md` §1 HYBRID |
| `notepad.md` | (옵션) 사용자 작업 메모 |
| `decisions.md` | (옵션) 설계 결정 누적 |

외부 도구는 파일 직독 금지 — `bin/forge status --json` surface 경유:

```bash
$CLAUDE_PLUGIN_ROOT/bin/forge status --json   # JSON Schema v1
$CLAUDE_PLUGIN_ROOT/bin/forge version
```

계약: `docs/contracts/state-schema.md`, `docs/contracts/event-schema.md`.

---

## 규칙 적재 (실제 frontmatter와 일치 — 변경 시 본 표 동기화)

| 규칙 | 적재 시점 | 핵심 |
|------|---|------|
| `rules/thinking-model.md` | **alwaysApply** | GROUND→APPLY→VERIFY→ADAPT 루프. 불변 제약 5가지. 가정 분류(A/B/C) |
| `rules/candidate-profile.md` | **alwaysApply** | 코딩 프로필(.candidate/profile.md) 참조 + §3 소통 최소 보장선 + §5 커밋 컨벤션 |
| `rules/coding-standards.md` | path-scoped (`*.{ts,tsx,js,jsx}`) | 코딩 표준, 네이밍, 금지 패턴, import 순서 |
| `rules/build-guide.md` | path-scoped (`*.{tsx,jsx}`) | React 패턴, Hook 규칙, TypeScript 패턴 |
| `rules/review-guide.md` | 자동 주입 없음 — 리뷰 에이전트 5종이 @-include로 직접 로드 (2026-06-12 이중 적재 해소) | 설계 철학, 안티패턴, 성능 최적화 |

---

## 멀티에이전트 협업

3개+ 에이전트 협업 시 Agent Teams 사용:

```
TeamCreate → 팀원 spawn → 병렬 작업 → shutdown → TeamDelete
```

가이드: `instructions/multi-agent/coordination-guide.md`

---

## forge-glow 연동 (L3)

별도 플러그인: https://github.com/ggombee/forge-glow
- bellows-log v2 필드 (session_id, model, duration_ms, success) 소비
- `bin/forge status --json` surface 경유 (파일 직독 안 함)
