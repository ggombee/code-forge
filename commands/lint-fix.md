---
description: tsc/eslint 오류 검사 및 수정. @lint-fixer 에이전트 사용.
argument-hint: [파일/디렉토리 경로...]
---

@../instructions/multi-agent/coordination-guide.md

# Lint Fix Command

> @lint-fixer 에이전트를 사용하여 tsc/eslint 오류를 자동으로 수정.

## 필수 사항

```typescript
Task(subagent_type="lint-fixer", model="haiku", prompt=`
  수행할 작업:
  1. tsc + eslint 병렬 검사
  2. 오류 분류 (간단/복잡)
  3. TodoWrite로 오류 목록 생성
  4. 간단한 오류: 즉시 수정
  5. 복잡한 오류: 분석 후 수정
  6. 전체 재검사로 완료 확인
`)
```

## 병렬 검사 (필수)

```bash
# 단일 메시지에서 동시 호출
npx tsc --noEmit    # TypeScript 타입 체크
npx eslint .        # ESLint 체크
```

## 우선순위

| 우선순위 | 유형 |
|----------|------|
| 1 | 타입 오류 (컴파일 차단) |
| 2 | 린트 오류 (error 레벨) |
| 3 | 린트 경고 (warning 레벨) |

## 금지 사항

- `any` 타입, `@ts-ignore`, `eslint-disable` 남발
- 여러 오류 동시 수정
- 분석 없이 급하게 수정
