---
type: interface
name: act-agent
agent-system: VAS
---

> ACT 에이전트의 구조를 정의한다.
> "이 에이전트가 무엇을 하는가"를 기술하는 데 사용한다.
>
> **ACT는 instance에서 override할 수 없다.**
> 워크플로우를 변경하려면 새로운 ACT class를 작성한다.
> ACT class 간 extends 체인은 허용한다.

## Trigger
- [When] 이 에이전트가 활성화되는 조건
- [Input] 받아야 하는 정보

## Workflow
- [Phase] 단계별 실행 흐름 (순서대로 기술)

## Verification
- [Check] 완료 전 자기 검증 항목

## Output
- [Deliverable] 최종 산출물의 형태

## Collaboration
- [Handoff] 다른 에이전트와의 인터페이스

## Permission
- [Model] 기본 사용 모델 (opus / sonnet / haiku)
- [PermissionMode] 권한 모드 (plan / acceptEdits / default / bypassPermissions)
- [Tools] 사용 가능한 도구 목록. 기본: `Read, Grep, Glob`. 쓰기가 필요하면 `Write, Edit` 추가, 명령 실행이 필요하면 `Bash` 추가
- [Boundary] 행동 범위 제한
