---
name: vas-create-agent
description: 프로젝트를 분석하여 VAS 2.0 에이전트를 생성한다. STATE class 조합과 ACT class를 선택하여 instance 에이전트를 만든다. "에이전트 만들어줘", "VAS 에이전트 생성", "create agent", "에이전트 세팅" 등의 요청에 사용한다.
agent-system: VAS
---

# VAS Create Agent

프로젝트를 분석하고 VAS 2.0 에이전트 정의 파일을 생성하는 스킬.

## References

- `references/subagent-spec.md` — Claude Code subagent frontmatter 필드 전체 규격

## Prerequisites

### vas-activate 확인

이 스킬은 VAS 시스템 위에서 동작한다. 실행 전 VAS가 활성화되었는지 확인한다.

- `.claude/rules/vibe-agent-system.md` 파일이 존재하면 → 로드된 상태
- 파일이 없으면 → "VAS가 활성화되지 않았습니다. `/vas-activate`를 먼저 실행해주세요."
- VAS 없이 진행 요청 시 → 중단. VAS 없이 에이전트를 만들면 상속 해석이 불가능하다.

## 기본 생성 구조

**최소 5개 파일을 기본으로 생성하되, 프로젝트 성격에 따라 추가 에이전트를 자유롭게 생성한다:**

```
.agents/agents/
├── {project}-base.md        (class, STATE) ← 프로젝트 공통 규칙
├── {project}-architect.md   (instance) ← 분석/설계
├── {project}-dev.md         (instance) ← 개발/구현
├── {project}-reviewer.md    (instance) ← 코드 리뷰
├── {project}-tester.md      (instance) ← 테스트 작성
└── ... 프로젝트에 필요한 만큼 추가
```

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
| architect | `${CLAUDE_PLUGIN_ROOT}/plugins/vas/agents/act/analysis/requirement-analyst.md` |
| dev | `${CLAUDE_PLUGIN_ROOT}/plugins/vas/agents/act/dev/implementor.md` |
| reviewer | `${CLAUDE_PLUGIN_ROOT}/plugins/vas/agents/act/quality/reviewer.md` |
| tester | `${CLAUDE_PLUGIN_ROOT}/plugins/vas/agents/act/dev/testgen.md` |

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

`${CLAUDE_PLUGIN_ROOT}/plugins/vas/agents/state/` 에서 프로젝트 스택에 맞는 STATE class를 자동 선택한다:

| 감지 결과 | STATE class |
|----------|-------------|
| React | `${CLAUDE_PLUGIN_ROOT}/plugins/vas/agents/state/framework/react.md` |
| Next.js | `${CLAUDE_PLUGIN_ROOT}/plugins/vas/agents/state/framework/next.md` |
| Vue | `${CLAUDE_PLUGIN_ROOT}/plugins/vas/agents/state/framework/vue.md` |
| TypeScript | `${CLAUDE_PLUGIN_ROOT}/plugins/vas/agents/state/language/typescript.md` |
| JavaScript | `${CLAUDE_PLUGIN_ROOT}/plugins/vas/agents/state/language/javascript.md` |
| Python | `${CLAUDE_PLUGIN_ROOT}/plugins/vas/agents/state/language/python.md` |
| Django | `${CLAUDE_PLUGIN_ROOT}/plugins/vas/agents/state/framework/django.md` |
| Fastify | `${CLAUDE_PLUGIN_ROOT}/plugins/vas/agents/state/framework/fastify.md` |
| PostgreSQL | `${CLAUDE_PLUGIN_ROOT}/plugins/vas/agents/state/database/postgresql.md` |
| Redis | `${CLAUDE_PLUGIN_ROOT}/plugins/vas/agents/state/database/redis.md` |
| monorepo (workspaces) | `${CLAUDE_PLUGIN_ROOT}/plugins/vas/agents/state/technique/monorepo.md` |
| SSR 감지 | `${CLAUDE_PLUGIN_ROOT}/plugins/vas/agents/state/technique/ssr.md` |
| testing-library 감지 | `${CLAUDE_PLUGIN_ROOT}/plugins/vas/agents/state/technique/testing-library.md` |

**base class 파일 형식:**

```markdown
---
type: class
name: {project}-base
schema: ${CLAUDE_PLUGIN_ROOT}/plugins/vas/agents/interface/state-agent.md
extends:
  - ${CLAUDE_PLUGIN_ROOT}/plugins/vas/agents/state/framework/{framework}.md
  - ${CLAUDE_PLUGIN_ROOT}/plugins/vas/agents/state/language/{language}.md
---

## Persona
- [Identity] {프로젝트}의 전문가

## Must
- [Key] 프로젝트 공통 규칙 (분석에서 발견한 컨벤션)

## Never
- [Key] 프로젝트 공통 금지사항
```

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
  - ${CLAUDE_PLUGIN_ROOT}/plugins/vas/agents/state/role/{role-state}.md
act: ${CLAUDE_PLUGIN_ROOT}/plugins/vas/agents/act/{category}/{act-class}.md
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
| architect | `${CLAUDE_PLUGIN_ROOT}/plugins/vas/agents/state/role/architect.md` |
| dev | `${CLAUDE_PLUGIN_ROOT}/plugins/vas/agents/state/role/developer.md` (+ `${CLAUDE_PLUGIN_ROOT}/plugins/vas/agents/state/role/fe.md` 또는 `${CLAUDE_PLUGIN_ROOT}/plugins/vas/agents/state/role/be.md`) |
| reviewer | `${CLAUDE_PLUGIN_ROOT}/plugins/vas/agents/state/role/quality.md` |
| tester | `${CLAUDE_PLUGIN_ROOT}/plugins/vas/agents/state/role/quality.md` |

#### 3-3: 사용자 확인

설계 결과를 보여주고 확인받는다.

### Step 4: 에이전트 파일 생성

1. `.agents/agents/`에 모든 에이전트 파일 작성 (base 1 + instance 4)
2. instance 파일만 `.claude/agents/`에 심링크 생성:
   ```bash
   ln -sf ../../.agents/agents/{agent_name}.md .claude/agents/{agent_name}.md
   ```
3. 심링크 읽기 테스트로 정상 작동 확인

### Step 5: 후속 안내

- 생성된 파일 목록
- `/vas-activate {agent_name}`으로 활성화하는 방법
- 규칙 수정 → `.agents/agents/{project}-*.md` 직접 편집
- 역할 추가 → 이 스킬 다시 호출

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
