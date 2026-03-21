---
name: smith-build
description: Smith 인스턴스를 빌드타임 컴파일하여 플랫 .md 에이전트 파일을 생성한다. "Smith 빌드", "에이전트 컴파일", "smith build" 등의 요청에 사용한다.
category: setup
agent-system: Smith
version: 1.0.0
---

# Smith Build — Build-Time Compilation

Smith 인스턴스(_agents/*.md)를 정적 .md 파일로 컴파일한다.

**비유:** TypeScript → tsc → .js 와 같이, Smith 템플릿 → /smith-build → 플랫 .md

## References

- `references/compilation-spec.md` — STATE/ACT 컴파일 시맨틱 상세
- `references/output-template.md` — 출력 파일 템플릿

## 빌드 모드

```
/smith-build                  # 전체 빌드: _agents/ → agents/
/smith-build --validate       # 검증만, 출력 없음
/smith-build --project        # 프로젝트 에이전트 빌드: .agents/agents/ → .claude/agents/
/smith-build --regenerate     # 수동 편집 보존하며 재빌드
```

## Pipeline

### Step 1: 소스 파일 수집

**전체 빌드 모드 (기본):**
```
소스: ${CLAUDE_PLUGIN_ROOT}/plugins/smith/agents/_agents/*.md
출력: ${CLAUDE_PLUGIN_ROOT}/agents/
```

**프로젝트 빌드 모드 (--project):**
```
소스: ./.agents/agents/*.md (type: instance만)
출력: ./.claude/agents/
```

1. 소스 디렉토리의 모든 .md 파일을 읽는다
2. frontmatter에서 `type: instance`이고 `agent-system: Smith`인 파일만 필터링한다
3. 유효하지 않은 파일은 경고를 출력하고 건너뛴다

### Step 2: STATE 체인 컴파일

각 인스턴스의 `state` 배열을 순서대로 해석한다.

1. **extends 체인 재귀 해석**:
   - 각 STATE class의 `extends` 필드를 따라 루트(state.md)까지 재귀적으로 올라간다
   - 각 레벨에서 Persona, Must, Never, Should, Override 섹션을 추출한다

2. **합산 규칙 (Union)**:
   - 모든 규칙은 합산된다 (union)
   - 동일 `[Key]`가 충돌할 때만 뒤쪽이 우선한다
   - Override 섹션의 규칙은 상속된 같은 Key를 대체한다

3. **우선순위** (낮음 → 높음):
   ```
   state.md (추상) → extends 상위 → extends 하위 → state[] 앞 → state[] 뒤 → instance body
   ```

4. **Persona 규칙**: instance body의 Persona가 있으면 상속된 Persona를 대체한다

### Step 3: ACT 체인 컴파일

인스턴스의 `act` 필드에서 ACT class를 해석한다.

1. **extends 체인 해석**:
   - ACT class의 `extends`를 따라 루트(act.md)까지 올라간다
   - Trigger, Workflow, Verification, Output, Collaboration, Permission 섹션을 추출한다

2. **상속 규칙**:
   - **Workflow**: 하위 class가 전체 재작성 (부분 override 아님)
   - **Permission**: 하위가 명시하면 대체, 미명시 시 상속
   - **나머지**: 하위가 명시하면 대체, 미명시 시 상속

### Step 4: 네이티브 frontmatter 매핑

Smith 필드를 Claude Code 네이티브 frontmatter로 변환한다.

**매핑 테이블:**

| Smith 필드 | 네이티브 필드 | 소스 |
|----------|-------------|------|
| `name` | `name` | instance frontmatter |
| `description` | `description` | instance frontmatter |
| `model` | `model` | instance > ACT Permission > 기본값(sonnet) |
| `tools` | `tools` | instance > ACT Permission > 기본값(Read, Grep, Glob) |
| `permissionMode` | `permissionMode` | instance > ACT Permission > 기본값(bypassPermissions) |
| `maxTurns` | `maxTurns` | instance frontmatter |
| `boundary` | 본문에 포함 | instance frontmatter |
| `memory` | `memory` | instance frontmatter (있을 경우) |
| `skills` | `skills` | instance frontmatter (있을 경우) |
| `isolation` | `isolation` | instance frontmatter (있을 경우) |

**제거 필드** (컴파일 후 불필요):
- `type`, `agent-system`, `schema`, `extends`, `state`, `act`

**disallowedTools 자동 계산:**
- 전체 도구 목록: `[Read, Write, Edit, Bash, Grep, Glob]`
- `tools`에 없는 도구를 `disallowedTools`에 추가한다

### Step 5: 이름 충돌 검증

Claude Code 빌트인 에이전트와 이름 충돌을 검증한다.

| 충돌 이름 | 변환 이름 | 이유 |
|----------|----------|------|
| `explore` | `scout` | Claude Code Explore 빌트인 에이전트와 충돌 |

프로젝트 에이전트(`--project`)는 `{project}-` 접두사를 사용하므로 충돌 가능성이 낮다.

### Step 6: 플랫 .md 파일 생성

`references/output-template.md`의 템플릿에 따라 컴파일된 에이전트 파일을 생성한다.

**instruction 참조 매핑 (4단계 권한 기준):**

| 에이전트 단계 | 에이전트 | instruction 참조 |
|-------------|---------|----------------|
| READ-ONLY | analyst, architect, refactor-advisor, vision | 없음 |
| SHELL-ACCESS | scout, code-reviewer | parallel-execution |
| SHELL-ACCESS | git-operator, researcher | 없음 |
| EDIT-ONLY | lint-fixer, build-fixer | coding-standards |
| READ-WRITE-FULL | implementor, deep-executor, testgen, codex | parallel-execution, coding-standards |

### Step 7: 빌드 매니페스트 생성

`agents/.smith-build-manifest.json`에 빌드 메타데이터를 기록한다.

```json
{
  "version": "2.0.0",
  "buildTime": "ISO 8601 타임스탬프",
  "source": "_agents/ 또는 .agents/agents/",
  "agents": [
    {
      "name": "scout",
      "source": "_agents/explore.md",
      "renamed": true,
      "stateChain": ["state/state.md", "state/role/developer.md"],
      "actChain": ["act/act.md", "act/analysis/explorer.md"],
      "model": "haiku",
      "permissionMode": "bypassPermissions"
    }
  ]
}
```

## --validate 모드

출력 파일을 생성하지 않고 검증만 수행한다.

**검증 항목:**
1. 모든 인스턴스 파일 파싱 가능
2. STATE 경로가 유효하고 extends 체인이 순환하지 않음
3. ACT 경로가 유효하고 extends 체인이 순환하지 않음
4. 이름 충돌 없음 (빌트인 + 인스턴스 간)
5. 필수 frontmatter 필드 존재 (type, name, agent-system, state, act)

**출력:**
```
✅ Smith Build Validation

인스턴스: 14개 파싱 완료
STATE 체인: 14개 해석 완료 (순환 없음)
ACT 체인: 14개 해석 완료 (순환 없음)
이름 충돌: 1개 (explore → scout 자동 변환)
검증 결과: PASS
```

## --regenerate 모드

기존 컴파일된 파일이 있을 때 수동 편집을 보존하며 재빌드한다.

1. 기존 agents/*.md 파일의 수동 편집 여부를 감지한다
   - `.smith-build-manifest.json`의 빌드 시간과 파일 수정 시간을 비교
2. 수동 편집된 파일은 건너뛰고 경고를 출력한다
3. 수동 편집되지 않은 파일만 재빌드한다

## 에러 처리

| 상황 | 대응 |
|------|------|
| STATE 경로 파일 없음 | 에러 출력, 해당 인스턴스 건너뜀 |
| ACT 경로 파일 없음 | 에러 출력, 해당 인스턴스 건너뜀 |
| extends 체인 순환 | 에러 출력, 해당 인스턴스 건너뜀 |
| frontmatter 파싱 실패 | 에러 출력, 해당 인스턴스 건너뜀 |
| 출력 디렉토리 없음 | 디렉토리 생성 후 계속 |
