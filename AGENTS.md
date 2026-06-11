# AGENTS.md — code-forge Agent Instructions

이 파일은 AAIF(Agent Architecture Instruction Format) 표준에 따라 작성되었다.
AI 에이전트(Codex/Cursor 포함)가 이 저장소에서 작업할 때 준수해야 할 규칙을 정의한다.

> **카탈로그(에이전트/스킬/훅/규칙 표)는 여기 없다** — 단일 소스 [`docs/REFERENCE.md`](docs/REFERENCE.md) 참조.
> 이 파일은 멀티모델 진입점 델타(수정 규칙 + 금지 작업)만 유지한다 (2026-06-12 H1 dedup).

---

## 프로젝트 구조 개요

```
code-forge/
├── agents/          # 플러그인 에이전트 .md (직접 편집 가능)
├── docs/            # 설계 원칙, 가이드, REFERENCE.md(카탈로그 단일 소스)
├── hooks/           # Claude Code 훅 스크립트
├── instructions/    # 멀티에이전트 협업 가이드
├── modules/         # 스택별 컨벤션 모듈
├── plugins/smith/   # Smith 빌드 시스템 (프로젝트 에이전트 소스)
├── presets/         # 스택 프리셋
├── rules/           # 사고 모델 + 코딩 표준
├── skills/          # 스킬 커맨드 (/start, /handoff 등 — 목록은 REFERENCE.md)
├── CLAUDE.md        # 플러그인 메인 설명서 (포인터 중심)
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

Smith 빌드는 프로젝트 에이전트 전용. STATE/ACT 부품은 `plugins/smith/agents/state/`, `plugins/smith/agents/act/`.

---

## 금지 작업

| 금지 | 이유 |
|------|------|
| `.claude/agents/` (프로젝트 컴파일 출력) 직접 수정 | smith-build 출력물 — 다음 컴파일 시 덮어씌워짐. 소스는 `.agents/agents/` |
| `hooks/hooks.json` 수동 수정 후 검증 생략 | JSON 파싱 오류로 훅 전체 비활성화됨 |
| `rules/` 파일 삭제 | alwaysApply/path-scoped 규칙 — 모든 에이전트 동작에 영향 |
| `presets/` 스키마 변경 | `/setup` 스킬 파싱 오류 유발 |
| 민감한 파일(.env, credentials) 커밋 | `write-guard.sh`가 Write를 차단하지만 직접 커밋은 차단 안 됨 |
| 폐지 스킬(/done /bug-fix /refactor /quality)을 문서/표에 재추가 | v4.0에서 규칙·훅으로 흡수됨 — 대체 매핑은 `docs/CATALOG.md` |
| 에이전트/스킬 개수를 손으로 세서 문서에 박기 | 3중 불일치 사고(17/19/21, 2026-06-11 검출) 재발 방지 — 산출 명령 표기 |

---

## 카탈로그 참조 (단일 소스)

| 찾는 것 | 위치 |
|---------|------|
| 에이전트 목록 (4단계 권한 + 모델 핀) | `docs/REFERENCE.md` §에이전트 |
| 스킬 목록 (직접/자동 호출) | `docs/REFERENCE.md` §스킬 |
| 훅 + quality-gate + State Layer | `docs/REFERENCE.md` §Hooks~ |
| 규칙 적재 시점 (alwaysApply/path-scoped) | `docs/REFERENCE.md` §규칙 적재 |
| 멀티에이전트 협업 (Agent Teams) | `docs/REFERENCE.md` §멀티에이전트 + `instructions/multi-agent/coordination-guide.md` |
