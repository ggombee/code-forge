# VAS v2.0 — Build-Time Compilation 마이그레이션 보고서

**날짜:** 2026-03-17
**버전:** 1.1.1 → 2.0.0

---

## 왜 이렇게 바꿨는가

### 기존 문제 (v1.x — 런타임 해석)

VAS v1.x는 **런타임 해석** 방식이었다. 매 세션 시작마다:

1. `session.sh`가 실행되어 VAS 설정을 읽고 `agents/`의 심링크를 전환
2. `vas-rules.md` (164줄)가 세션에 주입되어 TYPE 시스템, STATE/ACT 상속 규칙을 매번 해석
3. 에이전트를 spawn할 때마다 STATE 체인 재귀 해석 + ACT 체인 재계산
4. `SessionStart` / `SessionEnd` hook이 매 세션마다 실행

**구체적 문제:**

| 문제 | 영향 |
|------|------|
| **토큰 낭비** | vas-rules.md 164줄이 매 세션에 주입. 14개 에이전트 × STATE/ACT 체인 재계산 |
| **permissionMode 무시** | VAS 인스턴스의 `permissionMode: bypassPermissions`가 플러그인 제약으로 제대로 적용되지 않음. 심링크 → _agents/ → VAS 런타임 해석 → Agent tool spawn 경로에서 permission이 누락됨 |
| **심링크 전환 복잡성** | session.sh의 switch_agents()가 매 세션마다 rm + ln 수행. VAS on/off 상태에 따라 다른 에이전트 세트가 로드되는 이중 경로 |
| **세션 시작 지연** | SessionStart hook → session.sh → VAS 상태 확인 → 심링크 전환 → VAS 프롬프트 처리 → /vas-activate 실행 |
| **에이전트 이중 관리** | agents-default/ (14파일)와 _agents/ (14파일)를 별도로 유지해야 함 |

### 핵심 비유

> **TypeScript → tsc → .js**

TypeScript 코드를 매번 런타임에 해석하지 않고 빌드타임에 .js로 컴파일하는 것처럼,
VAS 인스턴스를 매번 런타임에 해석하지 않고 `/vas-build`로 정적 .md 파일로 컴파일한다.

---

## 무엇을 바꿨는가

### Phase 1: /vas-build 스킬 생성

| 파일 | 역할 |
|------|------|
| `plugins/vas/skills/vas-build/SKILL.md` | 컴파일러 스킬 정의 (7-step pipeline) |
| `plugins/vas/skills/vas-build/references/compilation-spec.md` | STATE union, ACT 상속, Priority 시맨틱 상세 |
| `plugins/vas/skills/vas-build/references/output-template.md` | 컴파일 출력 포맷 + 빌드 매니페스트 형식 |

### Phase 2: 14개 에이전트 컴파일

`_agents/*.md` → `agents/*.md` 로 컴파일. 심링크가 아닌 실제 파일.

| VAS 인스턴스 | 컴파일 결과 | 이름 변경 | 모델 |
|---|---|---|---|
| `_agents/explore.md` | `agents/scout.md` | explore → scout (빌트인 충돌 회피) | haiku |
| `_agents/analyst.md` | `agents/analyst.md` | - | opus |
| `_agents/architect.md` | `agents/architect.md` | - | opus |
| `_agents/researcher.md` | `agents/researcher.md` | - | sonnet |
| `_agents/code-reviewer.md` | `agents/code-reviewer.md` | - | sonnet |
| `_agents/refactor-advisor.md` | `agents/refactor-advisor.md` | - | sonnet |
| `_agents/vision.md` | `agents/vision.md` | - | sonnet |
| `_agents/implementor.md` | `agents/implementor.md` | - | sonnet |
| `_agents/build-fixer.md` | `agents/build-fixer.md` | - | sonnet |
| `_agents/lint-fixer.md` | `agents/lint-fixer.md` | - | haiku |
| `_agents/testgen.md` | `agents/testgen.md` | - | sonnet |
| `_agents/deep-executor.md` | `agents/deep-executor.md` | - | sonnet |
| `_agents/git-operator.md` | `agents/git-operator.md` | - | sonnet |
| `_agents/codex.md` | `agents/codex.md` | - | sonnet |

+ `agents/.vas-build-manifest.json` 빌드 메타데이터 생성

### Phase 3: 런타임 인프라 제거

| 삭제 대상 | 파일 수 | 이유 |
|---|---|---|
| `hooks/session.sh` | 1 | 심링크 전환 불필요 |
| `agents-default/` 전체 | 14 | 컴파일된 agents/로 대체 |
| `plugins/vas/skills/vas-activate/` | 1 | 런타임 활성화 불필요 |
| `hooks.json` SessionStart/SessionEnd | (수정) | session.sh 호출 + VAS 프롬프트 제거 |

### Phase 4: vas-create-agent 업데이트

- Prerequisites 섹션 제거 (VAS 활성화 체크 불필요)
- Step 4: 심링크 생성 → VAS 인스턴스 파일 생성으로 변경
- Step 5 (NEW): `/vas-build --project` 실행으로 `.claude/agents/`에 컴파일
- Step 6: 후속 안내 업데이트

### Phase 5: 문서 + 설정 업데이트

| 파일 | 변경 내용 |
|------|----------|
| `.claude-plugin/plugin.json` | version: "2.0.0", description 업데이트 |
| `CLAUDE.md` | 구조도에서 agents-default/ 제거, /vas-build 추가, 에이전트 테이블 업데이트 (explore→scout, implementation-executor→implementor) |
| `README.md` | 동일 구조 업데이트, VAS 섹션을 빌드타임 컴파일로 변경 |
| `skills/setup/SKILL.md` | VAS 안내 문구를 /vas-create-agent (자동 빌드) 안내로 교체 |
| `plugins/vas/rules/vas-rules.md` | frontmatter에 `status: reference-only` 추가 |
| `plugins/vas/agents/README.md` | /vas-activate → /vas-build 교체 |

---

## 무엇이 좋아졌는가

### 1. 토큰 절감

| Before (v1.x) | After (v2.0) |
|---|---|
| 매 세션: vas-rules.md 164줄 주입 | 0줄 (규칙이 에이전트 파일에 이미 컴파일됨) |
| 매 spawn: STATE 체인 재계산 | 0회 (이미 합산되어 본문에 포함) |
| SessionStart hook: VAS 프롬프트 36줄 | 0줄 (hook 제거) |

**추정 절감:** 세션당 ~200줄 + spawn당 ~50줄 = 에이전트 3회 spawn 시 **~350토큰 절감**

### 2. permissionMode 정상 적용

| Before | After |
|---|---|
| VAS 인스턴스의 `permissionMode` 무시 | 네이티브 frontmatter에 `permissionMode: bypassPermissions` 직접 명시 |
| Agent tool spawn 경로에서 permission 누락 | Claude Code가 frontmatter를 직접 읽어 적용 |

### 3. 세션 시작 속도 향상

| Before | After |
|---|---|
| SessionStart → session.sh → VAS 설정 확인 → 심링크 전환 → VAS 프롬프트 처리 | SessionStart hook 없음. 에이전트가 바로 로드됨 |
| SessionEnd → session.sh end | SessionEnd hook 없음 |

### 4. 단일 에이전트 소스

| Before | After |
|---|---|
| agents-default/ (14) + _agents/ (14) = 28파일 이중 관리 | agents/ (14) + _agents/ (14, 소스) = 단방향 |
| VAS on/off에 따라 다른 에이전트 세트 | 항상 같은 에이전트 세트 (VAS 컴파일 결과) |

### 5. 에이전트 파일 품질 향상

| Before (agents-default) | After (compiled) |
|---|---|
| `permissionMode: default` | `permissionMode: bypassPermissions` |
| 수동 작성된 규칙 | VAS STATE 체인에서 체계적으로 합산된 규칙 |
| 인스턴스별 분리된 관리 | STATE/ACT 재사용 + 컴파일로 일관성 보장 |

### 6. 점진적 확장 용이

```
/vas-create-agent                    # 프로젝트 에이전트 생성 + 빌드
/vas-create-agent api-specialist     # 추가 에이전트 1개 + 빌드
/vas-build --project --regenerate    # STATE 변경 반영하며 재빌드
```

---

## 보존된 것

| 항목 | 상태 |
|------|------|
| VAS STATE/ACT 체인 정의 (state/, act/, interface/) | 그대로 유지 (65파일) |
| VAS 인스턴스 소스 (_agents/) | 그대로 유지 (14파일, 컴파일 소스) |
| /vas-create-agent 스킬 | 업데이트 (빌드타임 컴파일 연동) |
| vas-rules.md | 유지 (status: reference-only 추가) |
| PostToolUse, PreToolUse, Stop, SubagentStart/Stop hooks | 그대로 유지 |
| 모든 기존 스킬 (/start, /done, /setup 등) | 그대로 유지 |
| 모듈 시스템, 프리셋 | 그대로 유지 |

---

## 파일 변경 요약

| Action | 파일 수 | 대상 |
|--------|---------|------|
| **CREATE** | 4 | vas-build/SKILL.md, compilation-spec.md, output-template.md, .vas-build-manifest.json |
| **CREATE** | 14 | agents/*.md (컴파일된 에이전트, 심링크 아닌 실제 파일) |
| **DELETE** | 16 | agents-default/ (14) + session.sh (1) + vas-activate/ (1) |
| **MODIFY** | 7 | hooks.json, vas-create-agent, plugin.json, CLAUDE.md, README.md, setup SKILL.md, vas-rules.md, vas agents/README.md |
| **KEEP** | 65+ | state/ (29) + act/ (20) + interface/ (2) + _agents/ (14) + 기타 |
