# Smith Build Output Template

컴파일된 에이전트 파일의 출력 형식 정의.

---

## 파일 구조

```markdown
---
name: {컴파일된 이름}
description: {instance description}
tools: {컴파일된 tools, 쉼표 구분}
disallowedTools: {자동 계산된 거부 도구 배열}
model: {컴파일된 model}
permissionMode: {컴파일된 permissionMode}
maxTurns: {instance maxTurns}
{memory: 값}       # 있을 경우만
{skills: [값]}     # 있을 경우만
{isolation: 값}    # 있을 경우만
---

{@${CLAUDE_PLUGIN_ROOT}/instructions/agent-patterns/parallel-execution.md}
{@${CLAUDE_PLUGIN_ROOT}/rules/coding-standards.md}

# {Name} Agent

{Persona [Identity]에서 추출한 한 줄 설명}

---

<purpose>

**목표:**
- {ACT Trigger/Workflow에서 추출한 목표 3-4개}

**사용 시점:**
- {ACT Trigger [When]에서 추출한 사용 시점 2-3개}

</purpose>

---

## Persona

- [Identity] {컴파일된 Persona Identity}
- [Mindset] {컴파일된 Persona Mindset}
- [Communication] {컴파일된 Persona Communication}

---

{에이전트별 고유 섹션}

---

<forbidden>

| 금지 | 이유 |
|------|------|
| **{Never Key}** | {Never 규칙 설명} |
{...모든 컴파일된 Never 규칙}

</forbidden>

---

<required>

| 필수 | 기준 |
|------|------|
| **{Must Key}** | {Must 규칙 설명} |
{...모든 컴파일된 Must 규칙}

</required>

---

{## Should 섹션 (있을 경우)}

---

<workflow>

{ACT Workflow 전체}

</workflow>

---

<output>

{ACT Output 형식}

</output>
```

---

## Instruction 참조 매핑 (4단계 권한 기준)

| 에이전트 단계 | 에이전트 | @참조 |
|-------------|---------|-------|
| READ-ONLY | analyst, architect, refactor-advisor, vision | 없음 |
| SHELL-ACCESS | scout, code-reviewer | parallel-execution.md |
| SHELL-ACCESS | git-operator, researcher | 없음 |
| EDIT-ONLY | lint-fixer, build-fixer | coding-standards.md |
| READ-WRITE-FULL | implementor, deep-executor, assayer, codex | parallel-execution.md, coding-standards.md |

---

## 에이전트별 고유 섹션 가이드

### analysis 카테고리
- 분석 도메인/카테고리 테이블
- 도구 선택 전략
- 에이전트 협업 매핑

### dev 카테고리
- 복잡도별 접근 테이블
- 에이전트 협업 매핑
- 검증 체크리스트

### quality 카테고리
- 심각도 분류 기준
- 체크리스트 항목
- 피드백 형식

### ops 카테고리
- 실행 모드
- 안전성 규칙
- 에러 처리 테이블

---

## 빌드 매니페스트 형식

```json
{
  "version": "2.0.0",
  "buildTime": "2026-03-17T00:00:00.000Z",
  "source": "${CLAUDE_PLUGIN_ROOT}/plugins/smith/agents/_agents/",
  "target": "${CLAUDE_PLUGIN_ROOT}/agents/",
  "agents": [
    {
      "name": "scout",
      "originalName": "explore",
      "source": "_agents/explore.md",
      "renamed": true,
      "stateChain": ["state/state.md", "state/role/developer.md"],
      "actChain": ["act/act.md", "act/analysis/explorer.md"],
      "model": "haiku",
      "tools": ["Read", "Grep", "Glob", "Bash"],
      "permissionMode": "bypassPermissions",
      "compiledMust": 12,
      "compiledNever": 5
    }
  ]
}
```
