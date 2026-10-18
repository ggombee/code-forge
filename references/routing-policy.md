# Routing Policy — 모델·사고 깊이·위임의 단일 진실

> Claude와 Codex가 공유하는 canonical 정책이다. 구체 모델명과 호스트 문법은 어댑터가 결정한다.
> 목표는 가장 강한 모델을 많이 쓰는 것이 아니라, **필요한 증거를 가장 싼 충분한 경로로 얻는 것**이다.

---

## 1. 결정 원칙

1. 복잡도·오케스트레이션 라우트는 GROUND→PLAN 경계에서 한 번 결정한다.
2. 파일 수는 신호일 뿐 복잡도의 판정 기준이 아니다.
3. 새 증거로 위험 등급이 바뀐 경우에만 라우트를 재판정한다. 단, 이미 결정한 라우트 안의 phase 전환(DEEP 계획 → BALANCED 구현 등)은 재라우팅이 아니며 resolver가 예고된 매핑을 적용한다.
4. 높은 effort와 다수 에이전트는 품질 보장이 아니다. 검증 가능한 이득이 있을 때만 올린다.
5. 자동 경로의 기본 상한은 `high`다. `xhigh` 이상은 고위험·고가치 작업에서 사용자가 요청했거나 eval로 이득이 확인된 경우만 쓴다.
6. **모델/effort, 컨텍스트 깊이, fan-out은 독립된 세 축**이다. 같은 위험 판정을 공유해도 한 축을 올렸다는 이유로 나머지를 자동 상향하지 않는다.

## 2. 위험 신호

GROUND에서 아래 축을 각각 `low | medium | high`로 판단한다.

| 축 | low | medium | high 예시 |
|---|---|---|---|
| **ambiguity** | 완료 조건이 명확 | 일부 선택지가 남지만 수용 기준으로 판별 가능 | 요구·소유권·정책 의도가 불명확 |
| **blast_radius** | 한 영역의 국소 변경 | 같은 기능의 여러 파일·호출자 영향 | 공용 계약, 여러 패키지·서비스 영향 |
| **irreversibility** | 쉽게 되돌릴 수 있음 | 롤백 가능하지만 상태 변환이 필요 | 데이터 마이그레이션, 삭제, 배포 |
| **external_effect** | 로컬 읽기·수정 | 승인된 개발 환경의 제한된 호출 | 외부 쓰기, 비용 발생, 권한·자격증명 |
| **verification_gap** | 직접 테스트 가능 | fixture·mock으로 부분 검증 가능 | 실환경 의존, 재현 불가, 관찰 수단 없음 |
| **novelty** | 저장소 기존 패턴 반복 | 익숙한 도구의 새 조합 | 새 아키텍처·새 런타임·미검증 기술 |

등급은 합산 점수보다 **가장 위험한 축**을 우선한다.

- **LOW**: 모든 축이 low이고 기존 패턴과 직접 검증 경로가 있다.
- **MEDIUM**: medium 축이 있으나 되돌릴 수 있고 검증 경로를 만들 수 있다.
- **HIGH**: high 축이 하나라도 있거나 medium 축들이 결합해 실패 비용이 커진다.
- **CRITICAL override**: 운영 데이터, 자격증명, 보안 경계, 대규모 삭제, 외부 공개·결제처럼 사전 승인 없이는 진행하면 안 되는 작업이다.

커밋 이후의 push·PR처럼 **선택 가능한 후속 외부 단계**는 구현 자체의 등급을 자동으로 HIGH로 올리지 않는다. 구현 위험과 외부 실행 위험을 단계별로 따로 판정하고, 외부 단계 직전에 승인 checkpoint를 둔다. 외부 효과가 작업의 본체라면 처음부터 해당 축에 반영한다.

## 3. 컨텍스트 적재 사다리

항상 작은 단계에서 시작하고, 해결되지 않은 질문이 있을 때만 다음 단계로 올라간다.

| 단계 | 읽는 것 | 확장 조건 |
|---|---|---|
| **C0 Spine** | 자동 적재된 최소 계약 | 항상 |
| **C1 Local** | 대상 파일 + 가장 가까운 정상 패턴 | 작업 시작 |
| **C2 Task** | 선택된 스킬 1개 + 직접 연결된 primary reference 1개 | 로컬 증거로 판단 불가 |
| **C3 Independent** | fresh reviewer가 산출물·수용 기준·diff만 검토 | HIGH에서 검증 공백이 남거나 독립 관점이 결정을 바꿀 때, CRITICAL에서는 필수 |

- 카탈로그·가이드·참조를 예방적으로 전부 읽지 않는다.
- 같은 내용을 설명하는 문서가 여러 개면 canonical 한 개만 읽고 나머지는 drift 검사 대상으로 취급한다.
- 질문이 답해졌거나 다음 행동이 검증 가능해지면 더 읽지 않는다.

## 4. 모델 클래스와 역할

공통 정책은 제품명이 아니라 능력 클래스를 사용한다.

| 클래스 | 용도 | 기본 effort |
|---|---|---|
| **FAST** | 검색, 분류, 목록화, 기계적 점검 | low |
| **BALANCED** | 일반 구현, 테스트, 문서 수정 | medium |
| **DEEP** | 아키텍처, 모호한 정책, 고위험 리뷰 | high |

에이전트 역할도 분리한다.

- **scanner**: FAST + read-only. 위치·패턴·증거만 반환한다.
- **builder**: BALANCED + workspace-write. 합의된 범위만 구현한다.
- **critic**: DEEP + read-only. 작성자의 추론을 받지 않고 산출물과 수용 기준만 본다.
- **researcher**: BALANCED 또는 DEEP + read-only/network. 최신 외부 사실이 결정에 필요한 경우만 쓴다.

위 역할의 read-only/workspace-write는 요구하는 경계다. Codex custom agent TOML은 부모의 sandbox·approval·provider·MCP를 대체하지 못하므로, 필요한 경계는 제한된 부모 session 또는 별도 프로세스에서 적용·검증한다. 역할 지침이나 도구 이름만으로 hard read-only를 선언하지 않는다. [공식 Subagents 문서](https://learn.chatgpt.com/docs/agent-configuration/subagents)

## 5. complexity → orchestration 매핑

| 등급 | 주 실행 | effort | 서브에이전트 | 검증 |
|---|---|---|---|---|
| **LOW** | 현재 에이전트 또는 BALANCED | low | 없음 | 직접 lint/test/확인 |
| **MEDIUM** | BALANCED | medium | 대상이 불명확할 때 scanner 1개 | 관련 테스트 + diff review |
| **HIGH** | DEEP/high 계획 → BALANCED/medium 구현 | phase별 | 서로 다른 read-only lane 최대 2개, 검증 공백이 남을 때 DEEP/high fresh critic 1개 | diff review + 판별 실험, 필요 시 독립 검토 |
| **CRITICAL** | DEEP/high 계획·검증, 구현은 승인된 최소 class | phase별, xhigh 이상은 명시 선택 | 독립 verifier 필수 | 변경 전 사용자 checkpoint + 복구 계획 |

`xhigh`/`max`/`ultra`를 단순 파일 수나 "더 잘해줘"만으로 자동 선택하지 않는다. 먼저 요구 충돌, 열린 도구 범위, 정지 조건을 정리한다.

- `plan_required`: HIGH와 CRITICAL에서 `true`. 별도 planner spawn을 뜻하지 않으며 현재 에이전트의 명시적 계획도 포함한다.
- `critic_required`: CRITICAL은 `true`. HIGH는 verification gap이 남거나 독립 관점이 결정을 바꿀 때만 `true`다.
- HIGH라는 이유로 구현 단계까지 high effort를 유지하지 않는다. phase가 바뀌면 구현·검증을 마친 host resolver만 실제 role/model/effort를 갱신하며, resolver가 없는 host는 권고값만 기록한다.

## 6. 호스트 resolver

| 공통 클래스 | Claude 어댑터 | Codex 어댑터 |
|---|---|---|
| FAST | 경량 티어(예: Haiku) | 설치 환경의 저지연 모델 |
| BALANCED | 균형 티어(예: Sonnet) | 설치 환경의 균형 모델 |
| DEEP | 심층 티어(예: Opus) | 설치 환경의 최상위 코딩 모델 |
| effort | 하니스가 강제하지 못하면 advisory로 기록 | `model_reasoning_effort`로 명시 |

- 실제 모델 ID는 어댑터 설정과 실행 로그에서만 관리한다. canonical 정책에 최신 버전·가격·폐기일을 적지 않는다.
- Codex custom agent의 **목표 출력**은 `.codex/agents/*.toml`이고 Claude agent의 현재 출력은 `agents/*.md`다. Codex compiler가 배선되기 전에는 resolver를 advisory/design 상태로 표시한다.
- 모델을 지정하지 않으면 부모 설정을 상속한다. 비용 격리가 필요할 때만 명시적으로 고정한다.
- skill 본문은 portable plugin으로 재사용할 수 있으며, compiler는 실제 host 차이가 있는 manifest·trigger·reference·도구 mapping을 변환한다. native pack 지원과 새 core runtime 지원은 별도 capability로 기록한다.

## 7. 위임 조건과 정지 규칙

서브에이전트는 다음 조건을 모두 만족할 때만 사용한다.

- 작업이 독립적이며 결과를 짧게 요약할 수 있다.
- 메인 스레드의 로그·탐색 노이즈를 실제로 줄인다.
- 같은 파일을 동시에 수정하지 않는다.
- 조율 비용보다 병렬 이득 또는 관점 독립성이 크다.

기본 fan-out은 0~2개다. 세 번째 lane은 기존 두 결과가 서로 다른 미해결 질문을 만들었을 때만 연다. 같은 주장만 반복되면 중단한다.

토론·리뷰는 아래 중 하나면 종료한다.

- 가장 큰 반론을 판별할 싼 테스트가 정해졌다.
- 새 증거 없이 주장이 반복된다.
- 수용 기준을 충족하거나, 어떤 증거가 부족한지 명확해졌다.
- 외부 승인이나 사용자 결정이 필요하다.

## 8. 기록 계약

라우팅 결과는 `bin/forge emit-event`를 통해 latest-only route snapshot에 기록한다. 현재 in-repo consumer는 이를 표시만 하므로 **실행 제어가 아니라 telemetry/advisory**다. 실제 모델·agent 자동 선택은 host resolver가 구현되고 eval을 통과한 뒤에만 활성화한다.

```json
{
  "complexity": "LOW|MEDIUM|HIGH|CRITICAL",
  "phase": "ground|plan|build|verify",
  "model_class": "FAST|BALANCED|DEEP",
  "effort_level": "minimal|low|medium|high|xhigh|max|ultra",
  "risk_triggers": ["ambiguity", "external_effect"],
  "orchestration": "direct|scan|plan-build|plan-build-critic|checkpoint-verify",
  "plan_required": true,
  "critic_required": false,
  "actual_orchestration": "pending|direct|scan|plan-build|plan-build-critic|checkpoint-verify",
  "actual_agents": [],
  "actual_model_class": null,
  "actual_effort_level": null
}
```

`model_class`·`effort_level`은 현 phase의 권고값이다. `actual_model_class`·`actual_effort_level`은 호스트가 실제 선택을 관측했을 때만 채우고, resolver가 없으면 `null`로 둔다. `orchestration`은 권고 경로다. `actual_orchestration`과 `actual_agents`는 실제 호출 뒤에 갱신하며, critic을 호출하지 않았는데 `plan-build-critic`으로 기록하지 않는다. latest-only snapshot은 현재 실행을 설명할 뿐 장기 eval 데이터가 아니다. 품질·token·latency 비교는 별도 fixture runner의 CI artifact로 계산한다.

공통 effort enum은 호스트별 지원값의 superset이다. resolver는 현재 모델이 지원하는 값을 확인해야 하며, 미지원 값을 묵시적으로 전달하지 않는다. 하향 매핑이 필요하면 adapter의 명시적 매핑을 쓰고, runtime에서 관측한 실제 값은 `actual_effort_level`에 verbatim으로 남긴다.

외부 도구는 상태 파일을 직접 읽지 않고 `bin/forge status --json`을 사용한다.

새 core의 managed Work에서는 같은 정책 원본을 pin하되 실행 권한·budget·Work verdict는 core가 맡는다. 이 latest-only snapshot과 Bellows 로그는 관찰 자료이며 core ledger의 전이·승인·완료를 대신하지 않는다. 실제 전달한 지침·profile·source는 Attempt의 context provenance로 따로 기록한다. 세부 전환은 [최종 개선 계획](../plan/code-forge-final-improvement-plan-2026-10-18.md)을 따른다.

## 9. 금지 패턴

- HIGH라는 이유만으로 모든 문서와 에이전트를 호출
- 동일한 탐색을 여러 에이전트가 중복 수행
- 같은 모델의 다수결이나 합의를 정확성의 증거로 취급
- fresh critic에게 작성자의 긴 추론과 결론을 먼저 주입
- 실제 검증 없이 effort·라운드·fan-out만 증가
- 호스트별 모델 ID를 공통 정책의 불변 규칙으로 고정
