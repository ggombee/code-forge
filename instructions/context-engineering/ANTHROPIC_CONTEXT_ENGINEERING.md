# Context Engineering for Claude

Anthropic 공식 가이드 기반 효과적인 Instructions 작성법.

**Sources:** [Effective Context Engineering](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents) · [Claude 4.x Best Practices](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-4-best-practices) · [XML Tags](https://console.anthropic.com/docs/en/build-with-claude/prompt-engineering/use-xml-tags)

---

<forbidden>

| 분류 | 금지 |
|------|------|
| **설명** | 장황한 설명, Claude가 아는 것 반복 |
| **구조** | 중복 정보, 모호한 지시사항 |
| **표현** | 부정형 ("Don't X"), 과도한 강조 (CRITICAL 남발) |
| **복잡도** | 복잡한 조건문, 모든 엣지 케이스 나열 |

</forbidden>

---

<required>

| 분류 | 필수 |
|------|------|
| **구조** | XML 태그 섹션 구분, 명확한 계층 |
| **표현** | 표 형식 압축, ✅/❌ 마커 |
| **예시** | 코드 중심, 복사 가능 패턴 |
| **로딩** | @imports로 just-in-time 로딩 |
| **지시** | 긍정형 명시적 지시 |

</required>

---

<core_principles>

| 원칙 | 방법 |
|------|------|
| **Right Altitude** | 명확한 원칙 + 예시 (조건문/엣지케이스 나열 ❌) |
| **Just-in-Time** | 필요 시점에만 정보 제공 (중복 제거) |
| **Explicit** | "Create X. Include Y and Z." (모호한 지시 ❌) |

**Details:** [references/core-principles.md](references/core-principles.md)

</core_principles>

---

<xml_patterns>

```xml
<!-- Instructions -->
<instructions>@path/to/guide.md</instructions>

<!-- Rules -->
<forbidden>절대 금지</forbidden>
<required>반드시 필수</required>

<!-- Examples -->
<examples>
  <example>
    <input>Input</input>
    <output>Output</output>
  </example>
</examples>

<!-- Thinking -->
<thinking>추론 과정</thinking>
<answer>최종 답변</answer>

<!-- Behavior -->
<default_to_action>Implement directly</default_to_action>
```

</xml_patterns>

---

<techniques>

| 기법 | 사용 시점 | 패턴 |
|------|----------|------|
| **CoT** | 복잡한 수학, 다단계 분석 | `<thinking>` → `<answer>` |
| **Extended** | 4D 시각화, 제약 최적화 | "철저히 생각. 여러 접근법 고려" (1024+ 토큰) |

**Details:** [references/techniques.md](references/techniques.md)

</techniques>

---

<claude_4x>

```xml
<!-- 명시적 지시 -->
"Create dashboard. Include as many features as possible."

<!-- 행동 제어 -->
<default_to_action>Implement directly</default_to_action>
<use_parallel_tool_calls>true</use_parallel_tool_calls>
```

**Details:** [references/claude-4x.md](references/claude-4x.md)

</claude_4x>

---

<quick_patterns>

```text
✅ "Create X with Y and Z" (명시적)
✅ 원하는 패턴 예시 코드
✅ XML/표로 구조화

❌ "Don't X" → ✅ "Do Y" (긍정형)
❌ "If X then Y, unless..." → ✅ "[예시] 패턴"
❌ CRITICAL 남발 → ✅ 일반 지시
```

</quick_patterns>

---

<document_template>

```xml
# Title

<instructions>@path/to/guides.md</instructions>

<forbidden>
[표 형식 금지]
</forbidden>

<required>
[표 형식 필수]
</required>

<patterns>
[복사 가능 코드]
</patterns>
```

| 위치 | 내용 | 크기 |
|------|------|------|
| 메인 | 핵심 + 요약 | 300줄 이하 |
| references/ | 상세 가이드 | 무제한 |

</document_template>

---

<examples>

```xml
<!-- Coding -->
<investigation>Read files before edits</investigation>
<implementation>Only requested changes</implementation>

<!-- Frontend -->
<aesthetics>Creative, distinctive (avoid generic AI look)</aesthetics>
```

**More:** [references/examples.md](references/examples.md)

</examples>

---

<sources>

**EN:** [Context Engineering](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents) · [Claude 4.x](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-4-best-practices) · [XML Tags](https://console.anthropic.com/docs/en/build-with-claude/prompt-engineering/use-xml-tags)

**KO:** [XML 태그](https://platform.claude.com/docs/ko/build-with-claude/prompt-engineering/use-xml-tags) · [CoT](https://platform.claude.com/docs/ko/build-with-claude/prompt-engineering/chain-of-thought) · [Extended Thinking](https://platform.claude.com/docs/ko/build-with-claude/prompt-engineering/extended-thinking-tips)

</sources>
