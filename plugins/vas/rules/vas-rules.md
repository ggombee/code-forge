---
agent-system: VAS
---

# VAS (Vibe-Agent-System) 해석 규칙

이 파일은 VAS 에이전트 정의 파일을 해석하는 방법을 정의한다. 에이전트 파일을 읽을 때 반드시 이 규칙을 따른다.

## File Format

모든 에이전트 파일은 YAML frontmatter + Markdown body 구조.

### Type System

| Type | 설명 |
|------|------|
| `interface` | 섹션 구조 정의. 지침사항이 아님. `${CLAUDE_PLUGIN_ROOT}/plugins/vas/agents/interface/`에 위치 |
| `class` | 상속 가능한 규칙 정의. 직접 활성화 불가 |
| `instance` | 실제 활성화 대상. STATE 조합 + ACT 참조 |

### Interface 종류

| Interface | 용도 | 섹션 |
|-----------|------|------|
| `state-agent` | "무엇을 아는가" | Persona, Must, Never, Should, Override |
| `act-agent` | "무엇을 하는가" | Trigger, Workflow, Verification, Output, Collaboration, Permission |

### Frontmatter Fields

**VAS 전용 fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `type` | string | Yes | `interface`, `class`, `instance` |
| `name` | string | Yes | 에이전트 식별자 |
| `schema` | string | Yes (class) | interface 파일 경로. 구조 정의 참조 |
| `extends` | string/string[] | No | 부모 class 경로. 상속 처리 |
| `state` | string[] | instance only | STATE class 경로 배열. 여러 STATE 조합 |
| `act` | string | instance only | ACT class 경로. 단일 값 |
| `model` | string | instance only | 사용 모델 (opus/sonnet/haiku) |
| `tools` | string[] | instance only | 사용 가능 도구 허용 목록 |
| `boundary` | string[] | instance only | 행동 범위 제한 |

**Claude Code 표준 fields (VAS와 함께 사용 가능):**

| Field | Description |
|-------|-------------|
| `description` | Claude가 subagent 위임 시기를 판단하는 설명 |
| `disallowedTools` | 거부할 도구 |
| `permissionMode` | `default`, `acceptEdits`, `dontAsk`, `bypassPermissions`, `plan` |
| `maxTurns` | 최대 에이전트 턴 수 |
| `mcpServers` | 사용 가능한 MCP 서버 |
| `hooks` | subagent 라이프사이클 hooks |
| `memory` | 지속적 메모리 범위: `user`, `project`, `local` |
| `background` | 백그라운드 실행. 기본값 `false` |
| `isolation` | `worktree` — 임시 git worktree에서 실행 |

## STATE 해석 규칙

### 합산 규칙 (Union)

여러 STATE를 조합할 때 모든 규칙은 **합산(union)**된다.

- 각 STATE의 Must/Never/Should 규칙은 전부 유효하다
- 동일 `[Key]`가 충돌하는 경우에만 배열 뒤쪽 STATE가 **우선**한다
- 어떤 STATE의 규칙도 명시적 충돌 없이 무시되지 않는다
- instance body에 같은 키 작성 시 최종 우선순위를 가진다

**우선순위 (낮음 → 높음):**

```
state.md (추상) → extends 체인 상위 → extends 체인 하위 → state 배열 앞 → state 배열 뒤 → instance body
```

### Override 규칙

`## Override` 섹션만이 상속된 규칙을 대체할 수 있다:

```markdown
## Override
### Must
- [Key] 이 규칙이 상속된 모든 Must [Key] 규칙을 대체한다
```

- Override에 명시되지 않은 섹션/Key는 그대로 누적 유지
- Override 자체도 상속된다

### Persona 규칙

`## Persona`는 예외. Instance의 Persona가 상속된 Persona를 대체한다.

## ACT 해석 규칙

### Override 불가

ACT는 instance에서 override할 수 없다. 워크플로우를 변경하려면 새로운 ACT class를 작성한다.

### extends 시 상속

ACT class 간 extends 체인에서:
- **Workflow**: 하위 class가 전체 재작성 (부분 override 아님)
- **Permission**: 하위가 명시하면 상위를 대체, 미명시 시 상속
- **나머지 섹션**: 하위가 명시하면 상위를 대체, 미명시 시 상속

### Permission → Instance Frontmatter

ACT class body의 Permission 섹션은 **기본값 가이드**이다.
실제 제약은 instance frontmatter의 `model`, `tools`, `boundary` 필드가 확정한다.

## Instance 해석

1. `state` 배열의 각 STATE class를 순서대로 해석
   - 각 STATE의 extends 체인을 재귀적으로 따라감
   - 모든 규칙을 합산 (동일 키 충돌 시 뒤쪽 우선)
2. instance body의 규칙이 최종 우선순위
3. `act` 필드의 ACT class를 해석
   - extends 체인을 재귀적으로 따라감
   - Workflow, Trigger, Verification, Output, Collaboration 적용
4. instance frontmatter의 `model`, `tools`, `boundary`가 최종 Permission 확정

## Activation Rule

**`type: instance` 에이전트만 활성화할 수 있다.** `class`와 `interface`는 상속/구조 정의 전용.

## VAS 에이전트 식별

frontmatter에 `agent-system: VAS`를 가진 파일만 VAS 에이전트로 인식한다. 이 필드가 없는 에이전트 파일은 VAS 해석 규칙을 적용하지 않는다.

```yaml
---
agent-system: VAS  # ← 이 필드가 있어야 VAS 에이전트
type: instance
name: my-agent
...
---
```

## Spawn Rule

**VAS가 활성화된 세션에서는 작업 수행 시 반드시 Agent 도구로 VAS 에이전트를 spawn한다.**

- `agent-system: VAS`를 가진 instance만 VAS spawn 대상이다
- 메인 에이전트가 직접 작업하지 않고, 활성화된 VAS instance를 subagent로 위임한다
- spawn 시 VAS instance의 해석 결과(STATE 규칙 합산 + ACT 워크플로우)를 system prompt로 전달한다
- instance frontmatter의 `model`, `tools`, `boundary`, `permissionMode`를 Agent 도구 파라미터에 반영한다
  - `permissionMode` → Agent 도구의 `mode` 파라미터로 매핑
  - `permissionMode` 미지정 시 기본값: `bypassPermissions`

## Agent 저장 위치

| 범위 | 경로 |
|------|------|
| VAS 추상 (interface/class) | `agents/` |
| Global instance | `agents/` |
| Project instance | `./.agents/agents/` |
| Project class (로컬 확장) | `./.agents/vas/` |

## 경로 해석

- `vas/` 시작 경로 → `agents/` 기준으로 해석
- `./` 시작 경로 → 프로젝트 루트 기준으로 해석
- 절대 경로 → 그대로 사용
- 참조할 수 없는 파일 경로 → 누락 보고, 추측하거나 건너뛰지 않음
