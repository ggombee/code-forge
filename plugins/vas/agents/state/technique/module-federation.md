---
type: class
agent-system: VAS
name: module-federation
schema: interface/state-agent.md
extends: state/state.md
---

## Must
- [ContractFirst] 공유 모듈의 인터페이스를 먼저 정의하고 구현한다
- [Versioning] 공유 모듈 변경 시 하위 호환성을 유지한다
- [FallbackUI] 원격 모듈 로드 실패 시 폴백 UI를 제공한다

## Never
- [TightCoupling] 원격 모듈의 내부 구현에 의존하지 않는다
