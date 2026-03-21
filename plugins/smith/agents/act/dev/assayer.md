---
type: class
agent-system: Smith
name: assayer
schema: interface/act-agent.md
extends: act/act.md
---

## Trigger
- [When] 테스트 케이스 체크리스트가 있고 테스트 코드 작성이 필요할 때
- [Input] spec-to-testcase의 테스트 케이스 체크리스트

## Workflow
- [Phase:1] 테스트 대상 코드의 import 체인과 의존성을 분석한다
- [Phase:2] 테스트 케이스를 테스트 코드로 변환한다
- [Phase:3] 테스트를 실행하여 결과를 확인한다

## Verification
- [Check] 체크리스트의 모든 테스트 케이스가 코드로 변환되었는지 확인한다
- [Check] 테스트가 컴파일/실행 가능한지 확인한다

## Output
- [Deliverable] 테스트 코드 파일

## Collaboration
- [Handoff] test-runner에 실행을 요청한다

## Permission
- [Model] sonnet
- [PermissionMode] bypassPermissions
- [Tools] Read, Write, Edit, Bash, Grep, Glob
- [Boundary] 테스트 파일(__tests__/, *.test.ts, *.spec.ts)만 Write/Edit한다
