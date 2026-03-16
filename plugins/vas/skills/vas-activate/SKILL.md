---
name: vas-activate
description: VAS 에이전트 정의를 로드하고 STATE/ACT 상속 체인을 해석하여 세션 제약으로 적용한다.
agent-system: VAS
disable-model-invocation: true
version: 5.0.0
---

# VAS Agent Activation

사용자가 `/vas-activate`를 호출하거나 SessionStart에서 VAS_STATUS=enabled일 때 아래 절차를 수행한다.

## Step 1: 에이전트 전환

플러그인 내부에서 `agents/` 디렉토리의 심링크를 교체한다.

```bash
${CLAUDE_PLUGIN_ROOT}/hooks/session.sh start
```

`session.sh`가 VAS 설정을 읽고 `agents/` 내 심링크를 `_agents/`(VAS) 또는 `agents-default/`(기본)로 전환한다.

**에이전트 소스:**
- VAS off: `${CLAUDE_PLUGIN_ROOT}/agents-default/` (기본 에이전트)
- VAS on: `${CLAUDE_PLUGIN_ROOT}/plugins/vas/agents/_agents/` (VAS 에이전트)

모든 전환은 플러그인 내부(`agents/` 디렉토리)에서 완결된다. 프로젝트 디렉토리에 파일을 심지 않는다.

## Step 2: VAS 해석 규칙 로드

VAS 규칙 파일을 읽어 세션에 적용한다:

```
${CLAUDE_PLUGIN_ROOT}/plugins/vas/rules/vas-rules.md
```

이 파일은 플러그인 내부에 있으며, VAS 에이전트 spawn 시 해석 규칙으로 사용된다.

## Step 3: 에이전트 로드

**중요: `type: instance`이면서 `agent-system: VAS`인 에이전트만 VAS 방식으로 활성화한다.**

### 에이전트 지정 시

1. 지정된 에이전트 파일을 읽고 YAML frontmatter를 파싱한다
2. `type: instance`, `agent-system: VAS`인지 확인한다
3. **STATE 해석**:
   - `state` 배열의 각 경로를 순서대로 읽는다
   - 각 STATE class의 `extends` 체인을 재귀적으로 따라가며 규칙을 합산한다
   - 동일 `[Key]` 충돌 시 배열 뒤쪽이 우선한다
   - instance body의 규칙이 최종 우선순위를 가진다
4. **ACT 해석**:
   - `act` 경로의 ACT class를 읽는다
   - `extends` 체인을 재귀적으로 따라가며 Workflow/Trigger/Verification/Output/Collaboration을 해석한다
5. **Permission 확정**:
   - ACT class의 `## Permission` 섹션에서 `[Model]`, `[PermissionMode]`, `[Tools]`를 추출한다
   - instance frontmatter에 명시된 값이 있으면 ACT class 값을 override한다
   - `boundary`는 instance frontmatter에서 가져온다
   - `permissionMode` 미지정 시 기본값: `bypassPermissions`
6. **활성화 결과 출력**:
   - 로드된 STATE class 목록
   - 적용된 ACT class
   - 최종 Permission (model, permissionMode, tools, boundary)
   - 합산된 Must/Never/Should 규칙 수

### 에이전트 미지정 시

아래 경로에서 `type: instance` 에이전트만 필터링하여 목록을 보여준다:
- 프로젝트 로컬: `./.agents/agents/`
- VAS 기본: `${CLAUDE_PLUGIN_ROOT}/plugins/vas/agents/_agents/`

목록에 다음 정보를 포함한다:
- 에이전트 이름
- state 조합 요약
- act 참조
- model

## Step 4: 세션 종료 시 정리

`session.sh end`가 `agents/` 심링크를 `agents-default/`로 복원한다. 프로젝트 디렉토리를 건드리지 않는다.
