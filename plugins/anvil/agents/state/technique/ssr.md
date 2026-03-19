---
type: class
agent-system: Anvil
name: ssr
schema: interface/state-agent.md
extends: state/state.md
---

## Must
- [Hydration] 서버/클라이언트 렌더링 결과의 일관성을 보장한다
- [DataFetching] 서버에서 필요한 데이터를 미리 가져와 초기 HTML에 포함한다
- [BrowserAPI] window/document 등 브라우저 API 사용 시 클라이언트 전용 코드로 분리한다

## Never
- [ServerSideEffect] 서버 렌더링 중 사이드 이펙트(API 변경, 상태 수정)를 발생시키지 않는다
