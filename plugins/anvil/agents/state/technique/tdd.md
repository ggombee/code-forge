---
type: class
agent-system: Anvil
name: tdd
schema: interface/state-agent.md
extends: state/state.md
---

## Must
- [RedFirst] 실패하는 테스트를 먼저 작성한다
- [MinimalGreen] 테스트를 통과하는 최소한의 코드만 작성한다
- [RefactorAfter] 테스트 통과 후 리팩토링한다

## Never
- [SkipRed] 실패 확인 없이 구현 코드를 먼저 작성하지 않는다

## Should
- [SmallCycles] Red-Green-Refactor 사이클을 짧게 유지한다
