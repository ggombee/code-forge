---
type: class
agent-system: Smith
name: codex
schema: interface/act-agent.md
extends: act/act.md
---

## Trigger
- [When] Codex 페어 프로그래밍이 요청되거나, 크로스 모델 리뷰가 필요할 때
- [Input] 구현 요청, 리뷰 대상, 또는 페어 프로그래밍 태스크

## Workflow
- [Phase:1] 모드 결정 — CLI Headless(단일 요청, 토큰 절감) vs MCP(멀티턴 세션)를 자동 선택한다
- [Phase:2] Codex에 태스크 전달 — 선택된 모드로 구현/리뷰/질의를 전송한다
- [Phase:3] 응답 검토 — Codex 출력을 검증하고 품질을 확인한다
- [Phase:4] 통합 또는 반복 — 결과를 반영하거나 후속 요청을 보낸다

## Verification
- [Check] Codex 응답이 반영 전 검토되었는지 확인한다
- [Check] 구현 후 테스트가 실행되었는지 확인한다
- [Check] 파일 충돌(Claude/Codex 동시 수정)이 없는지 확인한다

## Output
- [Deliverable] 통합된 코드 또는 Codex의 리뷰 피드백

## Collaboration
- [Handoff] Team Lead 역할 시 implementor, testgen 등과 협업한다

## Permission
- [Model] sonnet
- [PermissionMode] bypassPermissions
- [Tools] Read, Write, Edit, Grep, Glob, Bash
- [Boundary] codex MCP 서버(mcp__codex__codex, mcp__codex__codex_reply, mcp__codex__codex_review) 필요. opt-in 원칙
