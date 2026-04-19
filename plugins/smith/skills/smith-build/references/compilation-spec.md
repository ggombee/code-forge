# Smith Compilation Specification

smith-rules.md에서 추출한 컴파일 시맨틱 정의. /code-forge:smith-build 스킬의 참조 문서.

---

## TYPE System

| Type | 컴파일 대상 | 설명 |
|------|-----------|------|
| `interface` | ❌ | 구조 정의만. 섹션/키 형식 참조용 |
| `class` | ❌ | 상속 가능한 규칙 정의. extends 체인의 중간 노드 |
| `instance` | ✅ | 실제 컴파일 대상. STATE 조합 + ACT 참조 |

**오직 `type: instance`이면서 `agent-system: Smith`인 파일만 컴파일한다.**

---

## STATE 컴파일 시맨틱

### 합산 규칙 (Union)

여러 STATE를 조합할 때 모든 규칙은 합산된다.

```
state: [A, B, C]

결과 = A의 모든 규칙 ∪ B의 모든 규칙 ∪ C의 모든 규칙
```

동일 `[Key]`가 2개 이상 STATE에 존재할 때만 충돌 해소:
- 배열 뒤쪽(C > B > A)이 우선한다
- 충돌이 아닌 규칙은 전부 살아있다

### extends 체인 해석

```
instance body (최고 우선순위)
    ↑
state[] 배열 뒤쪽 (C)
    ↑
state[] 배열 앞쪽 (A, B)
    ↑
extends 하위 class
    ↑
extends 상위 class
    ↑
state.md (추상, 최저 우선순위)
```

### 각 STATE에서 추출하는 섹션

| 섹션 | 컴파일 규칙 |
|------|-----------|
| `## Persona` | instance body가 있으면 대체, 없으면 상속 |
| `## Must` | 합산 (union), 같은 [Key] 충돌 시 뒤쪽 우선 |
| `## Never` | 합산 (union), 같은 [Key] 충돌 시 뒤쪽 우선 |
| `## Should` | 합산 (union), 같은 [Key] 충돌 시 뒤쪽 우선 |
| `## Override` | 상속된 같은 [Key] 규칙을 명시적으로 대체 |

### Override 처리

```markdown
## Override
### Must
- [Priority] 이 규칙이 상속된 모든 Must [Priority]를 대체한다
```

1. Override에 명시된 [Key]는 상속된 같은 섹션의 같은 [Key]를 대체한다
2. Override에 명시되지 않은 규칙은 그대로 누적 유지된다
3. Override 자체도 상속된다

---

## ACT 컴파일 시맨틱

### extends 체인 해석

```
act.md (추상, 기본값)
    ↓
상위 ACT class
    ↓
하위 ACT class (instance의 act 필드)
```

### 각 ACT에서 추출하는 섹션

| 섹션 | 상속 규칙 |
|------|---------|
| `## Trigger` | 하위가 명시하면 대체, 미명시 시 상속 |
| `## Workflow` | **전체 재작성** (부분 override 아님) |
| `## Verification` | 하위가 명시하면 대체, 미명시 시 상속 |
| `## Output` | 하위가 명시하면 대체, 미명시 시 상속 |
| `## Collaboration` | 하위가 명시하면 대체, 미명시 시 상속 |
| `## Permission` | 기본값 가이드. instance frontmatter가 최종 결정 |

### Permission 해소 우선순위

```
act.md [Permission] (기본값)
    ↓ 하위가 명시하면 대체
하위 ACT class [Permission]
    ↓ instance frontmatter가 있으면 대체
instance frontmatter (model, tools, permissionMode, boundary)
```

**Permission 기본값:**
- model: sonnet
- permissionMode: bypassPermissions
- tools: Read, Grep, Glob

---

## Instance → 네이티브 Frontmatter 매핑

### 변환 테이블

| Smith 필드 | 네이티브 필드 | 변환 규칙 |
|----------|-------------|---------|
| `type` | (제거) | 컴파일 후 불필요 |
| `agent-system` | (제거) | 컴파일 후 불필요 |
| `schema` | (제거) | 컴파일 후 불필요 |
| `extends` | (제거) | 체인 해석 완료 |
| `state` | (제거) | 컴파일 완료, 본문에 반영 |
| `act` | (제거) | 컴파일 완료, 본문에 반영 |
| `name` | `name` | 그대로 (충돌 시 변환) |
| `description` | `description` | 그대로 |
| `model` | `model` | instance > ACT > 기본값 |
| `tools` | `tools` | instance > ACT > 기본값 |
| `permissionMode` | `permissionMode` | instance > ACT > bypassPermissions |
| `boundary` | 본문 포함 | 프론트매터에서 제거, 본문에 기술 |
| `maxTurns` | `maxTurns` | 그대로 |
| `memory` | `memory` | 그대로 (있을 경우) |
| `skills` | `skills` | 그대로 (있을 경우) |
| `isolation` | `isolation` | 그대로 (있을 경우) |
| `mcpServers` | `mcpServers` | 그대로 (있을 경우) |

### disallowedTools 자동 계산

```
전체 도구 = [Read, Write, Edit, Bash, Grep, Glob]
disallowedTools = 전체 도구 - tools
```

예시:
- tools: [Read, Grep, Glob, Bash] → disallowedTools: [Write, Edit]
- tools: [Read, Write, Edit, Bash, Grep, Glob] → disallowedTools: []

---

## 이름 충돌 해소

### 빌트인 에이전트 충돌

| 충돌 이름 | 변환 | 이유 |
|----------|------|------|
| `explore` | `scout` | Claude Code Explore 빌트인 |

### 프로젝트 에이전트 네이밍

프로젝트 에이전트(`--project`)는 `{project}-` 접두사를 사용한다:
- `project-dev`
- `project-reviewer`

이 접두사로 플러그인 에이전트와의 충돌을 방지한다.

---

## 경로 해석 규칙

| 패턴 | 해석 |
|------|------|
| `state/...` | `${CLAUDE_PLUGIN_ROOT}/plugins/smith/agents/state/...` |
| `act/...` | `${CLAUDE_PLUGIN_ROOT}/plugins/smith/agents/act/...` |
| `smith/...` | `${CLAUDE_PLUGIN_ROOT}/plugins/smith/agents/...` |
| `./...` | 프로젝트 루트 기준 |
| 절대 경로 | 그대로 사용 |
| `${CLAUDE_PLUGIN_ROOT}/...` | 플러그인 루트 기준 |
