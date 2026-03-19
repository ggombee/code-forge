---
type: class
agent-system: Anvil
name: testing-library
schema: interface/state-agent.md
extends: state/state.md
---

## Must
- [UserCentric] 사용자가 보고 상호작용하는 방식으로 테스트한다
- [QueryPriority] getByRole > getByLabelText > getByText > getByTestId 순서로 쿼리한다
- [AsyncHandling] 비동기 업데이트는 waitFor/findBy로 처리한다

## Never
- [ImplementationDetail] 컴포넌트 내부 상태나 메서드를 직접 테스트하지 않는다
