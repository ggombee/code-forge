# CodeForge 통합 계획 최종 검수

작성일: 2026-10-18. 상태: Codex·Claude 2차 검수 후 계획 검수 GO. 제품 구현·실호스트·출시 검증은 별도다.

## 검수 대상과 공개 범위

원격 계획 브랜치 `docs/agentops-platform-plan`의 `e05552cd`와 원격 main의 `e9b9c1f`를 같은 계획 브랜치에서 병합했다. 병합 결과 `243eb1a`를 초기 검수 기준으로 삼고, [통합 개선 계획](../../../plan/code-forge-final-improvement-plan-2026-10-18.md)을 실행 순서의 단일 기준으로 정리했다. 원본 작업트리의 미커밋 코드는 이 변경에 포함하지 않았다.

공개 문서의 예시는 `sample-app`, `sample-docs`, `realm-a`, `realm-b` 같은 가상 자료로 작성한다. 실제 사용자·조직 식별자, 계정, 내부 URL·경로·업무와 비공개 구현의 검사 이력은 공개 근거로 싣지 않는다. 기존 문서의 해당 서술은 일반 상태·복구 요구사항으로 교체하며, 합성 시나리오를 실행 결과로 표현하지 않는다.

기존 PNG 구조도 두 장도 확인해 가상 예시의 Mermaid 구조도로 교체했다. 원본은 Git 이력에서 복원할 수 있으며 현재 공개 문서와 파일 목록에는 포함하지 않는다.

## 제품에 대한 판단

CodeForge는 저장소의 결함·병목을 측정하고 작은 개선 후보를 만든 뒤, 기능·안전성·성능·비용을 독립적으로 확인하는 제품이다. 사용자는 질문과 검토 후보를 한곳에서 확인하고 정확한 반영 동작을 승인한다. 기존 CodeForge의 저장소 규칙·스킬·Smith는 유지하고, 새 core가 작업·검증·승인·복구 원장을 관리한다.

| 기존 시스템 | 재사용할 기능 | CodeForge가 추가할 책임 |
|---|---|---|
| 기존 CodeForge·Smith | 규칙·스킬·프로젝트 agent 원본, 정적 컴파일 | 두 호스트의 발견·권한·설치·제거 검증 |
| Claude·Codex | agent 실행, session·event·checkpoint·host permission | runtime 간 Work 기준·독립 판정·승인 기록 |
| Herdr | 사용자가 운영하는 터미널·agent 관찰과 제어 | turn·artifact 근거 연결, 완료 판정과 제어 권한 구분 |
| ForgeGlow | 현재 세션 표시와 native status line 안내 | 선택형 managed projection 계약. 제거된 legacy reader를 전제하지 않음 |
| Hermes·OS scheduler | 예약·wake·전송 | 권한·검증·재시도 판단을 core에서 유지 |
| LiteLLM 등 transport | provider 연결·fallback | realm·capability·예산 검사와 새 Attempt 기록 |
| Flow·Hearth | legacy import·도메인 자료·보고서 후보 | 필요할 때 연결. 동일 Work의 원장·scheduler 중복 금지 |
| Voice·Whetstone | 기존 접근성 입력·사람 학습·승인된 profile | 입력·질문 경로 회귀, profile의 허용된 선택 적재 |

이 책임 분리는 구현 판단이다. 기존 도구가 요구 계약을 충족하면 해당 구현을 재사용하고 자체 구현 범위를 줄인다.

## Debate Summary

주제: 기존 제품과 AgentOps 설계를 합친 계획이 사용자 목적·기존 도구·실제 검증 기준을 충족하는가.

모드: cross-model. 참가자: Codex와 Claude Code 2.1.302의 기본 선택 모델 `claude-opus-5-5`. Claude에는 공개 가능한 계획 checkout과 읽기 도구만 제공했다. 초기 검토는 파일 검토이며 웹·테스트·계정 실증을 수행하지 않았다. 공식 자료 확인과 격리 회귀검사는 Codex가 별도로 수행했다.

라운드: 2/3 완료. Claude는 초기 실질 blocker가 해소됐고 실행을 막는 새 blocker가 없다고 판정했다. 최종 정합성 보완은 Codex가 반영·재확인했다.

| 항목 | Codex 초기 판단 | Claude 반론 | 수정안 |
|---|---|---|---|
| 제품 구조 | 기존 pack과 독립 core가 목적에 맞음 | 동의. 문서별 역할·언어 결정이 충돌 | README·09·11·11b·12에 통합 계획 우선 표시 |
| 단계 | 단계별 완성 흐름 유지 | 네 단계 체계의 매핑과 무인 실행 시점 불명확 | 과거 단계 매핑, G2 단일 장비 무인 준비·G4 원격 접근 명시 |
| 검증 | 고정 recipe·독립 verifier 필요 | 첫 시험에 알려진 정답이 없음 | 결함 수정·weakening·미실행·stale 승인·응답 유실·질문/realm fixture |
| 선행 조건 | 기준선과 core 계약을 먼저 확인 | 안전성 수리가 core ADR에 묶임 | G0a 복원 뒤 G1a 가능, G0b는 host/core 작업별 의존성 적용 |
| 진입점 | `/start`·CLI가 같은 계약 사용 | 첫 시험부터 자연어 compiler가 필요하면 범위 확대 | WorkSpec 파일로 시작, `/start`는 G2 후반·두 호스트 parity는 G3 |
| runtime | structured session 우선 실증 | 단발 `exec`로 결합 시험을 먼저 줄일 수 있음 | 단발 실험 허용, session·cancel·resume conformance 대체 금지 |
| 범위 | 첫 제품의 질문·승인·복구 유지 | G2의 새 Voice 승인·다중 realm 운영은 큼 | G2 단일 public realm+다른 realm 거부, 기존 Voice 보존·새 승인 연결 G3 |

합의: 기존 작업 환경을 보존하며 신뢰·검증·승인·복구를 core에 구현하는 방향을 유지한다. 모델 합의는 검증 결과를 대신하지 않는다.

2차 검수에서 데이터 수명 정책의 결정 시점을 G0b fixture 기본값과 G2 실행 전 정책으로 나누고, 09번의 Phase 0~6 매핑을 추가했다. 검수 상태·Hearth 재평가 시점·G3 Voice 연결도 문서끼리 맞췄다. 최종 문서에는 실제 runtime·호스트·배포를 검증했다는 주장을 넣지 않았다.

남은 결정: core 이름·언어·DB driver·첫 실제 profile/runtime은 G0b 실증과 ADR로 확정한다. 확정 전에도 G0a와 그 뒤의 기존 안전성 수리는 진행할 수 있다.

## 실제 확인한 결과

| 확인 대상 | 결과 | 적용 범위 |
|---|---|---|
| 원격 refs 조회 | main `e9b9c1f`, 계획 브랜치 `e05552cd` | 조회 시점의 원격 상태 |
| 계획 브랜치 병합 | 충돌 없이 `243eb1a` 생성 | 문서 기준선 통합 |
| 커밋된 quality gate | macOS Bash 3.2 구문 검사 실패 | 계획 checkout의 기존 소스 |
| 원본 작업트리의 safety WIP | 구문 검사·격리 회귀검사 23건 통과 | 테스트 대역·임시 Git fixture. 계획 브랜치에는 미포함 |
| 원본 작업트리의 state WIP | 격리 회귀검사 9건 통과 | 동시 기록·손상·경로 fixture. 계획 브랜치에는 미포함 |
| Glow source | 커밋된 0.8.0과 미커밋 0.9.0 차이, legacy reader 제거 WIP 확인 | source 읽기. 설치본·배포 통과 근거로 사용하지 않음 |
| 문서 링크 | 변경 문서의 상대 링크 68건 유효 | 외부 링크와 제품 기능 검증은 별도 |
| 공개 범위 | 추적 텍스트의 식별자·내부 경로·관련 맥락 검색과 PNG 두 장 직접 확인·치환 | 현재 파일 기준. 기존 Git 이력은 재작성하지 않음 |

WIP 재사용에는 G0a의 실제 백업·복원과 통합 코드 재검증이 필요하다. 현재 문서 검수는 이를 완료했다고 기록하지 않는다.

## 공식 자료 재확인

- [Codex 통합 방식](https://developers.openai.com/blog/codex-as-a-platform): 단발 exec, SDK, app-server의 통합 목적이 다르다. session·event·approval이 필요한 제품에는 app-server 실증을 우선한다.
- [Codex plugin 패키징](https://developers.openai.com/plugins/build/plugins): portable manifest·skills와 hook 설치·배포 조건을 확인했다.
- [Codex subagents](https://learn.chatgpt.com/docs/agent-configuration/subagents): custom agent 지침은 별도 sandbox를 만들지 않으며 부모 권한을 상속한다.
- [Claude Managed Agents](https://platform.claude.com/docs/en/managed-agents/overview): 장기 session·event·실행 환경을 재사용할 수 있다. 실제 계정 가용성과 adapter 동작은 이번 검수에서 시험하지 않았다.
- [Herdr agent automation](https://herdr.dev/docs/agent-automation/): prompt/wait는 개별 turn을 추적하지 않으므로 완료 근거를 따로 연결해야 한다.
- [Hermes cron](https://github.com/NousResearch/hermes-agent/blob/main/website/docs/user-guide/features/cron.md), [LiteLLM routing](https://docs.litellm.ai/docs/routing): 선택형 예약·전송·provider 연결의 재사용 후보이며 core Work 원장을 대체하는지 별도 평가한다.

## 판정

계획 검수 GO. 문서 우선순위·단계·첫 정답 fixture·복구 baseline·진입점·예산 의존성은 실행 가능한 수준으로 정리했다. 다음 구현 단위는 G0a 복원 가능한 기준선과 G0b 정답 fixture다. 새 core 구현·실호스트 지원·출시는 완료로 판정하지 않는다. 출시에는 두 host pack·두 runtime·두 profile·설치본·복구의 실제 증거가 필요하다.
