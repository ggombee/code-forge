# CodeForge AgentOps 설계 문서 지도

> 상태: 채택된 제품 북극성 · 단계별 구현 전
>
> 초기 사용자: 여러 AI 코딩 세션을 함께 쓰는 개인 개발자와 소규모 팀

## 먼저 볼 문서

1. [AI가 만든 소프트웨어를 더 견고하고 효율적으로 만드는 시스템](./11b.codeforge-public-service-summary.md) — 제품이 해결할 문제와 실제 개선 루프부터 읽는다.
2. [공개 서비스·24시간 AgentOps 최종 설계](./11.codeforge-public-service-architecture-debate.md) — 쉬운 설명에 이어 내부 계약, 보안 규칙과 출시 계획을 확인한다.
3. [24시간 무인 실행기 참고 구현 감사와 최종 설계](./12.night-runner-reference-audit-and-design.md) — 무인 준비, 인간 승인, 실제 반영의 상태·권한·검증 계약을 정한다.

## 문서별 지위

| 문서 | 현재 지위 | 읽는 목적 |
|---|---|---|
| [08 Herdr·OMP·Hermes·Qwen 재검토](./08.herdr-omp-hermes-qwen-control-plane-review.md) | 초기 비교 자료 | 기존 도구의 기능과 한계를 확인 |
| [09 CodeForge 중심 장기 설계](./09.codeforge-owned-agent-system-design.md) | 채택된 북극성 | 확장 가능한 전체 구조와 단계별 목적지를 확인 |
| [10 Thin Coordinator 검증](./10.codeforge-thin-coordinator-overengineering-validation.md) | 역사적 판단 기록 | 초기 과잉설계 논쟁과 작은 관찰 실험의 측정법을 확인 |
| [11 공개 서비스 최종 설계](./11.codeforge-public-service-architecture-debate.md) | 제품 계획 기준 | 제품 범위, 출시 순서, 중단 기준을 결정 |
| [11b 제품 이야기](./11b.codeforge-public-service-summary.md) | 사람용 진입점 | 사용 장면, 최소 구성과 선택형 도구의 이유를 이해 |
| [12 무인 실행 최종 설계](./12.night-runner-reference-audit-and-design.md) | 실행 하위 계획 | 24시간 준비와 인간 반영 게이트를 구현 |
| [북극성 독립 검토](./evidence/2026-10-15-independent-north-star-review.md) | 최신 교차 검토 근거 | 과거 MVP 제약을 뒤집은 이유와 최신 runtime의 역할·한계를 확인 |

08번과 10번은 당시 판단과 근거를 보존한다. 09번은 채택된 북극성이고, 구체적인 현재 구현 결정은 11번과 12번을 따른다.

## 현재 제품 결정

CodeForge는 빠르게 생성된 소프트웨어를 저장소 기준으로 측정하고, 근본 원인을 찾아 최소 변경으로 개선하며, 같은 품질을 더 적은 토큰·비용으로 재현하는 검증·최적화 계층이다. 여러 모델과 실행기를 직접 대체하지 않고 작업 명세, 권한, 데이터 분리, 비용, 독립 검증, 실행 기록과 승인함을 소유한다. Claude, Codex, GLM, Qwen, Herdr, Hermes 같은 도구는 어댑터로 연결한다.

시간대는 권한 기준이 아니다. 허용된 모든 작업 유형을 받아 격리 환경에서 가능한 검증까지 끝내되, `CandidatePackage` 작성과 실제 push·PR 공개·merge·deploy를 분리한다. 저장소 정책이 허용하면 draft PR까지 자동으로 열고, 실제 반영은 정확한 artifact digest에 묶인 승인 뒤에만 수행한다.

실행 중 판단이 필요해도 전체 작업을 멈추지 않는다. 결정에 의존하는 노드만 `WAITING_DECISION`으로 두고, 메인 coordinator는 독립적으로 진행할 수 있는 일을 계속한다. 별도 Decision Concierge가 전용 창·스레드·모바일 카드로 질문하고, 답을 versioned `DecisionReceipt`로 원장에 돌려보낸다.

언어도 하나로 고정하지 않는다. 에이전트용 스킬과 규칙은 모델·작업별 `LanguageProfile` 평가로 선택한다. 한국어 사용자 문서는 윤문하고, 공개 영어 문서는 영어 독자에게 자연스럽게 별도로 작성한다.

![CodeForge 한눈에 보는 구조도](./assets/codeforge-overview-ko-v2.png)

## 구현 순서

1. 새 host-neutral core 모노레포에 versioned 계약, SQLite WAL, migration·outbox·`doctor`를 만든다.
2. structured runtime 하나, worktree·sandbox, 독립 검증, Decision/Approval Inbox, 별도 apply/readback을 연결한 개인 수직 단면을 완성한다.
3. Claude·Codex 두 계열과 Herdr 관찰을 conformance로 검증하고 24시간 authority·선택형 GPU worker·모바일 웹을 붙인다.
4. 첫날부터 쌓은 provenance를 이용해 Markdown·Obsidian·Dooray·Lark 지식 연속성을 완성하고, GLM·Qwen·prompt 개선은 eval 뒤에 연다.
5. 팀 승인과 조직 정책에 반복 수요가 확인되면 Postgres·Temporal 기반 Hosted Hub로 넓힌다.

현재 문서는 설계와 출시 판단이다. 새 코어, 무인 실행기, Hosted Hub, 모델 설치와 계정 연결은 아직 구현하지 않았다.

## ★ CURRENT — 다음 세션 인계

- **현재 상태**: AI 생성 소프트웨어의 견고성·코드 효율·에이전트 비용을 함께 개선하는 범용 AgentOps 북극성, 24시간 실행 계약, 지식·언어·측정 기반 검증 계획까지 문서화했다. 구현은 시작하지 않았다.
- **확정한 결정**: CodeForge가 신뢰 커널과 전역 Work 원장을 소유하고, runtime·terminal·model·notification은 교체 가능한 adapter로 연결한다. `VerificationRecipe`는 범용 계약으로 두고 실제 명령과 지표는 `RepositoryProfile`이 제공한다. 토큰 최적화는 품질 gate를 유지한 상태의 verified completion당 비용으로 판정한다.
- **반복하지 않을 것**: 특정 조직의 비공개 프로젝트나 계정 규칙을 공개 코어에 넣지 않는다. 특정 프론트엔드·언어·benchmark 도구를 코어 schema에 고정하지 않는다.
- **바로 할 일**: P0 구현 전에 `WorkSpec`, `PolicySnapshot`, `RepositoryProfile`, `VerificationRecipe`, `CheckResult`, `Evidence`, `Receipt`의 v0 schema와 상태 전이 초안을 작성한다.
- **검증할 것**: 성격이 다른 두 공개 저장소 profile이 같은 verifier 계약을 통과하고, 품질 비퇴행 조건에서 코드 또는 에이전트 비용을 실제로 개선하는지 확인한 뒤 SDK 경계를 확정한다.
- **먼저 읽을 곳**: 11b 제품 이야기 → 11 공개 서비스 최종 설계 → 12 무인 실행 최종 설계 순서로 읽는다.
