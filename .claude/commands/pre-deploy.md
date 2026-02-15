---
description: 배포 전 typecheck/lint/build 검증 및 수정
argument-hint: [파일/디렉토리 경로...]
---

@../instructions/multi-agent/coordination-guide.md

# Pre-Deploy Command

> 배포 전 typecheck/lint/build를 검증하고 오류 수정

## 워크플로우

1. **병렬 검사**
   ```bash
   npx tsc --noEmit    # TypeScript 타입 체크
   npx eslint .        # ESLint 체크
   ```

2. **오류 수정** (순차)
   - 타입 오류 우선 수정
   - 린트 오류 수정
   - 각 수정 후 해당 파일 재검사

3. **Build 실행**
   ```bash
   npm run build    # 또는 yarn build, pnpm build
   ```

4. **Build 성공 확인**
   - 오류 발생 시 분석 및 수정
   - 성공 시 배포 준비 완료

## 에이전트 활용 (병렬)

```typescript
// 검증 + 보안 검토 병렬
Task(subagent_type="deployment-validator", model="sonnet", prompt="typecheck + lint + build 전체 검증")
Task(subagent_type="security-reviewer", model="sonnet", prompt="배포 전 보안 취약점 검토")
```

## 금지 사항

- 오류 무시하고 배포
- `any` 타입, `@ts-ignore`, `eslint-disable` 남발
- build 단계 생략
