---
type: class
agent-system: VAS
name: micro-frontend
schema: interface/state-agent.md
extends: state/state.md
---

## Must
- [Independence] 각 마이크로 프론트엔드는 독립적으로 배포 가능해야 한다
- [Communication] 마이크로 프론트엔드 간 통신은 명시적 이벤트/메시지로만 한다
- [StyleIsolation] 스타일 충돌을 방지하는 격리 전략을 적용한다

## Never
- [SharedState] 마이크로 프론트엔드 간 전역 상태를 직접 공유하지 않는다
