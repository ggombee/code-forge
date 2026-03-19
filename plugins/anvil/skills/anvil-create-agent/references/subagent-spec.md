# Claude Code Subagent 스펙

Anvil 에이전트 생성 시 참조하는 Claude Code subagent 정의 규격.

## 파일 형식

YAML frontmatter + Markdown body. Body는 subagent의 시스템 프롬프트가 된다.

```markdown
---
name: agent-name
description: 설명
---

시스템 프롬프트 내용
```

## Frontmatter 필드

| 필드 | 필수 | 타입 | 설명 |
|------|------|------|------|
| `name` | Yes | string | 소문자 + 하이픈 고유 식별자 |
| `description` | Yes | string | Claude가 이 subagent에 위임할 시기를 판단하는 설명. 적극적 위임이 필요하면 "use proactively" 등 포함 |
| `tools` | No | string (쉼표 구분) | 사용 가능한 도구 허용 목록. 생략하면 모든 도구 상속 |
| `disallowedTools` | No | string (쉼표 구분) | 거부할 도구. 상속/지정된 목록에서 제거 |
| `model` | No | enum | `sonnet`, `opus`, `haiku`, `inherit`. 기본값 `inherit` |
| `permissionMode` | No | enum | `default`, `acceptEdits`, `dontAsk`, `bypassPermissions`, `plan` |
| `maxTurns` | No | number | 최대 에이전트 턴 수 |
| `skills` | No | list | 시작 시 컨텍스트에 로드할 skill 이름 목록. 부모에서 상속되지 않음 |
| `mcpServers` | No | list/object | 사용 가능한 MCP 서버. 이름 문자열 또는 인라인 정의 |
| `hooks` | No | object | subagent 라이프사이클 hooks (PreToolUse, PostToolUse, Stop) |
| `memory` | No | enum | 지속적 메모리 범위: `user`, `project`, `local` |
| `background` | No | boolean | 항상 백그라운드 실행. 기본값 `false` |
| `isolation` | No | enum | `worktree` — 임시 git worktree에서 실행 |

## 파일 위치 및 우선순위

| 위치 | 범위 | 우선순위 |
|------|------|----------|
| `--agents` CLI 플래그 | 현재 세션 | 1 (최고) |
| `.claude/agents/` | 현재 프로젝트 | 2 |
| `~/.claude/agents/` | 모든 프로젝트 | 3 |
| 플러그인 `agents/` | 플러그인 활성화 범위 | 4 (최저) |

같은 이름의 subagent가 여러 위치에 있으면 높은 우선순위가 우선.

## tools 필드 상세

### 기본 도구 목록
Read, Write, Edit, Glob, Grep, Bash, Agent, NotebookEdit 등 Claude Code 내부 도구 + MCP 도구.

### Agent 도구 제한
- `Agent(worker, researcher)` — 특정 subagent만 생성 허용
- `Agent` (괄호 없음) — 모든 subagent 생성 허용
- `Agent` 생략 — subagent 생성 불가

### 도구 거부
```yaml
disallowedTools: Write, Edit
```
또는 설정에서:
```json
{ "permissions": { "deny": ["Agent(Explore)", "Agent(my-agent)"] } }
```

## permissionMode 상세

| 모드 | 동작 |
|------|------|
| `default` | 표준 권한 확인 프롬프트 |
| `acceptEdits` | 파일 편집 자동 수락 |
| `dontAsk` | 권한 프롬프트 자동 거부 (명시 허용 도구만 작동) |
| `bypassPermissions` | 모든 권한 확인 건너뛰기 (주의) |
| `plan` | 읽기 전용 탐색 모드 |

부모가 `bypassPermissions`이면 자식이 재정의 불가.

## memory 필드 상세

| 범위 | 저장 위치 | 용도 |
|------|----------|------|
| `user` | `~/.claude/agent-memory/<name>/` | 모든 프로젝트에서 학습 유지 |
| `project` | `.claude/agent-memory/<name>/` | 프로젝트별, 버전 제어 공유 가능 |
| `local` | `.claude/agent-memory-local/<name>/` | 프로젝트별, 버전 제어 제외 |

활성화 시:
- 시스템 프롬프트에 메모리 디렉토리 읽기/쓰기 지침 포함
- `MEMORY.md`의 처음 200줄이 컨텍스트에 포함
- Read, Write, Edit 도구 자동 활성화

## hooks 필드 상세

subagent frontmatter에 직접 정의하는 hooks:

| 이벤트 | Matcher 입력 | 실행 시기 |
|--------|-------------|----------|
| `PreToolUse` | 도구 이름 | subagent가 도구 사용 전 |
| `PostToolUse` | 도구 이름 | subagent가 도구 사용 후 |
| `Stop` | (없음) | subagent 완료 시 (런타임에 SubagentStop으로 변환) |

```yaml
hooks:
  PreToolUse:
    - matcher: "Bash"
      hooks:
        - type: command
          command: "./scripts/validate.sh"
  PostToolUse:
    - matcher: "Edit|Write"
      hooks:
        - type: command
          command: "./scripts/lint.sh"
```

## skills 필드 상세

```yaml
skills:
  - api-conventions
  - error-handling-patterns
```

- 전체 skill 콘텐츠가 subagent 컨텍스트에 주입됨
- 호출 가능하게 등록되는 것이 아니라 시스템 프롬프트에 포함
- 부모 대화에서 skill을 상속하지 않으므로 명시적으로 나열 필요

## Anvil 확장 Frontmatter

Anvil 전용 필드 (`type`, `schema`, `extends`)와 Body 섹션 규격, Claude Code 필드와의 조합 규칙은 `plugins/anvil/rules/anvil-rules.md`에 정의되어 있다. 에이전트 생성 시 해당 문서를 함께 참조한다.

## 설계 원칙

- 각 subagent는 하나의 역할에 집중
- description을 구체적으로 작성 (Claude가 위임 시기를 판단하는 기준)
- 도구는 필요한 것만 부여 (최소 권한)
- subagent는 다른 subagent를 생성할 수 없음 (중첩 불가)
