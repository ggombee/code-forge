---
description: 모든 변경사항 커밋 후 푸시
---

@../instructions/multi-agent/coordination-guide.md

# Git All Command

> @git-operator 에이전트를 사용하여 모든 변경사항을 커밋하고 푸시.

## 필수 사항

**반드시 @git-operator 에이전트를 사용해야 합니다.**

```typescript
Task(subagent_type="git-operator", model="haiku", prompt=`
  전체 커밋 모드:
  - 모든 변경사항을 논리적 단위로 분리하여 전부 커밋
  - 반드시 푸시 (git push)
  - clean working directory 확인 필수
`)
```

## 금지 사항

- Bash 도구로 git 명령 직접 실행
- @git-operator 없이 커밋/푸시 수행

## 워크플로우

1. 모든 변경사항 분석
2. 논리적 단위로 그룹핑
3. 각 그룹별 커밋 (반복)
4. clean working directory 확인
5. git push 실행
