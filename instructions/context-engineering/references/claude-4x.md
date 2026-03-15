# Claude 4.x Specifics

Claude 4.x 모델의 특징과 효과적 사용법.

## 핵심 차이점

### Precise Instruction Following

Claude 4.x는 **문자 그대로** 지시를 따름.

| 상황 | Claude 3.x | Claude 4.x |
|------|-----------|-----------|
| "Create dashboard" | 추가 기능 자동 포함 | 최소한만 구현 |
| "Suggest changes" | 때때로 바로 구현 | 제안만 |
| "Fix bug" | 주변 코드도 개선 | 버그만 수정 |
| "Add feature X" | X + 관련 기능들 | X만 |

**결론:** 더 명시적으로 작성 필요.

---

## Action Control

### 적극적 행동 유도

```xml
<default_to_action>
Implement changes directly rather than suggesting.
When you identify an issue, fix it immediately.
Go beyond the minimum to create comprehensive solutions.
</default_to_action>
```

**사용 시점:** 빠른 프로토타이핑, 완전한 구현, 제안보다 실행 선호

### 보수적 행동 유도

```xml
<do_not_act_before_instructions>
Wait for explicit user instruction before taking action.
Only suggest changes, never implement without confirmation.
Ask for permission before modifying files.
</do_not_act_before_instructions>
```

**사용 시점:** 민감한 코드베이스, 검토 필요, 탐색적 작업

---

## Parallel Tool Calling

독립적 도구 호출을 병렬로 실행.

```xml
<use_parallel_tool_calls>
Call independent tools in parallel for maximum speed.
If operations don't depend on each other, run them simultaneously.
</use_parallel_tool_calls>
```

```text
❌ 순차: Read file1 → Read file2 → Read file3
✅ 병렬: Read [file1, file2, file3] 동시에
```

---

## Explicit Instruction Patterns

```text
❌ "Create user profile page"
✅ "Create comprehensive user profile page:
   - Avatar upload with preview
   - Editable fields (name, email, bio)
   - Password change form
   - Activity history
   - Settings panel
   Include all standard profile features."

❌ "Optimize this component"
✅ "Optimize this component. Apply:
   - useMemo for expensive calculations
   - useCallback for event handlers
   - React.memo for child components
   - Code splitting if bundle > 100kb
   Maximize performance improvements."

❌ "Refactor this code"
✅ "Refactor this code to improve:
   - Extract reusable logic into hooks
   - Separate concerns into modules
   - Add TypeScript types
   - Improve naming clarity
   Follow modern React patterns."
```

---

## Completeness Control

### 최소 구현 방지

```xml
<avoid_minimal_implementation>
Don't create placeholder or minimal implementations.
Build complete, production-ready solutions.
Include error handling, loading states, and edge cases.
</avoid_minimal_implementation>
```

---

## Testing & Validation

```text
❌ "Add tests"
✅ "Add comprehensive tests:
   - Unit tests for all functions
   - Integration tests for API calls
   - Edge cases and error scenarios
   Aim for 80%+ code coverage."
```

---

## Anti-Patterns

```text
❌ "Make it better" → 아무것도 안 함 (모호함)
✅ "Improve by adding X, Y, Z features"

❌ "Fix issues" → 최소한만
✅ "Fix all issues. Address root causes. Add safeguards."

❌ "Update design" → 최소 변경
✅ "Update design completely. Modern UI. Smooth animations."
```

---

## 요약

| 규칙 | 방법 |
|------|------|
| **명시성** | "Create X with Y and Z" |
| **행동 제어** | `<default_to_action>` or `<do_not_act>` |
| **병렬화** | `<use_parallel_tool_calls>` |
| **완전성** | "Include all features. Go beyond basics." |
