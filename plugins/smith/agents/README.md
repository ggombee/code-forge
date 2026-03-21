# Smith 2.0 (Agent Smith System)

AI 에이전트를 **지식(STATE)**과 **행동(ACT)**으로 분리하여 정의하는 시스템.

---

## 철학

### 왜 STATE/ACT를 분리하는가

스킬에도 두 종류가 있다:
- **규칙을 주입하는 스킬** — `vue-best-practices`, `coding-standards`
- **행동을 수행하는 스킬** — `bug-fix`, `refactor`, `generate-test`

에이전트도 마찬가지다. "React를 안다"와 "버그를 수정한다"는 본질적으로 다른 관심사다.

| | STATE | ACT |
|---|-------|-----|
| 핵심 질문 | "무엇을 아는가" | "무엇을 하는가" |
| 성격 | 정적 규칙 | 동적 워크플로우 |
| 조합 | 여러 개 합산 가능 | 하나만 선택 |
| 변경 | Override로 규칙 대체 | 새 class를 만들어야 함 |

### 설계 원칙

**추상 레이어는 thin하게.** 파일 수가 많아져도 괜찮다. 각 레이어는 자기 책임만 진다.

**합산, 덮어쓰기가 아닌 우선순위.** 여러 STATE를 조합할 때 모든 규칙이 살아있다. 같은 키가 충돌할 때만 뒤쪽이 우선한다. 어떤 규칙도 명시적 충돌 없이 무시되지 않는다.

**행동은 단일 책임.** 하나의 에이전트가 동시에 "버그 수정"이면서 "리팩토링"이면 책임이 꼬인다. 행동은 하나, 지식은 여러 개.

**권한 분리.** 분석하는 에이전트는 코드를 수정하지 않는다. 코드를 수정하는 에이전트는 리뷰하지 않는다. 검증하는 에이전트는 보고만 한다.

---

## 타입 시스템

```
interface  →  구조 정의 (섹션, 키 형식)
class      →  상속 가능한 규칙/워크플로우 정의
instance   →  실제 활성화 대상 (STATE 조합 + ACT)
```

`interface`와 `class`는 직접 활성화할 수 없다. 오직 `instance`만 활성화된다.

---

## 디렉토리 구조

```
   # 추상 정의 (플러그인 내)
├── interface/
│   ├── state-agent.md            # STATE 구조 정의
│   └── act-agent.md              # ACT 구조 정의
│
├── state/
│   ├── state.md                  # STATE 추상 class
│   ├── role/                     # 역할 (developer, architect, ...)
│   ├── language/                 # 언어 (typescript, python, ...)
│   ├── framework/                # 프레임워크 (react, vue, ...)
│   ├── database/                 # DB (postgresql, redis, ...)
│   ├── tool/                     # 도구 (figma, ...)
│   └── technique/                # 기법 (monorepo, tdd, ssr, ...)
│
└── act/
    ├── act.md                    # ACT 추상 class
    ├── analysis/                 # 분석 (requirement-analyst, spec-to-testcase)
    ├── dev/                      # 개발 (implementor, bug-fixer, refactorer, assayer)
    ├── quality/                  # 검증 (reviewer, test-runner, security-reviewer)
    └── ops/                      # 운영 (git-operator)

# 프로젝트 로컬
./.agents/
├── agents/                           # instance (프로젝트)
│   └── {project}-{role}.md
└── smith/                              # 프로젝트 전용 class (선택)
    └── ...
```

---

## Interface

### STATE Interface

"이 에이전트가 무엇을 아는가"를 기술한다.

```markdown
## Persona
- [Identity] 핵심 전문 영역과 정체성
- [Mindset] 우선순위와 철학
- [Communication] 톤과 상호작용 스타일

## Must        — 반드시 지켜야 하는 규칙
## Never       — 절대 해서는 안 되는 것
## Should      — 권장하는 패턴
## Override    — 상속된 규칙 대체
```

### ACT Interface

"이 에이전트가 무엇을 하는가"를 기술한다.

```markdown
## Trigger        — 활성화 조건과 입력
## Workflow        — 단계별 실행 흐름
## Verification    — 완료 전 자기 검증
## Output          — 최종 산출물
## Collaboration   — 다른 에이전트와의 핸드오프
## Permission      — 모델, 도구, 행동 범위 (기본값 가이드)
```

ACT는 instance에서 override할 수 없다. 워크플로우를 바꾸려면 새 ACT class를 만든다.

---

## 상속과 합산

### STATE 상속 체인

```
state.md (추상)
├── role/developer.md
│   ├── role/fe.md
│   └── role/be.md
├── language/language.md
│   ├── language/typescript.md
│   └── language/python.md
├── framework/framework.md
│   ├── framework/react.md
│   │   └── framework/next.md
│   └── framework/vue.md
└── ...
```

class에서 `extends`로 부모를 지정하면 부모의 규칙을 상속받는다.

### STATE 합산 규칙

instance에서 여러 STATE를 조합하면:

1. **모든 규칙이 합산**된다 (union)
2. 같은 `[Key]`가 충돌할 때만 **배열 뒤쪽이 우선**
3. instance body가 **최종 우선순위**

```
우선순위 (낮음 → 높음):
state.md → extends 상위 → extends 하위 → state[] 앞 → state[] 뒤 → instance body
```

### Override

`## Override` 섹션만이 상속된 규칙을 명시적으로 대체할 수 있다:

```markdown
## Override
### Must
- [Priority] 이 규칙이 상속된 모든 Must [Priority]를 대체한다
```

Override에 언급되지 않은 규칙은 그대로 누적된다.

### ACT 상속

ACT class 간 extends에서:
- **Workflow**: 하위가 전체 재작성
- **나머지**: 하위가 명시하면 대체, 미명시 시 상속

---

## 권한 분리

| 카테고리 | 기본 모델 | 허용 도구 | 원칙 |
|---------|----------|----------|------|
| `analysis/` | opus | Read, Grep, Glob | 분석하고 산출물 도출만 |
| `quality/` | opus | Read, Grep, Glob, Bash(개별) | 검증하고 보고만. 코드 안 건드림 |
| `dev/` | sonnet | Read, Write, Edit, Bash | 코드를 수정하는 행위 |
| `ops/` | sonnet | Read, Grep, Glob, Bash(git) | 운영 명령 실행만 |

ACT class body의 Permission은 **기본값 가이드**이다. 실제 제약은 instance frontmatter의 `model`, `tools`, `boundary`가 확정한다.

---

## Instance

STATE 조합 + 단일 ACT로 실제 에이전트를 생성한다.

```yaml
---
type: instance
name: next-bug-fixer
model: sonnet
tools: [Read, Write, Edit, Bash, Grep, Glob]
boundary: [apps/ 및 packages/ 내 파일만 수정]
state:
  - state/role/developer.md
  - state/language/typescript.md
  - state/framework/next.md
  - state/technique/monorepo.md
act: act/dev/bug-fixer.md
---

## Must
- [Styling] Emotion을 사용한다
```

- `state`: 배열 — 여러 STATE 조합
- `act`: 단일 값 — 하나의 행동
- body에 같은 키 → STATE 규칙 override
- ACT는 override 불가

---

## 파이프라인

ACT class들은 파이프라인으로 연결된다:

### 기능 개발

```
requirement-analyst → spec-to-testcase → assayer → implementor → test-runner → reviewer
   요구사항 분석        테스트 케이스 도출    테스트 작성     구현         검증          리뷰
```

### 버그 수정

```
bug-fixer → assayer → test-runner → reviewer
  분석/수정    회귀 테스트    검증       리뷰
```

### 리팩토링

```
refactorer → test-runner → reviewer
  보호 테스트+리팩토링   검증      리뷰
```

---

## 스킬

| 스킬 | 용도 |
|------|------|
| `/smith-build` | Smith 인스턴스를 정적 .md로 컴파일 (빌드타임 컴파일) |
| `/smith-create-agent` | 프로젝트를 분석하여 instance 에이전트 생성 → 자동 빌드 |

---

## 경로 해석

| 패턴 | 해석 |
|------|------|
| `smith/...` | `` 기준 |
| `./...` | 프로젝트 루트 기준 |
| 절대 경로 | 그대로 사용 |

---

## 확장

### STATE class 추가

프로젝트에 특화된 기법이 있으면 `state/technique/`에 추가한다:

```markdown
---
type: class
name: my-technique
schema: interface/state-agent.md
extends: state/state.md
---

## Must
- [Key] 이 기법의 필수 규칙
```

### ACT class 추가

새로운 워크플로우가 필요하면 해당 카테고리에 추가한다:

```markdown
---
type: class
name: my-workflow
schema: interface/act-agent.md
extends: act/act.md
---

## Workflow
- [Phase:1] ...
```

### 프로젝트 로컬 확장

글로벌 Smith를 변경하지 않고 프로젝트에서만 쓸 class/instance를 만들 수 있다:

```
./.agents/
├── smith/state/technique/our-custom-pattern.md      # 프로젝트 전용 STATE
└── agents/my-project-dev.md                      # 프로젝트 전용 instance
```
