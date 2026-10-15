# CodeForge AgentOps 설계 문서 지도

> 상태: 구현 전 계획
>
> 초기 사용자: 여러 AI 코딩 세션을 함께 쓰는 개인 개발자와 소규모 팀

## 먼저 볼 문서

1. [한눈에 보는 제품 결정](./11b.codeforge-public-service-summary.md) — 구조도와 쉬운 설명으로 제품 방향을 검토한다.
2. [공개 서비스·24시간 AgentOps 최종 설계](./11.codeforge-public-service-architecture-debate.md) — 현재 제품 범위와 출시 계획의 기준 문서다.
3. [야간 실행기 참고 구현 감사와 최종 설계](./12.night-runner-reference-audit-and-design.md) — 야간 실행의 상태, 권한, 언어, 검증 계약을 정한다.

## 문서별 지위

| 문서 | 현재 지위 | 읽는 목적 |
|---|---|---|
| [08 Herdr·OMP·Hermes·Qwen 재검토](./08.herdr-omp-hermes-qwen-control-plane-review.md) | 초기 비교 자료 | 기존 도구의 기능과 한계를 확인 |
| [09 CodeForge 중심 장기 설계](./09.codeforge-owned-agent-system-design.md) | 장기 구조 참고 | 확장 가능한 전체 구조를 확인 |
| [10 Thin Coordinator 검증](./10.codeforge-thin-coordinator-overengineering-validation.md) | 선택형 실험 | 과잉설계 위험과 작은 실험 범위를 확인 |
| [11 공개 서비스 최종 설계](./11.codeforge-public-service-architecture-debate.md) | 제품 계획 기준 | 제품 범위, 출시 순서, 중단 기준을 결정 |
| [11b 검토용 요약](./11b.codeforge-public-service-summary.md) | 사람용 요약 | 전체 결정을 빠르게 검토 |
| [12 야간 실행 최종 설계](./12.night-runner-reference-audit-and-design.md) | 실행 하위 계획 | 24시간 실행과 아침 승인함을 구현 |

08~10번 문서는 당시 판단과 근거를 보존한다. 현재 구현 결정이 다르면 11번과 12번을 따른다.

## 현재 제품 결정

CodeForge는 여러 모델과 실행기를 직접 대체하지 않는다. 작업 명세, 권한, 데이터 분리, 비용, 독립 검증, 실행 기록과 승인함을 소유하고 Claude, Codex, GLM, Qwen, Herdr, Hermes 같은 도구를 어댑터로 연결한다.

언어도 하나로 고정하지 않는다. 에이전트용 스킬과 규칙은 모델·작업별 `LanguageProfile` 평가로 선택한다. 한국어 사용자 문서는 윤문하고, 공개 영어 문서는 영어 독자에게 자연스럽게 별도로 작성한다.

![CodeForge 한눈에 보는 구조도](./assets/codeforge-overview-ko.png)

## 구현 순서

1. 기존 CodeForge의 거짓 성공 판정과 동시 기록 결함을 고친다.
2. 실행기와 무관한 검증 CLI와 GitHub Action을 공개한다.
3. 한 사람이 쓰는 야간 실행기와 아침 승인함을 만든다.
4. 모델별 비용·품질·언어 프로필과 ForgeGlow 연동을 검증한다.
5. 팀 승인과 조직 정책에 반복 수요가 확인되면 Hosted Hub로 넓힌다.

현재 문서는 설계와 출시 판단이다. 새 코어, 야간 실행기, Hosted Hub, 모델 설치와 계정 연결은 아직 구현하지 않았다.
