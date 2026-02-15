---
description: 현재 세션에서 수정한 파일만 커밋 후 푸시
---

@../instructions/multi-agent/coordination-guide.md

# Git Session Command

> @git-operator 에이전트를 사용하여 현재 세션 파일만 선택적으로 커밋하고 푸시.

## 필수 사항

```typescript
Task(subagent_type="git-operator", model="haiku", prompt=`
  세션 커밋 모드:
  - 현재 세션 관련 파일만 선택적 커밋
  - 반드시 푸시 (git push)
  - 이전 세션의 미완성 작업은 제외
`)
```

## 선택 기준

| 포함 | 제외 |
|------|------|
| 현재 세션 관련 파일 | 이전 세션의 미완성 작업 |
| 방금 전 작업한 파일 | 자동 생성 파일 (lock, cache) |
| 관련 기능의 파일들 | 무관한 변경사항 |
