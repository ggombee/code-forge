---
type: class
agent-system: VAS
name: monorepo
schema: interface/state-agent.md
extends: state/state.md
---

## Must
- [WorkspaceIsolation] 워크스페이스 간 의존성을 명시적으로 관리한다
- [SharedCode] 공유 코드 변경 시 영향 받는 모든 워크스페이스를 확인한다
- [BuildScope] 변경된 패키지와 의존 패키지만 빌드한다

## Never
- [CrossImport] 워크스페이스 간 직접 상대 경로 import를 사용하지 않는다
