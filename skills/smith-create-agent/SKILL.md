---
name: smith-create-agent
description: 프로젝트를 분석하여 Smith 2.0 에이전트를 생성한다. STATE class 조합과 ACT class를 선택하여 instance 에이전트를 만든다. "에이전트 만들어줘", "Smith 에이전트 생성", "create agent", "에이전트 세팅" 등의 요청에 사용한다.
category: setup
agent-system: Smith
---

# Smith Create Agent

프로젝트를 분석하고 Smith 2.0 에이전트 정의 파일을 생성하는 스킬.

## 호출 경로

| 경로 | 동작 |
|------|------|
| 사용자 직접 (`/code-forge:smith-create-agent`) | Step 1부터 풀 실행 — 프로젝트 분석 + 대화형 확인 |
| `/code-forge:setup`에서 위임 호출 (orchestrator) | **Step 1 스킵** — `.claude/profile.json`이 이미 Step 5에서 생성됐으므로 재사용. 즉시 Step 2 Deep Analysis부터 시작 |

**위임 감지 방법**: `.claude/profile.json`이 현재 턴에 이미 존재하면 setup으로부터 위임된 호출로 간주한다. 사용자 재확인 질문을 생략하고 분석/생성 파이프라인으로 직행한다.

## References

- `references/subagent-spec.md` — Claude Code subagent frontmatter 필드 전체 규격

## 기본 생성 구조

**최소 8개 파일을 기본으로 생성하되, 프로젝트 성격에 따라 추가 에이전트를 자유롭게 생성한다:**

```
.agents/agents/
├── {project}-domain.md      (class, STATE) ← 도메인 모델/용어/플로우
├── {project}-policy.md      (class, STATE) ← SSOT/금지 영역/규칙
├── {project}-context.md     (class, STATE) ← 디렉토리 맵/추상화/패턴
├── {project}-base.md        (class, STATE) ← extends: framework+language+위 3개
├── {project}-architect.md   (instance) ← 분석/설계
├── {project}-dev.md         (instance) ← 개발/구현
├── {project}-reviewer.md    (instance) ← 코드 리뷰
├── {project}-tester.md      (instance) ← 테스트 작성
├── .analysis-manifest.json  ← 분석 메타데이터 (staleness 감지용)
└── ... 프로젝트에 필요한 만큼 추가
```

### Deep Analysis Pipeline (Step 2)

프로젝트 분석을 4축 병렬로 수행한다:

**2-1. 기술 스택 스캔** (기존 유지)
- package.json, tsconfig.json 등에서 기술 스택 파악

**2-2. 도메인 분석** (신규)
- 타입 정의, API 라우트, DB 스키마, 상태 관리, README에서 교차 검증
- 핵심 엔티티, 비즈니스 플로우, 도메인 용어 추출
- → `{project}-domain.md` 생성

**2-3. 정책 분석** (신규)
- CLAUDE.md, ESLint, tsconfig, CI, CODEOWNERS에서 추출
- SSOT 위치, 수정 금지 영역, import 규칙, PR/커밋 규칙
- → `{project}-policy.md` 생성

**2-4. 컨텍스트 분석** (신규)
- 디렉토리 트리, import 빈도, shared 파일에서 추론
- 아키텍처 패턴 (레이어드, DDD, feature-based 등) 자동 분류
- → `{project}-context.md` 생성

### base class extends 확장

기존: `framework + language`만 extends
변경: `framework + language + domain + policy + context` extends
→ instance는 변경 불필요 (투명한 확장)

### --refresh 모드

`.analysis-manifest.json`의 `analyzedAt`으로부터 30일 이상 경과 시 재분석 권장.
변경된 축만 선택적으로 재분석하고, 사용자 정의 규칙(userDefinedRules)은 보호.

### 추가 에이전트 예시

프로젝트 분석 결과에 따라 아래와 같은 에이전트를 추가로 생성할 수 있다:

| 상황 | 추가 에이전트 | ACT class |
|------|-------------|-----------|
| 풀스택 프로젝트 | `{project}-fe-dev.md`, `{project}-be-dev.md` | `act/dev/implementor.md` (state로 fe/be 분리) |
| 보안 중요 프로젝트 | `{project}-security.md` | `act/quality/security-reviewer.md` |
| 리팩토링 중인 프로젝트 | `{project}-refactorer.md` | `act/dev/refactorer.md` |
| 버그 트래킹 필요 | `{project}-bug-fixer.md` | `act/dev/bug-fixer.md` |
| Git 워크플로우 복잡 | `{project}-git-ops.md` | `act/ops/git-operator.md` |
| 테스트 케이스 도출 분리 | `{project}-spec-analyst.md` | `act/analysis/spec-to-testcase.md` |

기본 5개에 제한되지 않는다. 프로젝트를 분석한 뒤 필요한 역할을 모두 생성하라.

### 역할별 기본 ACT 매핑

| 역할 | ACT class |
|------|-----------|
| architect | `${CLAUDE_PLUGIN_ROOT}/plugins/smith/agents/act/analysis/requirement-analyst.md` |
| dev | `${CLAUDE_PLUGIN_ROOT}/plugins/smith/agents/act/dev/implementor.md` |
| reviewer | `${CLAUDE_PLUGIN_ROOT}/plugins/smith/agents/act/quality/reviewer.md` |
| tester | `${CLAUDE_PLUGIN_ROOT}/plugins/smith/agents/act/dev/assayer.md` |

ACT class의 `## Permission` 섹션에서 `model`, `tools`, `permissionMode`를 자동 추출하여 instance frontmatter에 적용한다.

### tools / permissionMode — ACT class에서 자동 추출

instance의 `tools`와 `permissionMode`는 하드코딩하지 않는다. 매핑된 ACT class 파일의 `## Permission` 섹션에서 읽어온다:

1. ACT class 파일을 읽는다
2. `[Tools]` 값 → instance frontmatter의 `tools` 필드에 적용
3. `[PermissionMode]` 값 → instance frontmatter의 `permissionMode` 필드에 적용
4. `[Model]` 값 → instance frontmatter의 `model` 필드에 적용

ACT class에 값이 없으면 상위(`act.md`)의 기본값을 사용한다:
- `tools`: `Read, Grep, Glob`
- `permissionMode`: `bypassPermissions`
- `model`: `sonnet`

### 기본 스킬 매핑

| 역할 | 스킬 |
|------|------|
| architect | `superpowers:brainstorming`, `superpowers:writing-plans`, `investigate` |
| dev | `superpowers:test-driven-development`, `superpowers:executing-plans`, `superpowers:verification-before-completion` |
| reviewer | `code-review:code-review`, `simplify`, `superpowers:verification-before-completion` |
| tester | `superpowers:test-driven-development`, `spec-to-test-cases`, `superpowers:verification-before-completion` |

프로젝트 스택에 따라 추가 스킬을 매핑한다:
- Vue 프로젝트 → reviewer에 `vue-best-practices`, `vue-development-guides` 추가
- React 프로젝트 → reviewer에 `vercel-react-best-practices` 추가

## Pipeline

### Step 1: 프로젝트 디렉토리 준비

1. `.gitignore`에 `.agents`와 `.claude`가 포함되어 있는지 확인
2. 없으면 사용자에게 추가 여부 질문
3. 필요한 디렉토리 생성: `.agents/agents/`, `.claude/agents/`

#### 1-2: 기존 에이전트 통합 스캔

`.claude/agents/`에 기존 에이전트 파일이 있으면 통합 흐름을 실행한다:

1. 기존 `.claude/agents/*.md` 파일 목록과 역할(name, description, tools) 추출
2. 역할 매핑: 기존 에이전트가 dev/reviewer/architect/tester 중 어떤 역할인지 판별
3. 충돌 감지 결과를 보여주고 사용자에게 선택:

```
기존 에이전트가 발견되었습니다:

  .claude/agents/my-dev.md       → 개발 역할 (Smith dev와 충돌)
  .claude/agents/my-reviewer.md  → 리뷰 역할 (Smith reviewer와 충돌)
  .claude/agents/api-agent.md    → 커스텀 역할 (충돌 없음)

> Smith 에이전트에 기존 규칙 병합 (기존 에이전트의 Must/Never를 Smith에 포함)
  Smith 에이전트로 교체 (기존 에이전트 → .claude/agents.bak/)
  공존 (기존 유지 + Smith는 {project}- 접두사로 분리)
  취소
```

| 선택 | 동작 |
|------|------|
| 병합 | 기존 에이전트의 Must/Never/Persona 분석 → `{project}-policy.md`에 반영 → 기존 파일 `.claude/agents.bak/`으로 백업 |
| 교체 | 기존 파일 `.claude/agents.bak/`으로 백업 → Smith 에이전트로 대체 |
| 공존 | 기존 파일 그대로 유지 → Smith 에이전트는 `{project}-` 접두사로 병존 |
| 취소 | 아무것도 하지 않고 종료 |

기존 에이전트가 없으면 이 단계를 건너뛴다.

### Step 2: 프로젝트 분석

**설정 파일 스캔:**
- `package.json` → 프레임워크, 런타임, 주요 의존성
- `tsconfig.json` / `jsconfig.json` → TypeScript 사용 여부
- `vite.config.*`, `next.config.*`, `nuxt.config.*` → 빌드 도구
- `pyproject.toml`, `go.mod`, `Cargo.toml` → 기타 언어

**프로젝트 구조 분석:**
- `src/` 구조 파악
- 기존 CLAUDE.md 읽기 → 컨벤션 수집
- 테스트 설정 파일 확인

**코드 패턴 샘플링:**
- 주요 디렉토리에서 2-3개 파일을 읽어 코딩 스타일 파악

### Step 3: 에이전트 설계

#### 3-1: base class 설계

**STATE class 자동 선택:**

`${CLAUDE_PLUGIN_ROOT}/plugins/smith/agents/state/` 에서 프로젝트 스택에 맞는 STATE class를 자동 선택한다:

| 감지 결과 | STATE class |
|----------|-------------|
| React | `${CLAUDE_PLUGIN_ROOT}/plugins/smith/agents/state/framework/react.md` |
| Next.js | `${CLAUDE_PLUGIN_ROOT}/plugins/smith/agents/state/framework/next.md` |
| Vue | `${CLAUDE_PLUGIN_ROOT}/plugins/smith/agents/state/framework/vue.md` |
| TypeScript | `${CLAUDE_PLUGIN_ROOT}/plugins/smith/agents/state/language/typescript.md` |
| JavaScript | `${CLAUDE_PLUGIN_ROOT}/plugins/smith/agents/state/language/javascript.md` |
| Python | `${CLAUDE_PLUGIN_ROOT}/plugins/smith/agents/state/language/python.md` |
| Django | `${CLAUDE_PLUGIN_ROOT}/plugins/smith/agents/state/framework/django.md` |
| Fastify | `${CLAUDE_PLUGIN_ROOT}/plugins/smith/agents/state/framework/fastify.md` |
| PostgreSQL | `${CLAUDE_PLUGIN_ROOT}/plugins/smith/agents/state/database/postgresql.md` |
| Redis | `${CLAUDE_PLUGIN_ROOT}/plugins/smith/agents/state/database/redis.md` |
| monorepo (workspaces) | `${CLAUDE_PLUGIN_ROOT}/plugins/smith/agents/state/technique/monorepo.md` |
| SSR 감지 | `${CLAUDE_PLUGIN_ROOT}/plugins/smith/agents/state/technique/ssr.md` |
| testing-library 감지 | `${CLAUDE_PLUGIN_ROOT}/plugins/smith/agents/state/technique/testing-library.md` |

**base class 파일 형식:**

```markdown
---
type: class
name: {project}-base
schema: ${CLAUDE_PLUGIN_ROOT}/plugins/smith/agents/interface/state-agent.md
extends:
  - ${CLAUDE_PLUGIN_ROOT}/plugins/smith/agents/state/framework/{framework}.md
  - ${CLAUDE_PLUGIN_ROOT}/plugins/smith/agents/state/language/{language}.md
blueprint:
  - ${CLAUDE_PLUGIN_ROOT}/rules/thinking-model.md
  - ${CLAUDE_PLUGIN_ROOT}/rules/coding-standards.md
---

## Persona
- [Identity] {프로젝트}의 전문가

## Must
- [Key] 프로젝트 공통 규칙 (분석에서 발견한 컨벤션)

## Never
- [Key] 프로젝트 공통 금지사항
```

> **`blueprint` 필드**: 컴파일 시 축약본이 에이전트 본문에 인라인 임베딩된다. `extends`/`state`와 달리 STATE 체인에 합산되지 않고, 독립된 `## Blueprint` 섹션으로 출력된다. 이를 통해 플러그인 없이도(degraded mode) 사고모델 핵심이 에이전트에 포함된다.

규칙 작성 원칙:
- 부모 STATE에 이미 있는 규칙은 반복하지 않는다
- 프로젝트에 특화된 규칙만 추가한다
- 부모 규칙을 바꿔야 하면 Override 섹션 사용

#### 3-2: instance 에이전트 설계

**instance 파일 형식:**

```yaml
---
type: instance
name: {project}-{role}
description: {역할 설명}
model: {ACT class [Model]에서 추출}
permissionMode: {ACT class [PermissionMode]에서 추출}
tools: {ACT class [Tools]에서 추출}
boundary: [{행동 범위}]
state:
  - ./.agents/agents/{project}-base.md
  - ${CLAUDE_PLUGIN_ROOT}/plugins/smith/agents/state/role/{role-state}.md
act: ${CLAUDE_PLUGIN_ROOT}/plugins/smith/agents/act/{category}/{act-class}.md
memory: project
skills:
  - {역할별 스킬 목록}
---

## Persona
- [Identity] {구체적 역할과 입출력}
- [Mindset] {판단 기준과 우선순위}
- [Communication] {출력 형식과 소통 스타일}

## Must
- [Key] 역할 특화 필수 규칙 (5~8개)

## Never
- [Key] 역할 특화 금지사항 (3~4개)

## Should
- [Key] 역할 특화 권장사항 (2~4개)
```

**역할별 state 매핑:**

| 역할 | state에 포함할 role STATE |
|------|-------------------------|
| architect | `${CLAUDE_PLUGIN_ROOT}/plugins/smith/agents/state/role/architect.md` |
| dev | `${CLAUDE_PLUGIN_ROOT}/plugins/smith/agents/state/role/developer.md` (+ `${CLAUDE_PLUGIN_ROOT}/plugins/smith/agents/state/role/fe.md` 또는 `${CLAUDE_PLUGIN_ROOT}/plugins/smith/agents/state/role/be.md`) |
| reviewer | `${CLAUDE_PLUGIN_ROOT}/plugins/smith/agents/state/role/quality.md` |
| tester | `${CLAUDE_PLUGIN_ROOT}/plugins/smith/agents/state/role/quality.md` |

#### 3-3: 사용자 확인

설계 결과를 보여주고 확인받는다.

### Step 4: 에이전트 파일 생성

1. `.agents/agents/`에 모든 에이전트 파일 작성 (base 1 + instance N)

### Step 5: 빌드타임 컴파일

`/code-forge:smith-build --project` 를 실행하여 `.agents/agents/`의 Smith 인스턴스를 `.claude/agents/`에 컴파일한다.

1. `.agents/agents/`의 `type: instance` 파일을 대상으로 Smith 빌드 수행
2. STATE 체인 해석 → ACT 체인 해석 → 네이티브 frontmatter 매핑
3. `.claude/agents/`에 플랫 .md 파일 생성
4. 빌드 결과를 사용자에게 보고

### Step 6: 후속 안내

- 생성된 파일 목록
- 컴파일된 에이전트가 `.claude/agents/`에 위치하여 즉시 사용 가능
- 규칙 수정 → `.agents/agents/{project}-*.md` 직접 편집 후 `/code-forge:smith-build --project` 재실행
- 역할 추가 → `/code-forge:smith-create-agent {역할}` 으로 추가 생성

## 기존 에이전트 수정

`.agents/agents/`에 에이전트가 이미 있으면:
1. 기존 에이전트 목록을 보여준다
2. "새로 만들기" vs "기존 수정" 중 선택
3. 수정 선택 시: 기존 파일 읽기 → 프로젝트 재분석 → 변경 필요 부분만 제안

## 역할별 규칙 가이드

<details>
<summary>architect (분석/설계)</summary>

Must:
- `[ImpactAnalysis]` 변경 시 영향 범위를 파일/컴포넌트 단위로 명세
- `[Specification]` 원본(Jira/Confluence/Figma)을 참조하여 명세서 작성
- `[DataFlow]` API 요청/응답 타입, 쿼리 키, 상태 변환 흐름을 명세에 포함
- `[FileList]` 생성/수정/삭제할 파일 목록과 변경 사유 기술
- `[TestScenario]` 검증해야 할 테스트 시나리오 함께 도출

Never:
- `[NoImplBeforeReview]` 명세서 리뷰 완료 전 구현 코드 작성 금지
- `[NoAssumption]` 기존 코드 실제 확인 없이 동작 가정 금지

Should:
- `[AlternativeDesign]` 구현 방식 대안과 트레이드오프 비교
</details>

<details>
<summary>dev (개발/구현)</summary>

Must:
- `[SpecFirst]` 확정된 명세서 확인 후 구현
- `[TypeSafety]` 새로운 API 응답/props/상태에 TypeScript 타입 정의 필수
- `[ErrorHandling]` API 실패, 빈 데이터, 로딩 상태 처리
- `[ExistingPattern]` 기존 패턴 확인 후 일관성 유지

Never:
- `[NoSpecNoCode]` 명세서 없이 구현 시작 금지
- `[NoAnyType]` any 타입 사용 금지
- `[NoScopeCreep]` 명세서에 없는 기능 추가 금지
</details>

<details>
<summary>reviewer (코드 리뷰)</summary>

Must:
- `[SpecCompliance]` 명세서 요구사항 전체 구현 여부 대조
- `[ProjectConvention]` 프로젝트 컨벤션 준수 검증
- `[TypeReview]` 타입 정의 정확성 검증

Never:
- `[NoDirectFix]` 코드 직접 수정 금지. 피드백만 제공
- `[NoStyleNit]` ESLint/Prettier로 잡히는 이슈에 시간 소비 금지

피드백 형식: `[BLOCKER]`, `[MAJOR]`, `[MINOR]`, `[SUGGESTION]`
</details>

<details>
<summary>tester (테스트)</summary>

Must:
- `[ScenarioFirst]` 테스트 시나리오 먼저 도출
- `[HappyPath]` 정상 동작 시나리오 커버
- `[EdgeCase]` 빈 데이터, null, 경계값 커버
- `[ErrorCase]` API 실패, 유효성 검증 실패 커버

Never:
- `[NoImplDetail]` 내부 구현에 의존하는 테스트 금지
- `[NoFlaky]` 타이밍 의존 불안정 테스트 금지

테스트 시나리오 형식: Given-When-Then
</details>
