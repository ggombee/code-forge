# Claude Opus 교차 검토 요약

> 작성일: 2026-10-14
>
> 목적: CodeForge AgentOps 계획의 과잉설계 위험과 공개 제품성을 독립 관점에서 검토
>
> 공개 범위: 결론과 의사결정 근거만 남긴다. 원본 대화 로그에는 로컬 경로와 비공개 업무 맥락이 있어 배포하지 않는다.

## 검토 방식

Claude Opus와 세 라운드씩 두 차례 토론했다. 첫 토론은 현재 사용자 문제에 비해 전체 Control Plane이 과도한지 검토했고, 두 번째 토론은 오픈소스와 유료 서비스로 확장할 때 무엇을 직접 소유해야 하는지 검토했다. 각 라운드에서 반론을 다시 제시하고 이전 결론을 유지하거나 수정하게 했다.

이 기록은 모델의 의견을 사실로 취급하지 않는다. 최종 문서에는 로컬 코드·테스트로 확인한 사실, 공식 문서로 확인한 외부 사실, 아직 검증하지 않은 제품 가설을 구분해 반영했다.

## 토론 1 — 과잉설계 검증

| 라운드 | 판정 | 핵심 이유 |
|---|---|---|
| 1 | 전체 Control Plane은 `OVERENGINEERED` 70 | Work·Approval·Knowledge·라우팅까지 한 번에 소유하면 기존 정본과 중복되고 검증 전 운영 부담이 커진다. |
| 2 | 전체안 `OVERENGINEERED` 75, Thin Coordinator `PROPORTIONATE` 65 | 외부에서 복구할 수 없는 최소 권위 필드와 검증 receipt만 저장하면 현재의 창 순회 문제를 작은 실험으로 확인할 수 있다. |
| 3 | Thin Coordinator `PROPORTIONATE` 70 | run별 단일 writer, 읽기 전용 adapter, status 한 화면, 2주 중단 기준으로 범위를 고정했다. 전체안 판정은 유지했다. |

수용한 비판은 다음과 같다.

- 업무 본문과 승인 기록을 새 원장에 복제하면 기존 이슈·PR 시스템과 정본이 충돌한다.
- 세션 관찰만으로 복구 가능한 값과 제품이 직접 기록해야 하는 권위 값을 나눠야 한다.
- 모델 라우터, 지식 그래프, GEPA, 메신저, 팀 서버는 현재 효용 검증에 필요하지 않다.
- 완료는 에이전트의 자기 보고가 아니라 독립 검증 결과로 판정해야 한다.

## 토론 2 — 공개 제품 아키텍처

첫 라운드는 host-neutral core를 권고했다. 투자자와 플랫폼 엔지니어 관점의 반론을 거치며 범위를 더 줄였고, 마지막 라운드에서는 **신뢰 커널은 소유하고 실행 생태계는 조합하는 D안**을 1위로 확정했다.

직접 소유할 경계는 다음 네 가지로 수렴했다.

1. base revision에 고정된 acceptance spec
2. `pass | fail | error | skipped`의 fail-closed 판정
3. 테스트 삭제·완화·우회 같은 검증 약화 탐지
4. 재현 가능한 receipt와 schema version

기존 도구에 맡길 범위도 명확히 했다.

- 모델 전송·retry·fallback은 기존 gateway를 우선 사용한다.
- 터미널·원격 실행·cron·메신저·범용 UI는 adapter로 연결한다.
- ForgeGlow는 공개 상태 API를 소비하는 별도 HUD로 유지한다.
- 지식 그래프와 prompt 자동 최적화는 realm·provenance·평가 데이터가 쌓인 뒤 연다.

## 최종 반영

- 제품 기준 문서: [`../11.codeforge-public-service-architecture-debate.md`](../11.codeforge-public-service-architecture-debate.md)
- 작은 효용 실험: [`../10.codeforge-thin-coordinator-overengineering-validation.md`](../10.codeforge-thin-coordinator-overengineering-validation.md)
- 야간 실행 계약: [`../12.night-runner-reference-audit-and-design.md`](../12.night-runner-reference-audit-and-design.md)

모델의 신뢰도 수치는 토론 내부의 판단 척도일 뿐 통계적 확률이 아니다. 실제 출시 결정은 문서에 정의한 사용자 행동·오류·검증·비용 지표로 다시 판단한다.
