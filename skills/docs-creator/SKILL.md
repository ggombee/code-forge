---
name: docs-creator
description: Claude Code 문서 작성. CLAUDE.md, SKILL.md, COMMAND.md 효율적 작성.
metadata:
  version: '1.0.0'
---

# Docs Creator Skill

> 고밀도, 실행 가능, 유지보수 가능한 문서 작성

---

## 트리거 조건

| 상황            | 작성 필요   |
| --------------- | ----------- |
| **새 프로젝트** | CLAUDE.md   |
| **새 스킬**     | SKILL.md    |
| **새 커맨드**   | COMMAND.md  |
| **규칙 추가**   | rules/\*.md |

---

## 병렬 에이전트 실행

### 핵심 원칙

| 원칙            | 방법                           | 효과        |
| --------------- | ------------------------------ | ----------- |
| **PARALLEL**    | 단일 메시지 여러 에이전트 호출 | 5-10배 속도 |
| **DELEGATE**    | 전문 에이전트 즉시 위임        | 품질 향상   |
| **SMART MODEL** | 작업 복잡도별 모델             | 비용 최적화 |

```typescript
// 순차 (120초)
Task(...) // 60초
Task(...) // 60초

// 병렬 (60초) - 단일 메시지
Task(subagent_type="explore", model="haiku", prompt="프로젝트 구조 분석")
Task(subagent_type="explore", model="haiku", prompt="기존 규칙 분석")
```

---

## 금지 패턴

| 분류       | 금지                              |
| ---------- | --------------------------------- |
| **설명**   | 장황, 중복, Claude가 아는 것 반복 |
| **구조**   | XML 태그 없음, 모호한 지시        |
| **표현**   | 부정형 (Don't X → Do Y)           |
| **복잡도** | 조건문, 엣지 케이스 나열          |
| **강조**   | CRITICAL/MUST 남발                |

---

## 필수 패턴

| 분류     | 필수                       |
| -------- | -------------------------- |
| **구조** | XML 태그 섹션, 명확한 계층 |
| **표현** | 표 형식, 마커              |
| **예시** | 코드 중심, 복사 가능       |
| **로딩** | @imports just-in-time      |
| **지시** | 긍정형, 명시적             |
| **버전** | 라이브러리 버전 명시       |

---

## 문서 템플릿

### CLAUDE.md

````markdown
# CLAUDE.md - [프로젝트명]

<instructions>
@path/to/common.md
@.claude/docs/library/[lib]/index.md
</instructions>

---

<forbidden>
| 분류 | 금지 |
|------|------|
| **Git** | AI 표시, 이모지 |
</forbidden>

---

<required>
| 분류 | 필수 |
|------|------|
| **타입** | 명시적 return type |
</required>

---

<tech_stack>
| 기술 | 버전 | 주의 |
|------|------|------|
| TypeScript | 5.x | strict |
</tech_stack>

---

<quick_patterns>

```typescript
// 복사 가능 패턴
const fn = (): ReturnType => { ... }
```

</quick_patterns>

````

---

### SKILL.md

```markdown
---
name: skill-name
description: 한 줄 설명
---

<trigger_conditions>
| 트리거 | 반응 |
|--------|------|
| "키워드" | 즉시 실행 |
</trigger_conditions>

---

<workflow>
<step number="1">
<action>작업</action>
<tools>Tool1</tools>
</step>
</workflow>

---

<examples>
```typescript
// 실행 가능 코드
````

</examples>
```

---

### COMMAND.md

```markdown
---
description: 커맨드 설명
allowed-tools: Read, Edit
argument-hint: <인자>
---

<purpose>
구체적 목표
</purpose>

---

<workflow>
실행 단계
</workflow>

---

<examples>
비교
</examples>
```

---

## 워크플로우

| Step  | 작업                                        | 도구       |
| ----- | ------------------------------------------- | ---------- |
| **1** | 유형 결정, 구조 파악                        | Glob, Read |
| **2** | 규칙 추출 (forbidden → required → patterns) | Grep       |
| **3** | 작성 (XML 태그, 표, 코드, @imports)         | Write      |
| **4** | 검증 (체크리스트)                           | -          |

---

## 검증 체크리스트

| 항목       | 기준        | 검증    |
| ---------- | ----------- | ------- |
| **토큰**   | 500줄 이하  | wc -l   |
| **XML**    | 올바른 중첩 | 수동    |
| **예시**   | 실행 가능   | 테스트  |
| **긍정형** | Don't < 5   | grep -c |

**최종 확인:**

- [ ] XML 태그 섹션 구분
- [ ] 표 형식 압축
- [ ] 코드 예시 실행 가능
- [ ] 마커
- [ ] @imports 중복 제거
- [ ] 버전 명시
- [ ] 긍정형 지시

---

## Best Practices

| 원칙                  | 방법            |
| --------------------- | --------------- |
| **Show, Don't Tell**  | 설명 < 코드     |
| **High Density**      | 1줄당 최대 정보 |
| **Copy-Paste Ready**  | 바로 사용 가능  |
| **Version Explicit**  | 버전 명시       |
| **Positive Language** | Do X > Don't Y  |

---

## 참조 문서

| 문서                                                    | 용도      |
| ------------------------------------------------------- | --------- |
| `@${CLAUDE_PLUGIN_ROOT}/instructions/multi-agent/coordination-guide.md` | 병렬 실행 |
| `@${CLAUDE_PLUGIN_ROOT}/instructions/validation/forbidden-patterns.md`  | 금지 패턴 |
