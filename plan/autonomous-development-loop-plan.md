# code-forge 자율 개발 폐쇄 루프 개선 계획

> 상태: 역사 자료 · 2026-10-18 통합 계획에서 실행 순서와 엔진 선택 재검토
> 작성일: 2026-08-31
> 기준점: code-forge HEAD 1779c8a와 현재 미커밋 작업 트리, flow-toolkit HEAD d15bf3c
> 문서 역할: 당시 요구사항·판단 근거 보존. 현재 실행 순서는 [최종 개선 계획](code-forge-final-improvement-plan-2026-10-18.md)을 따른다. 아래 flow-toolkit 엔진·경로·수치·지원 설명은 당시 제안이며 현재 구현 완료를 뜻하지 않는다.

---

## 0. 결론

현재 code-forge의 최상위 구조는 유지하는 편이 맞다. agents, skills, rules, modules, hooks, docs의 구분은 Claude Code 플러그인으로서 자연스럽고, 얇은 기본 지침·점진 적재·독립 리뷰·가설 기반 재시도라는 방향도 좋다.

문제는 저장소의 폴더 구성이 아니라 실행 책임이 프롬프트와 대화 컨텍스트에 몰려 있다는 점이다. 지금의 /start는 좋은 UX 진입점이지만, 634줄짜리 문서가 입력 분석부터 구현, 테스트, PR, 회고까지 모두 설명한다. progress.md와 quality.jsonl은 사람에게 상태를 보여주기에는 유용하지만, 충돌·재개·무효화·증거 신선도를 보장하는 실행 상태로는 부족하다.

따라서 다음 구조를 채택한다.

| 결정 | 채택안 |
|---|---|
| code-forge 전체 구조 | 유지. 대규모 디렉터리 재편 금지 |
| 현재 Paperthin 참고 리팩터링 | 되돌리거나 재작성하지 않고 현재 diff를 구현 baseline으로 사용 |
| /start | 얇은 단일 진입점으로 유지하고 phase 세부 지침은 늦게 적재 |
| flow-toolkit | 별도 저장소로 유지하고 결정론적 실행 엔진으로 재정의 |
| 두 저장소의 결합 | 하나의 버전 계약과 하나의 bridge로만 연결 |
| 개발자용 윤문 | 작은 docs-polish 스킬로 code-forge 안에 유지 |
| 라우팅 정책 | references/routing-policy.md가 model class, effort, fan-out의 유일한 소스 |
| 런타임 상태 | opt-in autopilot run만 flow-toolkit의 run store가 권위 상태 |
| 기존 상태 표면 | bin/forge의 잠금·원자 쓰기 계약과 status --json 호환을 유지 |
| progress.md | 기존 경로에서는 보존하고, autopilot에서는 권위 상태가 아닌 사람용 projection |
| hooks | 빠른 피드백·관찰용. 최종 통과 판정 권한 없음 |
| 최종 품질 게이트 | flow CLI의 검증된 exit code와 evidence 계약 |
| 자가개선 | 후보 생성·평가는 자동화하되 영구 규칙 승격은 사람 승인 |
| 기존 /start --auto | 동작 보존 |
| 새 무인 경로 | 별도 /start --autopilot 플래그로 opt-in |

한 문장으로 요약하면 다음과 같다.

> code-forge는 작업을 이해하고 host를 움직이는 얇은 제품 계층, flow-toolkit은 opt-in run의 상태·증거·재시도·무효화를 책임지는 별도 실행 계층으로 둔다.

---

## 1. 목표 상태

### 1-1. 사용자가 원하는 전체 흐름

~~~text
티켓 / Markdown / Figma / 자유 텍스트
  → 입력 정규화
  → 요구사항과 수용 조건 작성
  → 결정적 명세 gate + 필요할 때 독립 검증
  → AC별 테스트 케이스와 추적성 작성
  → 결정적 TC gate + 필요할 때 독립 검증
  → 구현 계획
  → 계획 gate + 필요할 때 독립 검증
  → 프로젝트 컨벤션에 맞춘 구현
  → scope/diff gate + 필요할 때 독립 코드 리뷰
  → 누수·보안·과설계·불필요한 리팩터링 점검
  → 변경 의미 분류
  → 가장 알맞은 테스트 선택·실행
  → UI 기능이면 provisioned platform runner로 화면 흐름 검증과 증거 수집
  → 실패 원인 분류와 최소 수정
  → 최초로 잘못된 phase 귀속
  → 영향받은 downstream 산출물 무효화·재실행
  → 개선 후보 생성·회귀 평가
  → 필수 게이트 100% 통과
  → 인간 최종 검토
~~~

### 1-2. 여기서 말하는 100%의 정확한 의미

100%는 버그가 절대 없다는 뜻도, 코드 커버리지 100%도, LLM 자신감 100%도 아니다. 다음 계약이 모두 충족됐다는 뜻이다.

- 입력 source가 모두 식별되고 revision 또는 content hash가 기록됨
- 필수 요구사항과 AC의 source coverage가 100%
- 모든 필수 AC가 하나 이상의 검증 방법과 연결됨
- 모든 필수 TC가 PASS
- required인데 SKIP된 검증이 0개
- blocking review finding이 0개
- stale artifact와 stale evidence가 0개
- 최종 HEAD SHA와 검증한 tested SHA가 일치
- 미해결 보안·개인정보·외부 효과 경고가 0개

이 정의를 final gate가 기계적으로 판정해야 한다. 자유 서술의 “문제없어 보임”은 통과 증거가 아니다.

### 1-3. 인간이 마지막에만 보는 범위

다음 조건을 모두 만족하는 작업은 최종 검토 전까지 자동 진행한다.

- 대상 저장소 내부의 가역적 변경
- 요구사항 충돌이 없고 기존 근거로 판단 가능
- 운영 데이터와 자격증명을 건드리지 않음
- 외부 공개, 결제, 배포, 영구 삭제가 없음
- 허용된 테스트 환경에서 재현 가능
- 정해진 비용·시간·재시도 예산 안에 있음

아래 상황은 사람을 일찍 부르는 것이 실패가 아니라 올바른 안전 동작이다.

- Figma, 티켓, 정책, 코드가 서로 충돌하며 어느 것이 우선인지 근거가 없음
- 제품·디자인 의사결정이 필요함
- 자격증명이나 운영 환경 권한이 필요함
- 데이터 마이그레이션, 삭제, 외부 공개, 비용 발생이 포함됨
- 보안 또는 개인정보 판단이 필요함
- 서로 다른 판별 가설을 모두 소진했는데 같은 실패가 계속됨

초기 버전은 자동 merge를 하지 않는다. push와 Draft PR도 사용자가 해당 run에 명시적으로 허용한 경우만 수행한다.

autopilot 플래그 선택과 run manifest 승인은 해당 run의 가역적 repo-local 구현 checkpoint를 미리 승인한 것으로 본다. 작업 경로, 쓰기 허용 범위, 실행 가능한 테스트, 외부 도구, 비용·시간, commit/push/PR 허용 여부를 고정하며, 범위가 커지면 새 승인이 필요하다. commit/push/PR checkpoint와 CRITICAL routing checkpoint는 우회하지 않는다.

---

## 2. 현재 구조 감사

### 2-1. 유지할 기반

| 영역 | 현재 장점 | 근거 |
|---|---|---|
| 단일 진입점 | Markdown, 텍스트, Pencil, Figma를 /start 하나로 받음 | skills/start/SKILL.md:67-198 |
| 위험 기반 라우팅 | 파일 수보다 모호성·영향도·가역성·검증 공백을 봄 | references/routing-policy.md:17-37 |
| 점진 적재 | C0-C3 사다리와 fresh critic 원칙이 있음 | references/routing-policy.md:39-52 |
| 구현 규율 | GROUND → APPLY → VERIFY → ADAPT가 이미 정리됨 | rules/thinking-model.md:24-93 |
| 독립 리뷰 | reviewer에게 작성자의 긴 추론을 넘기지 않는 원칙이 있음 | references/routing-policy.md:64-69 |
| 테스트 라우팅 | 변경 경로가 아니라 변경된 행동을 기준으로 테스트를 고름 | skills/start/SKILL.md:399-426 |
| bounded repair | 같은 실패·같은 가설 반복을 금지하고 총 3회 상한을 둠 | skills/start/SKILL.md:470-476 |
| E2E 진단 | 테스트·제품·환경 문제를 나누고 fresh critic을 제한적으로 사용 | skills/e2e/SKILL.md:199-290 |
| 세션 복구 | SessionStart는 progress 원문 대신 compact brief만 주입 | hooks/session-init.sh:218-270 |
| 관찰 가능성 | quality.jsonl, route.json, forge-glow surface가 존재 | docs/contracts/state-schema.md:21-35 |
| 개발 문서 윤문 | 짧은 skill과 온디맨드 가이드로 기술 요소를 보호 | skills/docs-polish/SKILL.md, skills/docs-polish/references/developer-writing.md |

### 2-2. 핵심 결함

| 우선순위 | 결함 | 영향 |
|---|---|---|
| P0 | /start가 634줄, 약 29 KiB의 단일 실행 문서 | /start를 고르는 순간 모든 phase 지침이 함께 적재됨 |
| P0 | 명세·AC·TC가 stable ID와 schema로 남지 않음 | 누락률과 downstream 영향을 기계적으로 계산할 수 없음 |
| P0 | 대화와 progress.md가 실행 상태를 대신함 | compact, crash, host 전환 후 재탐색과 추론이 반복됨 |
| P0 | quality-gate.sh가 항상 exit 0 | 관찰용 경고와 authoritative gate가 혼재됨 |
| P0 | tested SHA와 evidence hash가 없음 | 테스트 뒤 코드가 바뀌어도 최종 통과로 오인 가능 |
| P0 | flow-toolkit에 실제 개발 phase 상태 머신이 없음 | 현재는 external data 준비 여부만 전환 |
| P0 | flow-toolkit 테스트와 CI가 없음 | 자율 controller로 승격할 근거가 없음 |
| P1 | /test, /e2e, /generate-test, .policy가 TC를 각자 해석 | 테스트 선택과 추적성의 단일 진실이 없음 |
| P1 | E2E screenshot, trace, JSON, console/network가 필수 evidence index로 묶이지 않음 | 실패 진단과 최종 인간 검토가 다시 로그 탐색에 의존 |
| P1 | author/verifier packet schema가 없음 | 독립 리뷰 원칙이 프롬프트 품질에 따라 흔들림 |
| P1 | cache와 artifact invalidation이 없음 | 같은 파일·문서·도구 결과를 phase마다 다시 읽음 |
| P1 | 회고가 반복 횟수 위주 | 개선 후보가 실제 품질을 높였는지 비교하지 못함 |
| P2 | always-loaded rule에 delivery·문서 라우팅까지 섞임 | 코드 작업이 아닌 턴에도 불필요한 기본 토큰 사용 |
| P2 | Smith의 역할 체인과 plugin agents가 병렬로 존재 | 역할 계약이 두 군데에서 drift할 위험 |

### 2-3. flow-toolkit의 현재 수준

flow-toolkit은 별도 저장소로 둘 가치가 있지만, 지금 상태를 “자율 실행 엔진”이라고 부르면 안 된다.

- workflow 상태는 needs_external_data와 ready_for_analysis 정도만 있음
- 같은 ticket으로 동시에 시작하면 같은 디렉터리를 덮어쓸 수 있음
- revision, compare-and-swap, lease, heartbeat, idempotency key가 없음
- resume 입력에 content hash와 schema 검증이 없음
- run report는 테스트를 실행하지 않고 기존 result.json을 집계만 함
- skip을 분모에서 제외하므로 최종 100% 게이트에 그대로 쓸 수 없음
- stale 검사는 component 경로와 Figma 존재 여부 정도에 그침
- artifact promote와 undo는 TODO
- 문서에 보이는 일부 명령과 실제 CLI 구현이 다름
- flow policy schema와 code-forge template schema가 서로 다름
- package lint가 no-op이고 unit/integration/CI가 없음
- 범용 도구를 표방하지만 일부 rules와 경로가 Claude·React·기존 프로젝트 관행에 묶임

따라서 flow-toolkit은 공개·자동 활성화보다 계약·테스트·정직화가 먼저다.

### 2-4. 현재 Paperthin 참고 리팩터링과의 병합 판정

2026-08-31에 다시 확인한 working tree는 추적 파일 77개의 대규모 변경과 기존 untracked 파일 7개를 포함한다. 이 문서가 추가한 파일은 plan/autonomous-development-loop-plan.md 하나다. 숫자는 당시 snapshot 설명일 뿐이며 이후 작업의 진실은 매번 git status --short와 파일별 git diff로 다시 확인한다.

현재 diff에서 이미 해결 중인 항목은 새로 만들지 않는다.

| 기존 diff의 방향 | 판정 | 새 계획에서의 처리 |
|---|---|---|
| AGENTS.md와 CLAUDE.md thin spine | 유지 | 자동 적재 문서를 다시 키우지 않고 측정만 추가 |
| routing-policy의 위험 기반 FAST/BALANCED/DEEP 정책 | canonical | flow나 /start에 별도 모델·fan-out 표를 만들지 않음 |
| 고정 agent 수·강제 합의·고정 팀 평가 제거 | 유지 | 삭제 문서와 패턴을 부활시키지 않음 |
| build/review/coding guide의 자동 적재 해제 | 유지 | 선택 phase에서 직접 필요한 절만 읽음 |
| Flow 자동 호출 제거와 opt-in 전환 | 유지 | autopilot도 별도 opt-in이며 기존 기본 경로에 연결하지 않음 |
| Codex 지원 수준 정직화와 안전한 stdin bridge | 유지 | native 지원으로 과장하지 않고 bridge 계약을 재사용 |
| emit-event의 process lock·atomic write 강화 | 불변 조건 | 새 projection도 반드시 bin/forge를 통하고 직접 상태 파일을 쓰지 않음 |
| progress archive의 safe ID·lock·idempotency | 불변 조건 | SessionStart GC나 무잠금 재작성을 추가하지 않음 |
| 문서·동시성·archive 검증 script 추가 | 유지 | 최종 검증 행렬에 포함 |
| docs-polish와 기존 plan 파일 | 보존 | 임의 삭제·흡수·이름 변경 없음 |

새 설계가 실제로 더해야 하는 것은 기존 리팩터링을 다시 설명하는 문서가 아니라 stable REQ/AC/TC, opt-in run protocol, worktree-bound evidence, dependency invalidation, adaptive testing, 평가 기반 개선이다.

---

## 3. 저장소별 책임

### 3-1. 책임 표

| 주체 | 소유하는 것 | 소유하지 않는 것 |
|---|---|---|
| code-forge | 사용자 진입 UX, source adapter 호출, 역할·권한 정책, host별 agent/tool 실행, 기존 상태 호환 표면, developer writing, 최종 사람용 projection | autopilot run 상태 머신, lease, evidence freshness 계산, 프로젝트별 AC 내용 |
| flow-toolkit | opt-in autopilot의 versioned run protocol, phase transition, artifact DAG, gate, lease, idempotency, evidence index, invalidation, resume, improvement experiment | Claude slash 문법, 특정 모델 이름, 프로젝트 코딩 컨벤션, Figma/Jira 자격증명 |
| 대상 프로젝트 | 실제 요구사항·정책·AC·TC, 소스 코드, 테스트 코드, fixture, runner config와 baseline | 범용 orchestration 엔진 |
| forge-glow | bin/forge status --json을 통한 run과 gate 상태의 읽기 전용 표시, 비용·진행·알림 | 상태 파일 직접 읽기, 상태 변경, pass/fail 판정 |
| Smith | 프로젝트 전용 agent를 STATE+ACT로 컴파일 | 기본 runtime controller |
| 별도 coding-practice | Whetstone 학습·연습 UX | code-forge runtime 상태와 canonical rule 직접 변경 |
| 인간 | 제품·디자인 결정, 위험 권한, 개선 규칙 승격, 최종 결과 검토 | 정상적인 repo-local phase 진행 |

### 3-2. flow-toolkit을 별도 저장소로 두는 이유

1. Claude 플러그인 없이 Codex나 다른 host에서도 같은 run을 재개해야 한다.
2. state, schema, lease, evidence는 플러그인 release보다 독립적으로 테스트하고 버전 관리해야 한다.
3. code-forge의 “외부 의존성 없이 기본 가치 제공” 원칙을 지킬 수 있다.
4. runtime trace와 screenshot을 플러그인 저장소에 넣지 않아도 된다.
5. controller 장애가 code-forge의 기본 /start를 깨뜨리지 않게 할 수 있다.

별도 저장소라고 해서 느슨하게 방치해서는 안 된다. 다음 결합 계약은 필요하다.

- protocol version handshake
- 최소·최대 호환 버전 표
- 단 하나의 code-forge bridge
- JSON input/output schema
- idempotency key와 expected revision
- 명확한 exit code
- 기존 /start는 flow 없이 유지, 명시한 autopilot의 미설치·비호환은 structured unavailable

기존 /start는 flow가 없어도 그대로 동작한다. 다만 사용자가 --autopilot을 명시했는데 flow가 없거나 비호환이면 일반 경로로 조용히 바꾸지 않는다. structured unavailable을 반환하고 기존 /start로 다시 실행할 선택지만 안내한다.

Git submodule이나 flow 소스 복사는 사용하지 않는다. code-forge skill 여러 곳에서 flow 명령을 직접 호출하는 구조도 없앤다. JSON payload는 stdin 또는 검증된 mode-600 임시 파일로 전달하고 raw 사용자 입력·오류 로그를 shell argv에 넣지 않는다.

### 3-3. 현재 결합도의 비판적 판정

현재 결합은 “런타임은 약하지만 의미 중복은 강한” 좋지 않은 중간 상태다.

| 축 | 현재 | 목표 |
|---|---|---|
| 런타임 의존 | opt-in·휴면이라 낮음 | opt-in이지만 실제 vertical slice 동작 |
| 계약 | 문서와 ad-hoc JSON 위주 | versioned schema와 compatibility test |
| 상태 | .claude/state와 ~/.flow가 병렬 | 기존 경로는 bin/forge 계약 유지, opt-in run만 flow 권위 |
| 회고 | flow retro와 forge whet 역할 중복 | flow는 incident/eval, forge whet는 local draft 호환, 별도 Whetstone은 학습 UX |
| 테스트 정책 | code-forge와 flow-rules에 중복 | code-forge modules와 프로젝트가 컨벤션 소유 |
| 명령 호출 | /start 여러 phase와 hook에 분산 | bridge 한 곳 |

### 3-4. docs-polish의 위치

docs-polish는 별도 저장소로 빼지 않는다.

- 현재 skill은 27줄, 상세 가이드는 61줄이라 code-forge를 비대하게 만들지 않는다.
- README, PR, Issue, ADR, 계획서, 최종 리포트는 code-forge 실행 결과와 직접 연결된다.
- im-not-ai의 한국어 문체 분류 아이디어만 참고하고, 기술 요소 삭제·AI 탐지 회피·다중 agent 파이프라인은 가져오지 않는 현재 방향이 맞다.
- 윤문은 canonical JSON을 고치는 phase가 아니다. 요구사항 ID, 수치, 코드, 명령, 경로, MUST/SHOULD 강도를 고정한 뒤 사람용 Markdown projection에만 적용한다.

나중에 다국어 corpus, 독립 CLI, 대규모 회귀 suite가 생기고 code-forge 밖 사용량이 더 커질 때만 별도 저장소를 재검토한다.

---

## 4. 목표 실행 아키텍처

### 4-1. 전체 구조

~~~text
사용자
  │
  ▼
code-forge /start --autopilot
  ├─ 입력 source adapter: text / MD / ticket / Figma
  ├─ host adapter: Claude / Codex
  ├─ role executor: author / critic / builder / reviewer / tester
  └─ 사람용 진행·최종 리포트
  ▲                     │
  │ next action         │ result receipt
  │                     ▼
flow-toolkit controller ── versioned JSON envelope
  ├─ run state machine
  ├─ artifact dependency graph
  ├─ gate evaluator
  ├─ lease + idempotency
  ├─ evidence index + SHA freshness
  ├─ failure signature + invalidation
  └─ improvement experiment
  │
  ├─ ~/.flow/projects/{repoKey}/runs/{runId}
  ├─ 대상 프로젝트의 코드·테스트·선택적 .policy
  └─ forge-glow read-only projection
~~~

### 4-2. controller와 host의 step protocol

flow-toolkit은 모델을 직접 실행하지 않는다. controller와 code-forge host adapter가 다음 한 단계짜리 handshake를 반복한다.

1. code-forge가 source snapshot과 권한 manifest로 opt-in run을 생성한다.
2. flow가 action_id, phase, expected_revision, artifact pointer, 종료 조건이 담긴 next action을 반환한다.
3. code-forge가 현재 host에서 필요한 agent 또는 tool을 선택·실행한다.
4. code-forge가 action_id, idempotency key, output hash, evidence pointer, 실제 capability와 실제 route를 stdin JSON으로 전달한다.
5. flow가 schema·revision·lease·gate를 검증한 뒤 한 번만 transition한다.
6. terminal 상태가 될 때까지 반복한다.

외부 부수효과의 exactly-once를 로컬 lock만으로 약속하지 않는다. provider가 idempotency key나 조회 가능한 operation ID를 지원하면 이를 사용하고, 호출 뒤 receipt 기록 전에 crash가 나서 결과를 확인할 수 없으면 unknown_external_effect로 blocked 처리한다. 자동 재호출은 금지한다.

flow만 autopilot run state를 쓴다. code-forge는 run.json을 직접 수정하지 않으며, 기존 code-forge telemetry나 projection이 필요하면 현재 bin/forge emit-event 경로를 사용한다. 외부 consumer는 flow 파일이나 .claude/state를 직접 읽지 않고 bin/forge status --json만 사용한다.

지원 수준은 다음과 같이 고정한다.

| 경로 | 현재 의미 | 이 계획의 처리 |
|---|---|---|
| Claude native | skills, agents, hooks가 실제 동작 | 첫 host와 회귀 기준 |
| Claude → Codex bridge | 공식 plugin 사용자 경로와 code-forge CLI wrapper가 부분 동작 | prompt를 workspace 밖 mode-600 임시 파일과 stdin으로 전달하고 --ignore-user-config 사용 |
| Codex native | AGENTS.md 로드는 가능하지만 skill/agent/hook adapter는 미배선 | docs/codex-coexistence.md의 dry-run compiler P1과 opt-in P2 뒤에만 지원 선언 |

Codex read-only sandbox는 로컬 파일 쓰기 경계일 뿐 MCP, API, plugin, hook의 외부 부수효과를 증명하지 않는다. CRITICAL verifier는 해당 도구가 비활성 또는 stub인 통제 profile에서만 실행한다. 전역 skill 설치, symlink farm, 사용자 홈 자동 수정은 하지 않는다.

model class, effort, fan-out 판단은 references/routing-policy.md만 소유한다. route.json은 host resolver와 eval이 준비될 때까지 telemetry/advisory이며 controller가 실제 모델 전환을 했다고 간주하지 않는다.

### 4-3. run, phase, gate 상태

수명주기가 다른 값을 한 enum에 섞지 않는다.

- run_status: queued, running, awaiting_external, blocked, completed, failed, cancelled
- phase_status: pending, ready, running, passed, failed, invalidated, cancelled
- gate_status: pending, pass, fail, blocked, not_applicable

required gate에는 not_applicable을 사용할 수 없다. optional 검증만 실행 전에 근거와 함께 not_applicable로 고정할 수 있다. completed, failed, cancelled는 terminal run 상태다. blocked와 awaiting_external은 resume 가능하지만 reason code와 필요한 actor가 있어야 한다.

자유 문자열 phase와 status를 섞지 않는다. 모든 transition은 expected revision과 actor를 받아야 하며, 허용되지 않은 이전 상태·lease owner·artifact 조합의 갱신은 거부한다. 정확한 전이표, terminal 정의, exit code는 P1 reducer fixture가 권위다.

### 4-4. phase와 gate

| Phase | 주 작성자 | 권위 산출물 | Gate |
|---|---|---|---|
| INTAKE | code-forge adapter | input manifest | source revision/hash와 scope 식별 |
| SPEC | main 또는 analyst 역할 | requirements + AC | 필수 source coverage 100% |
| SPEC_REVIEW | deterministic validator, 조건부 fresh critic | spec findings | blocker 0, 모호함 분류 완료 |
| TC | assayer 또는 test planner 역할 | traceability + TC | 모든 필수 AC에 검증 방법 연결 |
| TC_REVIEW | deterministic validator, 조건부 fresh critic | TC findings | required AC coverage 100% |
| PLAN | main/architect 역할 | implementation plan | allowed paths, rollback, 검증 계획 존재 |
| PLAN_REVIEW | deterministic validator, 조건부 fresh critic | plan findings | AC/change mapping과 scope blocker 0 |
| BUILD | builder 역할 | code diff | scope와 convention 계약 준수 |
| CODE_REVIEW | deterministic scope/diff validator, 조건부 code-reviewer | review findings | bug·보안·누수·과설계 blocker 0 |
| TEST_SELECT | deterministic classifier + planner | change classification + test plan | 변경 의미와 AC가 테스트에 매핑 |
| TEST_EXECUTE | runner adapters | normalized evidence | required PASS, required SKIP 0 |
| DIAGNOSE | repair 역할 | incident + hypothesis | 새 가설과 가장 싼 판별 실험 존재 |
| FINAL_GATE | flow evaluator | final decision | stale 0, tested SHA = final SHA |
| HUMAN_REVIEW | 사용자 | accept 또는 follow-up | 최종 판단 |

phase는 agent 이름이 아니다. 작은 작업은 같은 agent가 여러 author phase를 수행할 수 있다. schema, coverage, freshness 같은 결정적 검사는 항상 실행하지만 fresh critic은 자동 기본값이 아니다. routing-policy의 C3 조건, 즉 HIGH의 검증 공백이나 독립 관점이 결정을 바꿀 때와 CRITICAL에서만 연다. 독립 검증을 열 때 author의 긴 추론은 넘기지 않는다.

### 4-5. 새 agent를 늘리지 않는 원칙

초기에는 기존 역할을 재사용한다.

- main 또는 analyst: spec author
- analyst의 fresh invocation: 조건이 충족된 spec critic
- architect: 조건이 충족된 고위험 plan critic
- implementor 또는 main: builder
- code-reviewer: code critic
- assayer: test author
- flow deterministic validators: coverage·schema·freshness verifier

기본 fan-out은 0~2개다. 세 번째 read-only lane은 앞선 두 결과가 서로 다른 새 미해결 질문을 만들었을 때만 추가한다. HIGH라는 이유만으로 planner, architect, critic, team을 모두 호출하지 않는다. 같은 모델의 다수결, 강제 합의, 고정 라운드는 gate evidence가 아니다.

별도 spec-reviewer, test-reviewer agent 파일은 fixture에서 기존 역할로 품질이 나오지 않을 때만 추가한다. phase 수를 agent 수로 그대로 옮기지 않는다.

---

## 5. 권위 상태와 산출물 계약

### 5-1. 외부 run store

기본 runtime 산출물은 프로젝트 저장소 밖에 둔다.

~~~text
~/.flow/projects/{repoKey}/runs/{runId}/
├── run.json
├── events.jsonl
├── inputs/
│   ├── manifest.json
│   └── snapshots/
├── artifacts/
│   ├── requirements.json
│   ├── traceability.json
│   ├── implementation-plan.json
│   ├── change-classification.json
│   └── test-plan.json
├── reviews/
│   ├── spec-review.json
│   ├── tc-review.json
│   ├── plan-review.json
│   └── code-review.json
├── receipts/
│   └── {actionId}.json
├── evidence/
│   ├── index.json
│   ├── tests/
│   ├── screenshots/
│   ├── traces/
│   └── logs/
├── incidents/
│   └── {incidentId}.json
└── reports/
    ├── progress.md
    └── final.md
~~~

큰 screenshot, trace, video, raw stdout은 evidence 아래에 두고 모델 컨텍스트에는 경로와 digest만 전달한다.

run 디렉터리는 기본 mode 700, 민감할 수 있는 파일은 mode 600으로 만든다. source snapshot, evidence, incident마다 public/internal/sensitive 분류와 retention_until을 기록한다. 모델에 전달하는 packet은 원본이 아니라 필요한 최소 redacted derivative를 기본으로 사용한다. 자동 GC는 만들지 않고, 잠금이 있는 명시적 retention 명령과 감사 event가 준비된 뒤에만 삭제한다.

### 5-2. 프로젝트에 남길 것

프로젝트 공유가 필요한 durable truth만 선택적으로 승격한다.

~~~text
.policy/
├── config.json
├── requirements/
├── test-cases/
└── traceability/
~~~

기존 flat .policy 파일은 migration adapter로 읽는다. 새 .forge 같은 세 번째 namespace는 당장 만들지 않는다. 이미 .policy와 ~/.flow가 있는 상황에서 새 루트를 추가하면 오히려 source of truth가 늘어난다.

기본은 external-only다. 팀이 version control을 원할 때만 accepted requirements와 TC를 .policy로 promote한다. 실행 로그와 screenshot은 기본적으로 커밋하지 않는다.

~/.flow는 진행 중 run의 권위 저장소이지 팀의 유일한 장기 완료 증거가 아니다. 최종 결과를 PR이나 다른 host와 공유할 때는 redacted evidence index, tested fingerprint, gate 결과, 승인된 artifact hash를 프로젝트가 선택한 CI artifact 또는 승인된 저장소로 export한다. raw screenshot·trace의 보존 위치와 만료는 pointer로 남기며, 공유할 수 없는 로컬 evidence만으로 원격 승인을 자동 생성하지 않는다.

기존 flat .policy JSON과 목표 구조의 이행은 한 번에 바꾸지 않는다.

| 단계 | 읽기 | 쓰기 | 호환 조건 |
|---|---|---|---|
| legacy | 기존 consumer가 flat JSON 읽기 | 기존 writer 유지 | 현재 /test, quality-gate, flow lint 회귀 |
| dual-read | adapter가 legacy와 v2를 읽음 | 새 autopilot만 v2 external store에 씀 | old/new/mixed fixture 모두 같은 의미 |
| promote | 명시 승인된 truth만 .policy로 export | 단일 promotion owner | export hash와 source run 기록 |
| retire | 모든 consumer migration 뒤 legacy write 중단 | v2만 | downgrade 필요 여부와 제거 release 별도 결정 |

schema 사본을 code-forge와 flow 양쪽에서 수동 관리하지 않는다. flow가 machine schema를 소유하고 code-forge는 compatibility profile과 golden fixture로 소비 계약을 검증한다.

### 5-3. 모든 artifact의 공통 필드

| 필드 | 목적 |
|---|---|
| schema_version | 호환성 판단 |
| artifact_id | 안정적인 참조 |
| run_id | 실행 귀속 |
| producer_role | 작성 주체 |
| created_at | 생성 시각 |
| input_artifact_ids | dependency |
| input_hashes | stale 판정 |
| content_hash | 불변성 확인 |
| source_refs | ticket/Figma/file revision |
| base_sha, head_sha | 코드 기준점 |
| worktree_fingerprint | tracked diff, 허용된 untracked 파일, 관련 config를 포함한 실제 작업점 |
| status | draft/passed/failed/invalidated |

LLM의 숨은 추론은 저장하지 않는다. 근거, 결정, 반례, 불확실성, 다음 검증 방법만 구조화한다.

### 5-4. requirement와 AC

각 항목은 stable ID를 갖는다.

~~~json
{
  "requirement_id": "REQ-001",
  "source_refs": ["SRC-001"],
  "text": "사용자는 이메일로 로그인할 수 있다",
  "priority": "required",
  "acceptance_criteria": [
    {
      "ac_id": "AC-001",
      "given": "유효한 계정이 있고",
      "when": "올바른 이메일과 비밀번호를 제출하면",
      "then": "인증 후 지정 화면으로 이동한다",
      "validation_type": "e2e"
    }
  ]
}
~~~

input manifest는 문서 전체를 한 덩어리로 coverage 계산하지 않는다. ticket field, Markdown heading/문단, Figma node/property처럼 재현 가능한 source_segment_id를 만들고 각 segment에 다음 disposition을 둔다.

- covered: 하나 이상의 requirement 또는 AC에 연결
- assumption: source에 없는 해석이며 승인 또는 명시적 검증 필요
- conflict: 다른 source와 충돌하여 사람 결정 전 final gate 불가
- out_of_scope: 이유와 승인 주체가 있어야 제외 가능
- informational: 검증 대상이 아닌 배경이며 근거 기록 필요

required source coverage 100%는 required segment가 covered이거나 승인된 out_of_scope여야 한다는 의미다. assumption과 conflict를 covered로 계산하지 않는다. spec author는 required segment를 스스로 informational 또는 out_of_scope로 내려 coverage를 만들 수 없다. source adapter의 결정적 field policy, 조건부 verifier, 또는 사람 결정이 필요하다. stable ID는 source namespace와 persisted lineage를 기반으로 유지하고 content hash는 revision 판정에 쓴다. 삭제·분할·병합은 supersedes와 tombstone을 남긴다. source에서 직접 확인되지 않은 해석은 required 사실처럼 섞지 않는다.

### 5-5. traceability

traceability의 최소 연결은 다음과 같다.

~~~text
source
  → requirement
    → acceptance criterion
      → implementation change
        → testcase
          → evidence
            → final gate
~~~

모든 필수 AC에는 적어도 하나의 TC가 있어야 하고, 모든 TC 결과는 AC ID와 evidence ID를 가져야 한다. 테스트가 없어도 되는 문서 변경은 AC에 validation_type=docs를 명시하고 link/render/lint 같은 실제 검증을 연결한다.

implementation plan과 builder receipt에는 ac_id별 change_ref, diff hunk 또는 생성 artifact, 충족 이유를 기록한다. 테스트 코드나 fixture만 약화해 PASS를 만든 경우를 막기 위해 product behavior evidence와 test-strength finding을 분리한다. AC 구현 누락인데 mock만 통과하는 경우와 assertion 삭제로 통과하는 경우를 필수 negative fixture로 둔다.

### 5-6. review packet

fresh reviewer에게는 전체 대화를 넘기지 않고 다음 packet만 준다.

~~~json
{
  "run_id": "RUN-...",
  "review_type": "spec|plan|code|test",
  "base_sha": "...",
  "head_sha": "...",
  "worktree_fingerprint": "...",
  "artifact_hashes": {},
  "acceptance_ids": [],
  "allowed_paths": [],
  "diff_ref": "...",
  "evidence_refs": [],
  "rubric_ref": "...",
  "context_budget": {}
}
~~~

reviewer 결과는 severity, finding_id, evidence_ref, affected_ac_ids, suggested_test를 가진 JSON이 권위다. Markdown은 사람용 projection이다.

### 5-7. evidence freshness

각 evidence는 다음을 기록한다.

- exact command와 working directory
- started_at, ended_at, exit_code
- base_sha와 tested_sha
- worktree_fingerprint와 관련 파일 content hash
- runner와 config hash
- 관련 AC/TC ID
- stdout/stderr digest와 raw 경로
- screenshot/trace/log 경로
- environment identity
- redaction status와 sensitivity

final gate 직전에 HEAD 또는 worktree_fingerprint가 바뀌면 code review와 관련 test evidence를 자동으로 invalidated 처리한다. 기본 autopilot은 clean disposable worktree를 사용한다. 사용자가 현재 worktree 실행을 명시하면 시작 시 허용된 tracked diff와 untracked manifest를 fingerprint에 묶고 lease 동안 사용자 또는 다른 agent의 동시 수정을 감지하면 덮어쓰지 않고 invalidated 또는 blocked로 전환한다. secret pattern이나 허용 목록 밖 untracked 파일은 내용을 모델 packet으로 읽지 않고 current-worktree mode를 blocked 처리하거나 clean worktree로 전환한다.

---

## 6. 무효화와 재실행

무인 루프에서 중요한 것은 “다시 전부 실행”이 아니라 “어디부터 다시 실행할지”다.

| 변경 또는 실패 | 유지 가능 | 무효화 |
|---|---|---|
| ticket/Figma/MD source revision 변경 | capability cache | SPEC 이후 전부 |
| requirement 또는 AC 변경 | source snapshot | TC 이후 전부 |
| TC만 변경 | 승인된 SPEC | TC_REVIEW, TEST_SELECT, TEST_EXECUTE |
| implementation plan 변경 | SPEC, TC | PLAN_REVIEW 이후 전부 |
| 제품 코드 변경 | SPEC, TC, PLAN | CODE_REVIEW, TEST_SELECT, TEST_EXECUTE |
| 테스트 코드·fixture 변경 | SPEC, TC, 제품 code review | 관련 TEST_EXECUTE |
| test config 또는 environment 변경 | logical artifacts | 관련 evidence |
| final HEAD 변경 | 요구사항·TC | code review와 모든 SHA-bound evidence |
| reviewer rubric 변경 | 구현과 테스트 결과 | 해당 review gate |
| 허용된 worktree fingerprint 변경 | source snapshot | 영향 파일과 연결된 BUILD 이후 artifact |
| lease 밖 사용자·agent 수정 감지 | 이미 확정된 source/spec | 자동 merge하지 않고 해당 run blocked 또는 invalidated |

무효화된 artifact는 삭제하지 않는다. status=invalidated와 이유를 남겨 사고 분석에 사용한다.

기존 code-forge 상태를 projection할 때는 bin/forge emit-event의 read→merge→write 전체 process lock을 그대로 사용한다. Linux flock, macOS shlock fallback, unique temp, atomic rename을 우회하는 별도 writer를 만들지 않는다. progress archive도 safe ID exact match, lock, idempotency를 유지하며 append-only history를 SessionStart에서 GC하거나 앞부분부터 삭제하지 않는다.

---

## 7. 토큰과 컨텍스트 관리

### 7-1. 현재 가장 큰 낭비

현재 자동 적재 spine은 이미 많이 줄었지만, /start 하나가 약 29 KiB이고 선택 순간 모든 phase가 들어온다. 대화가 실행 상태를 대신하므로 phase가 길어질수록 이전 탐색·로그·실패 추론도 계속 들고 간다.

개선의 핵심은 요약을 더 잘하는 것이 아니라 artifact를 context boundary로 쓰는 것이다.

### 7-2. 목표 컨텍스트 계층

| 계층 | 내용 | 적재 조건 |
|---|---|---|
| C0 Spine | 불변 제약, 승인 경계, current run brief, 포인터 | 항상 |
| C1 Local | 대상 파일, 가장 가까운 정상 패턴, 현재 phase의 짧은 실행 packet | 작업 시작 |
| C2 Task | 선택된 skill 하나와 직접 연결된 primary reference 하나 | 로컬 증거로 판단할 수 없을 때 |
| C3 Independent | 산출물, AC, diff, rubric만 있는 fresh review packet | routing-policy의 독립 검증 조건을 만족할 때 |

agent 간에는 transcript가 아니라 artifact ID와 packet을 넘긴다. subagent의 전체 도구 로그도 메인 대화에 합치지 않고 결과 JSON과 5~10줄 요약만 받는다.

이 계획 문서는 설계와 milestone의 기준이지 runtime prompt가 아니다. agent가 70 KiB를 넘는 문서 전체를 매 phase 읽지 않는다. 각 change set은 관련 section 링크, 열린 질문, 허용 경로, 완료 조건, 검증 명령만 담은 2~4 KiB execution brief를 만들고, 막힌 판단에 필요한 절만 범위 지정해서 읽는다.

### 7-3. 초기 예산

아래 값은 20개 안팎의 대표 fixture를 측정하기 전 임시 기준이다.

| 항목 | 초기 상한 |
|---|---:|
| host별 C0 자동 적재 | 관측 2,500 tokens 또는 source 8 KiB |
| /start façade | 1,500 tokens 또는 6 KiB |
| 한 phase 지침·rubric | 3,000 tokens |
| phase 시작 packet | context window의 20% 이하 |
| phase 실행 전 남길 여유 | context window의 50% 이상 |
| PASS evidence digest | 2 KiB 또는 20줄 |
| FAIL evidence digest | 8 KiB 또는 100줄 |
| 같은 immutable 파일의 phase 내 재읽기 | 1회 이하 |
| repeated-read byte ratio | 10% 이하 |
| subagent 간 중복 read | 필수 계약 제외 20% 이하 |
| 기본 read-only lane | 최대 2 |
| gate별 fresh critic | 최대 1 |

큰 diff가 상한을 넘으면 effort를 무작정 올리지 않는다. AC 또는 독립 change cluster 기준으로 나눈다.

### 7-4. /start 다이어트

목표 구조는 다음과 같다.

~~~text
skills/start/SKILL.md
  진입, 옵션, 안전 경계, controller 호출, fallback만 보유

skills/start/references/{intake,spec-gate,plan-gate,build,review-gate,test-selection,delivery}.md
  현재 phase에서만 읽는 host 실행 지침
~~~

phase transition, retry, invalidation, completion은 Markdown이 아니라 flow controller가 소유한다. /start 본문에 routing 표, state schema, PR 템플릿, 전체 phase 요약을 반복하지 않는다.

phase reference는 새 canonical 정책 문서가 아니다. 현재 /start에서 host 실행 절차를 추출한 delta만 두고 model class, effort, fan-out, 상태 enum, 테스트 정책은 각각의 기존 canonical 문서를 링크한다. 측정 없이 파일 수부터 늘리지 않으며, 실제로 독립 적재할 절이 확인된 경우에만 나눈다. 선택 상세에 @${CLAUDE_PLUGIN_ROOT} eager include를 다시 넣지 않는다.

### 7-5. always-loaded rule 다이어트

- thinking-model은 핵심 invariant와 GROUND/APPLY/VERIFY/ADAPT, routing pointer만 남긴다.
- candidate-profile은 profile 우선순위와 최소 소통 규칙만 always-load한다.
- commit 규칙은 delivery phase에서 읽는다.
- docs-polish pointer는 사람용 산출물을 만들 때만 읽는다.
- review-guide, build-guide, coding-standards는 지금처럼 자동 적재하지 않고 해결되지 않은 질문에 필요한 절만 읽는다.
- AGENTS.md와 CLAUDE.md에 카탈로그, 모델표, workflow 전문을 다시 넣지 않는다.

### 7-6. cache

다음 결과는 content hash로 cache한다.

- repo map: manifest, lockfile, CI, workspace, 실제 명령
- convention snapshot: profile과 가까운 정상 패턴
- capability manifest: Figma, tracker, Playwright, host, reviewer availability
- source adapter result: ticket revision, Figma version, file hash
- test selection: change classification + AC/TC/config hash

cache hit라도 dependency hash가 하나라도 다르면 판정 결과를 재사용하지 않는다.

### 7-7. 측정할 telemetry

- input_tokens / completed_required_ac
- phase별 p50/p95 input, cached input, output tokens
- repeated_read_bytes / total_read_bytes
- subagent context overlap ratio
- artifact cache hit과 stale cache 오사용 수
- phase별 first-pass gate rate
- critic이 실제 판정을 바꾼 비율
- finding 하나당 critic token
- compact/crash 후 무수정 resume 성공률
- earliest faulty phase 귀속 정확도
- final SHA와 evidence SHA 불일치 수
- human interruption rate
- autonomous completion rate

raw transcript는 기본 장기 보존 대상이 아니다. 집계값과 artifact pointer만 남긴다.

model, effort, fan-out telemetry는 실제 host가 관측한 값과 권고값을 분리한다. resolver가 없는 동안 actual_model_class와 actual_effort_level은 null이며, route.json만 보고 자동 전환이 일어났다고 평가하지 않는다.

---

## 8. 변경 의미 기반 테스트와 evidence

### 8-1. semantic change classifier

파일 경로만으로 테스트를 고르지 않는다. diff와 AC를 기준으로 다음 태그를 복수 선택한다.

| 태그 | 최소 검증 |
|---|---|
| docs_text | link, markdown, render, 사실 대조 |
| pure_logic | unit 또는 property test |
| state_transition | unit + integration |
| ui_component | component/integration + 접근성 |
| ui_flow | provisioned browser E2E 또는 platform adapter |
| visual_only | render/screenshot 비교 |
| api_contract | contract/integration + fixture |
| persistence | integration/migration/rollback |
| schema_config | parser/schema/build |
| build_runtime | build + smoke |
| security_boundary | security rubric + negative test |

classifier는 테스트를 실행하지 않는다. change-classification artifact를 만들고 test planner가 AC와 연결한다. classifier confidence가 낮으면 더 넓은 테스트를 조용히 돌리기보다 ambiguity를 기록하고 가장 싼 판별 근거를 찾는다.

input manifest에는 validation_profile과 실제 runner capability를 함께 기록한다. browser UI이며 저장소에 Playwright 또는 동등한 provisioned runner가 있을 때만 browser screenshot·trace를 required로 만든다. mobile/native UI는 해당 adapter의 screenshot, device log, accessibility evidence를 사용하고, 지원 adapter가 없으면 required 검증을 SKIP으로 숨기지 않고 awaiting_external 또는 사람 결정으로 전환한다. backend, infra, 문서 작업에 Playwright를 강제하지 않는다.

### 8-2. UI 기능의 필수 evidence

browser UI flow가 바뀌고 provisioned runner가 있으면 다음을 기본으로 남긴다.

- 사용자 흐름의 핵심 상태별 screenshot
- JSON reporter 결과
- 첫 실패부터 Playwright trace
- console error와 page error
- 관련 network failure 요약
- 테스트 환경과 base URL
- tested SHA
- scenario와 AC/TC ID

video는 실패를 trace와 screenshot으로 재현할 수 없을 때만 켠다. 모든 이미지를 모델에 넣지 않고 시각 판단이 필요한 failure packet에만 선택적으로 적재한다.

외부 공개 bucket 업로드는 기본 금지다. PR에 이미지 URL이 꼭 필요하면 sensitivity scan과 redaction을 통과하고, 해당 run에서 사용자가 허용한 저장소만 쓴다.

### 8-3. 테스트 결과 규칙

- required SKIP은 PASS가 아니다.
- flaky 재실행으로 한 번 통과했다고 완료하지 않는다.
- 같은 HEAD, 같은 config, 같은 environment에서 재현 가능한 결과만 최종 evidence로 쓴다.
- snapshot 기준선 갱신은 구현 수정과 분리하고 이유를 기록한다.
- 테스트 자체를 고쳤다면 기존 제품 코드 evidence는 그대로 두되 관련 test evidence는 다시 만든다.
- assertion, mock, fixture가 약해졌다면 제품 행동 evidence도 다시 검증하고 test-strength review를 통과한다.
- 범용 quality-gate.sh는 빠른 advisory feedback으로 유지한다.
- authoritative runner는 실행 명령, exit code, evidence hash를 검증하고 실패 시 non-zero를 반환한다.

---

## 9. 실패 진단과 자동 수리

### 9-1. 실패 분류

모든 실패는 먼저 다음 중 하나로 분류한다.

- source/spec 문제
- AC/TC 추적성 문제
- implementation 문제
- test code 또는 fixture 문제
- environment/capability 문제
- security/permission 문제
- transient external failure

### 9-2. failure signature

signature는 phase, command, normalized error class, failing AC/TC, relevant stack digest, tested SHA, worktree fingerprint, runner/config hash로 만든다.

- 같은 signature에 같은 수정을 반복하지 않는다.
- 새 증거가 없으면 재실행하지 않는다.
- 서로 다른 판별 가능한 가설만 최대 3개까지 시험한다.
- 환경 장애와 제품 장애를 섞지 않는다.
- 수정 후에는 최초 잘못된 phase를 찾고 그 downstream만 무효화한다.

### 9-3. 최초 오류 phase 귀속

예를 들어 E2E assertion 실패가 발생해도 바로 BUILD 탓으로 보지 않는다.

1. AC가 실제 source와 맞는가
2. TC가 AC를 올바르게 표현했는가
3. fixture와 environment가 유효한가
4. 구현이 TC를 위반했는가
5. evidence가 현재 HEAD, worktree fingerprint, runner/config의 것인가

원인이 SPEC이면 SPEC부터, 테스트 선택이면 TEST_SELECT부터, selector면 TEST_EXECUTE의 테스트 artifact부터 다시 간다. 전체 루프를 무조건 처음부터 반복하지 않는다.

### 9-4. no-progress와 blocked

다음 조건 중 하나면 자동 루프를 멈춘다.

- 같은 failure signature에 같은 가설·수정·명령을 반복하려 함
- 새 가설이나 판별 실험이 없음
- 서로 다른 판별 가능한 가설의 총 상한 3개를 소진
- 외부 시스템이 지속적으로 unavailable
- 필요한 사람 결정이 확인됨
- 비용·시간 예산 초과

중단 시 마지막 오류만 보여주지 않는다. 시도한 가설, 반증 결과, 최초 의심 phase, 필요한 다음 증거를 final packet에 넣는다.

같은 signature가 다시 보여도 새 증거와 서로 다른 반증 가능한 가설이 있으면 다음 판별 실험은 허용한다. 총 3회는 채워야 하는 목표가 아니라 비상 상한이다.

---

## 10. 자가개선

자가개선은 “실패할 때마다 규칙 한 줄 추가”가 아니다. 잘못된 규칙이 계속 쌓이지 않도록 실험으로 다룬다.

### 10-1. improvement loop

~~~text
실패 또는 사람 수정
  → incident 구조화
  → 최초 오류 phase와 원인 분류
  → 개선 대상 선택
     prompt / rule / router / schema / fixture / adapter
  → candidate patch
  → 과거 fixture baseline 재생
  → candidate 재생
  → holdout 반례 평가
  → 품질·토큰·latency 비교
  → canary
  → 사람 승인 후 promote
  → rollback 가능 상태로 배포
~~~

### 10-2. incident 최소 필드

- incident_id
- run_id와 phase
- symptom과 failure signature
- expected와 observed
- affected AC/TC
- root cause와 confidence
- earliest_faulty_phase
- attempted hypotheses
- successful correction
- candidate improvement target
- 개인정보 제거 상태

### 10-3. 자동화 가능한 것과 사람에게 남길 것

자동화:

- incident 수집
- 중복 cluster
- candidate rule/prompt 생성
- baseline/candidate/holdout replay
- 품질·토큰·latency 비교
- regression report와 Draft PR 준비

사람 승인:

- canonical rule 영구 승격
- 보안·권한 정책 변경
- 제품 의미 변경
- model/effort 기본값 변경
- auto-merge 허용

Whetstone 학습 UX는 docs/design-principles.md에 정의된 별도 coding-practice 프로젝트 소유다. code-forge의 forge whet는 quality.jsonl에서 local convention 후보를 만드는 compatibility command일 뿐 Whetstone 제품이나 범용 approval UI로 확장하지 않는다. flow-toolkit은 incident, experiment, evaluation 결과를 제공하고, code-forge는 사람이 검토할 Markdown/JSON draft만 투영한다. canonical rule 변경은 별도 승인된 change set과 일반 code review를 거친다.

### 10-4. 외부 사례에서 가져올 것

#### im-not-ai

[im-not-ai](https://github.com/epoko77-ai/im-not-ai)는 기술 문서를 그대로 가져올 대상이 아니라 운영 아이디어의 참고다.

가져올 것:

- 결정적 사전 점수로 light/standard/heavy 경로를 고르는 방식
- 이미 괜찮은 입력의 조기 종료
- 의미·수치·고유명사 같은 불변 요소를 먼저 잠그는 방식
- 변경률 상한과 deterministic gate
- golden case와 인간 작성 반례 corpus
- 단일 source 반복만으로 rule을 승격하지 않고 hold하는 방식

가져오지 않을 것:

- AI 탐지 회피 목적
- 기술 표현을 일반 문체로 바꾸는 규칙
- 모든 문서에 다중 agent 윤문
- 원문의 구조·표·요구 강도를 지우는 과윤문

#### Codex Desktop PR QA

[I Made Codex Desktop QA My Pull Requests Every Hour](https://theaiplatform.app/blog/automating-pull-request-qa-with-codex-desktop/)에서 바로 가져올 가치가 큰 부분은 다음이다.

- 버릴 수 있는 전용 QA checkout
- diff가 테스트 계획을 만들게 하는 방식
- 실제 앱 조작과 screenshot evidence
- 테스트한 뒤 PR HEAD가 바뀌면 approve하지 않는 freshness 규칙
- 동시 QA 1개를 보장하는 lock
- 증상·원인·screenshot을 다음 repair run이 소비하는 구조

그대로 가져오지 않을 것:

- 초기부터 매시간 schedule
- evidence의 public bucket 업로드 기본값
- 하나의 긴 prompt를 controller 대신 사용하는 구조
- 특정 desktop app과 bundle ID에 묶인 실행

#### Labor0

[Labor0를 만든 이유](https://kdy1.dev/2026-8-22-labor0)에서 가져올 것은 다음이다.

- 큰 일을 사람이 검토 가능한 작은 단위로 나누기
- dependency-aware 작업 graph
- CI 실패, conflict, review 반영을 같은 run의 후속 task로 연결
- 사람 결정 node에서만 알림
- 마지막 확인 이후 변경을 요약하는 Catch-up
- GitHub, Sentry, Grafana, schedule 같은 event source 확장

그대로 가져오지 않을 것:

- 첫 단계부터 50개 session 운영
- PR 생성만을 모든 작업의 성공 조건으로 삼는 것
- 안정화 전 graph UI와 원격 runner부터 만드는 것
- 디자인 판단까지 억지로 자동화하는 것

우리에게 필요한 것은 Labor0 복제가 아니라 Spec → TC → Build → Review → Evidence라는 한 개 vertical slice를 정확히 닫는 것이다.

---

## 11. 목표 파일 구조

### 11-1. code-forge

~~~text
code-forge/
├── skills/start/SKILL.md
├── skills/start/references/phase-*.md   # 측정으로 분리가 필요한 host delta만
├── skills/docs-polish/
├── agents/{analyst,architect,implementor,assayer,code-reviewer}.md
├── references/routing-policy.md
├── docs/contracts/INTEGRATION.md
├── hooks/
│   └── quality-gate.sh
└── bin/forge
    └── flow bridge와 status projection
~~~

새 top-level 디렉터리를 여러 개 만들지 않는다. code-forge에는 flow schema 사본을 두지 않고 protocol version과 integration profile만 문서화한다.

AGENTS.md, CLAUDE.md, rules 자동 적재 상태는 현재 Paperthin 참고 diff를 baseline으로 삼는다. phase reference는 기존 /start 본문을 의미 보존하며 추출하는 것이고 routing-policy, codex-coexistence, 테스트 정책을 복제하는 새 가이드가 아니다.

Smith의 requirement-analyst, spec-to-testcase 같은 좋은 역할 정의는 재사용하되 /start runtime의 두 번째 orchestration source로 만들지 않는다. plugin-native 역할과 Smith ACT가 공유할 canonical role contract 또는 생성 관계는 별도 소규모 작업으로 정리한다.

### 11-2. flow-toolkit

초기에는 package를 과도하게 쪼개지 않는다. 두 번째 독립 consumer가 생기기 전까지 flow-core 내부 경계로 구현한다.

~~~text
flow-toolkit/
├── packages/flow-core/
│   ├── schemas/
│   │   ├── run.schema.json
│   │   ├── artifact.schema.json
│   │   ├── transition.schema.json
│   │   ├── review-packet.schema.json
│   │   ├── evidence.schema.json
│   │   └── incident.schema.json
│   ├── src/
│   │   ├── domain/
│   │   ├── engine/
│   │   ├── storage/
│   │   ├── adapters/
│   │   └── commands/
│   └── test/
│       ├── unit/
│       ├── integration/
│       ├── concurrency/
│       └── fixtures/
├── packages/flow-rules/
│   └── optional rule packs only
└── .github/workflows/
~~~

flow-rules에 있는 React/Next.js 컨벤션과 프로젝트 회고 규칙은 core runtime과 분리한다. 범용 코딩 컨벤션은 code-forge modules가, 프로젝트별 규칙은 대상 저장소가 소유한다.

protocol을 별도 package로 추출하는 것은 Codex adapter나 다른 runtime이 npm-level dependency를 실제로 요구할 때 한다. 지금 바로 package 3개로 쪼개는 것은 과설계다.

### 11-3. forge-glow

forge-glow는 run.json이나 .claude/state를 직접 읽거나 수정하지 않는다. 유일한 consumer surface인 bin/forge status --json만 소비한다. flow 세부 상태도 code-forge가 이 표면에 additive하게 projection한다.

표시할 최소 정보:

- run ID와 current phase
- required gate 통과 수
- blocker 수
- tested SHA freshness
- active lease와 heartbeat age
- retry budget
- token/cost summary
- 사람 결정 필요 여부

---

## 12. 단계별 구현 계획

### P0. 기준선 보호와 사실 정리

목표: 현재 Paperthin 참고 미커밋 변경을 baseline으로 인정하고, 새 구조 개선을 의미적으로 병합한다.

- [x] git status --short와 git diff로 현재 baseline 재확인
- [x] AGENTS.md 전체와 design-principles, routing-policy, codex-coexistence만 우선 확인
- [x] 기존 리팩터링과 새 불변 조건의 충돌 보고
- [ ] 편집할 파일마다 직전에 git diff -- <path> 재확인
- [ ] 기존 tracked 변경과 untracked plan, scripts, docs-polish를 보존
- [ ] 자동 stash, reset, checkout, git add ., commit, push, PR 금지
- [ ] 현재 diff의 thin spine, routing, Codex, lock, archive 변경을 다시 만들지 않고 누락만 보완
- [ ] flow-toolkit은 현재 clean 상태와 HEAD 기록
- [ ] FT 작업 전 flow-toolkit이 쓰기 가능한 workspace인지 확인
- [ ] flow-toolkit 문서의 TODO·미구현·obsolete 명령을 실제 상태와 일치시킴
- [ ] flow-toolkit 공개 전 회사·개인 식별자와 package name 재감사
- [ ] versioned fixture manifest, oracle owner, replay 명령, 환경 hash 정의
- [ ] 이 문서 §17의 code-forge 전체 검증 행렬 실행

완료 조건:

- 기존 리팩터링의 의도와 새 변경의 추가 목적이 파일별로 설명 가능
- 기존 사용자 변경을 되돌리거나 전면 재작성한 파일 0개
- flow README, AGENTS, help가 실제 구현 이상을 약속하지 않음
- baseline 결과와 token/read 측정 위치가 정해짐
- 환경 상태인 doctor 경고와 실제 코드 검증 실패가 분리됨

rollback:

- reset이나 checkout이 아니라 새로 추가한 hunk만 파일별로 되돌릴 수 있게 작은 patch로 작업한다. 릴리스·상태 migration은 하지 않는다.

### P1. flow 계약과 테스트 기반

목표: 기능 추가 전에 controller가 지켜야 할 불변 조건을 executable test로 만든다.

- [ ] v2 run, artifact, transition, evidence, review, incident schema
- [ ] pure transition reducer
- [ ] run_status, phase_status, gate_status 분리와 전체 허용·거부 전이표
- [ ] append-only events
- [ ] atomic state write와 revision
- [ ] expected revision conflict
- [ ] create-run conflict policy: repoKey + source revision + requested mode
- [ ] idempotency key scope와 TTL
- [ ] expiring lease, heartbeat, crashed lease recovery
- [ ] action receipt: claimed → invoked → recorded
- [ ] worktree fingerprint와 동시 사용자 변경 탐지
- [ ] strict step/tool validation
- [ ] source/evidence/incident sensitivity, mode, retention 계약
- [ ] unit, integration, concurrency fixture
- [ ] CI와 실제 lint
- [ ] legacy/dual-read/promote/retire .policy 호환 fixture

필수 fault fixture:

- 같은 ticket 동시 start
- 같은 resume 중복 전달
- 허용되지 않은 step 완료
- state write 중 process crash
- lease owner 종료
- lease 만료 뒤 late writer 도착
- 외부 tool 호출 뒤 receipt 기록 전 crash
- 같은 ticket의 다른 source revision
- 현재 worktree에서 사용자 동시 수정
- evidence 없는 PASS
- tested SHA 불일치
- 같은 SHA지만 worktree fingerprint 불일치

완료 조건:

- concurrent update 유실 0
- idempotent/reconcilable adapter의 duplicate delivery side effect 1회
- 결과를 조회할 수 없는 external invocation crash는 자동 replay 0, unknown_external_effect block 100%
- crash 후 resume 성공
- invalid transition은 non-zero
- 모든 terminal, resume, cancel, human follow-up 전이가 fixture로 고정
- schema 없는 결과는 gate에서 거부

### P2. Spec → TC plan-only vertical slice

목표: 코드를 쓰지 않고도 입력부터 검증된 계획까지 닫는다.

- [ ] text/MD/ticket/Figma input manifest
- [ ] source revision/hash와 source segment disposition
- [ ] requirements와 stable AC ID
- [ ] supersedes/tombstone을 포함한 split/merge/delete ID 규칙
- [ ] deterministic spec gate와 조건부 fresh review packet
- [ ] AC → TC traceability
- [ ] deterministic coverage gate
- [ ] deterministic TC gate와 조건부 fresh review
- [ ] implementation plan
- [ ] deterministic plan gate와 조건부 fresh review
- [ ] host별 capability와 승인 manifest
- [ ] code-forge /start --autopilot --plan-only
- [ ] 기존 /start와 결과 비교하는 shadow mode

완료 조건:

- 대표 fixture의 필수 source coverage 100%
- 필수 AC의 validation mapping 100%
- required ambiguity가 숨지 않음
- 동일 입력 재실행이 같은 ID와 dependency hash를 생성
- source conflict, 요구 삭제·분할, mixed .policy fixture 통과
- 기존 /start default, --auto, --flow, FORGE_FLOW_AUTO 동작 변화 없음

### P3. 실행 controller와 복구

목표: plan 뒤의 실제 작업을 대화가 아니라 run 상태가 통제한다.

- [ ] disposable worktree 또는 명시된 현재 worktree adapter
- [ ] current-worktree는 허용 diff/untracked manifest와 lease를 fingerprint에 결박
- [ ] phase checkpoint
- [ ] content-addressed artifact DAG
- [ ] invalidation engine
- [ ] agent invocation receipt
- [ ] current run brief
- [ ] compact/crash 후 resume
- [ ] bridge version negotiation
- [ ] flow 미설치 시 기존 /start 무영향, 명시한 --autopilot은 structured unavailable
- [ ] 기존 projection은 emit-event의 flock/shlock, unique temp, atomic rename 사용
- [ ] progress archive safe ID, lock, idempotency 회귀 fixture
- [ ] external consumer status --json golden contract

완료 조건:

- phase 종료 직후 process를 끊어도 다음 host가 재탐색 없이 재개
- 같은 run을 두 host가 동시에 수정하지 못함
- input, HEAD 또는 worktree fingerprint 변경 시 올바른 downstream만 invalidated
- append-only history의 SessionStart 자동 GC와 앞부분 삭제 0건

### P4. 구현·검토·자동 수리

목표: 구현을 마친 뒤 사람보다 먼저 결정적 gate가 검토하고, routing 조건을 만족할 때만 독립 critic을 추가한다.

- [ ] allowed path와 scope enforcement
- [ ] convention snapshot
- [ ] builder receipt
- [ ] AC별 change_ref/diff-hunk/충족 이유
- [ ] base/head가 고정된 code review packet
- [ ] worktree fingerprint가 고정된 review packet
- [ ] deterministic scope/diff gate와 조건부 bug, security, leak, overengineering critic
- [ ] blocking finding 자동 repair
- [ ] repair 후 review 재실행
- [ ] 동일 signature+동일 가설 즉시 중단과 서로 다른 가설 최대 3개 상한
- [ ] earliest faulty phase 귀속
- [ ] assertion 삭제·mock-only PASS·TC 약화 negative fixture

완료 조건:

- blocking finding 0
- out-of-scope 변경 0
- 같은 failure signature와 같은 가설·조치의 반복 실행 0
- 리뷰한 HEAD와 final HEAD가 다르면 자동 invalidation

### P5. adaptive testing과 evidence

목표: 변경 의미에 맞는 가장 작은 충분한 검증을 선택하고 사람이 확인 가능한 증거를 남긴다.

- [ ] semantic change classifier
- [ ] validation profile과 runner capability manifest
- [ ] test plan과 AC/TC mapping
- [ ] 실제 runner adapter
- [ ] normalized command result
- [ ] provisioned browser UI용 Playwright 또는 동등 runner evidence
- [ ] sensitivity scan과 redaction
- [ ] tested SHA freshness
- [ ] worktree fingerprint freshness
- [ ] required SKIP blocker
- [ ] final evidence package

완료 조건:

- test selection이 모든 required AC를 덮음
- required test PASS 100%
- required SKIP 0
- stale evidence 0
- tested SHA = final SHA
- provisioned browser UI fixture에서 screenshot과 trace 경로를 final report에서 열 수 있음
- mobile/native/backend/infra fixture가 Playwright 부재만으로 오분류되지 않음

### P6. 평가 기반 자가개선

목표: 실패에서 개선 후보를 만들되 품질을 망치는 자동 승격을 막는다.

- [ ] structured incident
- [ ] cluster와 recurrence
- [ ] candidate generator
- [ ] baseline/candidate/holdout replay
- [ ] quality, token, latency comparison
- [ ] canary
- [ ] forge whet compatibility draft와 별도 coding-practice 소유권 유지
- [ ] promote와 rollback
- [ ] improvement PR template

완료 조건:

- 후보마다 재현 fixture 존재
- holdout regression 0
- 품질 향상 또는 명확한 비용 절감 근거 존재
- 사람 승인 전 canonical rule 변경 0
- rollback이 한 명령으로 가능

### P7. event-driven 운영

목표: core loop가 안정된 뒤 반복 prompt 입력을 줄인다.

모든 event adapter와 schedule은 명시적 opt-in이다. SessionStart나 기본 /start가 네트워크를 호출하거나 flow run을 자동 생성하지 않는다.

- [ ] GitHub issue/PR event adapter
- [ ] schedule
- [ ] Sentry/Grafana 같은 외부 event adapter interface
- [ ] Catch-up summary
- [ ] Draft PR update
- [ ] cross-run queue와 priority
- [ ] 비용·동시성 quota

완료 조건:

- event 중복 전달에도 run 하나만 생성
- 사람 결정 node에서만 알림
- catch-up이 마지막 확인 이후 변경만 요약
- 초기 버전에서 auto merge 0

### 병렬 호스트 어댑터 lane

이 lane은 autonomous loop가 호스트 지원을 과장하지 않게 하는 호환 작업이다. 세부 SSOT는 docs/codex-coexistence.md이며 여기서는 milestone 의존성만 둔다.

- Claude native: 현재 동작과 기존 fixture를 계속 회귀 기준으로 사용
- Claude → Codex bridge: 현재 부분 지원을 유지하고 stdin, mode-600 temp file, --ignore-user-config, 통제된 tool profile을 검증
- Codex native P1: 임시 디렉터리에 core skill과 scanner/builder/critic TOML을 만드는 dry-run compiler만 구현
- Codex native P2: fixture/eval 통과 뒤 사용자 승인으로 프로젝트 범위 .agents/skills, .codex/agents, hook adapter를 opt-in 생성
- P2 전에는 AGENTS.md를 읽는다는 이유만으로 native 지원 완료라고 문서화하지 않음
- model/effort resolver는 실제 선택을 관측하고 eval을 통과하기 전까지 advisory 상태 유지
- xhigh, max, ultra는 사용자 요청 또는 eval 근거 없이 자동 선택하지 않음

---

## 13. 첫 구현 단위

다음 작업은 큰 리팩터링이 아니라 아래 순서의 작은 change set으로 시작한다.

### CF-BASE-001 — 현재 Paperthin 참고 리팩터링 완결

대상: 현재 code-forge working tree

- 현재 diff를 baseline으로 두고 파일별 변경 목적을 thin spine, routing, Codex, state/concurrency, 잔재 제거로 분류
- 기존 hunk를 되돌리거나 처음부터 다시 쓰지 않고 새 계획과 충돌하는 표현·검증 누락만 최소 patch
- deleted legacy 문서와 자동 Flow 경로를 부활시키지 않음
- bin/forge lock, progress archive, status --json consumer 계약을 회귀 검증
- §17의 전체 검증을 실행하고 환경 경고와 코드 실패를 분리

완료 전에는 flow bridge나 /start façade의 새 runtime 동작을 추가하지 않는다.

### FT-001 — flow 사실 정리와 테스트 골격

대상: flow-toolkit

전제: flow-toolkit 저장소가 쓰기 가능한 workspace로 열려 있고 현재 clean HEAD가 유지됨.

- 실제 help와 문서 불일치 수정
- TODO 명령은 experimental 또는 unavailable로 명시
- package lint를 실제 구문·정적 검사로 교체
- CI 추가
- 현재 workflow start/resume 회귀 fixture 추가

### FT-002 — v2 run contract와 reducer

대상: flow-toolkit

- schema
- reducer
- revision
- event log
- atomic storage
- concurrency tests

### CF-001 — 단일 bridge와 shadow mode

대상: code-forge

- flow version 확인
- stdin 기반 한 개 JSON envelope와 version handshake
- raw 사용자 입력·로그의 shell argv 보간 금지
- /start의 직접 flow 명령 호출을 bridge로 수렴
- 기본 off
- 결과는 관찰만 하고 기존 실행을 제어하지 않음
- status --json additive golden test
- 기존 --flow와 FORGE_FLOW_AUTO 회귀 test

### FT-003 — plan-only Spec → TC

대상: flow-toolkit + fixture

- requirements
- AC
- traceability
- deterministic spec/TC/plan gate와 routing 조건부 critic packet
- final plan packet

### CF-002 — /start façade 분리

대상: code-forge

- 현재 634줄을 façade와 측정상 필요한 host delta reference로 의미 보존 추출
- routing, 상태, 테스트 canonical 표를 새 reference에 복제하지 않음
- /start default, --auto, --flow 의미 보존
- /start --autopilot --plan-only 연결
- docs-polish는 final Markdown projection에만 적용

이 여섯 change set이 통과하기 전에는 자동 구현·자동 repair·schedule을 시작하지 않는다. plugin-visible 릴리스는 별도 change set이며 사용자가 요청할 때만 CHANGELOG, plugin version, push/update, cache spot-check 절차를 수행한다.

---

## 14. 평가 계획

### 14-1. 대표 fixture

초기에는 20개 안팎을 권장한다.

- 문서·문구 3개
- 순수 로직 3개
- API contract 3개
- UI component 3개
- UI flow 4개
- schema/build 2개
- 의도적 요구사항 충돌 1개
- 의도적 stale evidence 1개

각 fixture에는 version, source, expected source disposition, expected AC, expected test class, expected gate result, 허용 경로, fault injection, replay command, environment/config hash를 둔다. expected 결과는 사람이 승인한 oracle manifest가 소유하며 baseline version을 고정한다. 일반 성공 fixture 외에 source 분할·삭제, mixed .policy, 동시 worktree 변경, lease late writer, test 약화, mock-only false PASS, mobile/non-browser UI를 포함한다.

### 14-2. 품질 지표

- required source coverage
- required AC coverage
- first-pass spec/TC/code gate rate
- escaped blocker 수
- human 최종 수정량
- false PASS와 false BLOCK
- earliest faulty phase accuracy
- crash resume 성공률
- stale evidence 검출률
- autonomous completion rate

### 14-3. 비용 지표

- completed required AC당 input token
- phase별 cached input ratio
- repeated read ratio
- critic decision-change rate
- retry당 token과 latency
- evidence storage 크기
- human interruption당 절약 시간

초기 release 기준은 “토큰이 줄었다”가 아니다.

- 필수 gate 성공률이 baseline보다 낮아지지 않을 것
- required·security·freshness negative fixture의 false PASS 0건
- concurrency·stale evidence 검출 fixture 성공률 100%
- false BLOCK은 baseline보다 증가하지 않거나 각 증가에 승인된 안전 근거가 있을 것
- median tokens/completed AC가 15% 이상 악화하면 품질 향상 근거가 있을 것
- 자동 완수율이 올라가도 사람 최종 수정량이 늘면 승격하지 않을 것
- holdout regression 0은 고정된 holdout manifest의 required oracle 판정이 하나도 악화되지 않았다는 뜻이며, 표본을 결과 확인 뒤 교체하지 않을 것

---

## 15. 위험과 대응

| 위험 | 대응 |
|---|---|
| controller 자체가 새 복잡성이 됨 | plan-only vertical slice와 pure reducer부터 시작 |
| prompt와 schema가 두 source로 갈라짐 | machine schema는 flow만 소유, code-forge는 profile만 소유 |
| 테스트를 많이 돌리면 품질이 오른다는 착각 | AC 기반 최소 충분 테스트와 비용 지표 |
| flaky E2E가 무한 repair를 유발 | failure signature, quarantine 정책, 3개 가설 상한 |
| screenshot에 개인정보 노출 | 로컬 기본, sensitivity scan, 공개 upload opt-in |
| self-improvement가 규칙을 오염 | baseline/candidate/holdout, canary, 사람 promote |
| 여러 host가 같은 run을 덮음 | revision, lease, heartbeat, idempotency |
| dirty worktree에서 같은 SHA를 오인 | worktree fingerprint와 lease hard gate |
| 테스트 후 새 commit을 승인 | tested SHA와 fingerprint freshness hard gate |
| agent 수가 폭증 | phase와 agent를 분리하고 기존 역할 우선 재사용 |
| code-forge 기본 UX가 깨짐 | 기존 /start와 --auto 보존, --autopilot opt-in |
| 현재 미커밋 작업을 덮거나 재작성 | 현재 diff를 baseline으로 고정하고 edit 직전 파일별 diff 재확인 |
| Codex read-only를 외부 무부수효과로 오인 | 통제 profile, stub, stdin bridge, 외부 capability 명시 |
| evidence와 source snapshot에 민감 정보 잔존 | mode 700/600, 분류, redacted derivative, 명시 retention |
| flow-toolkit을 너무 일찍 공개 | 문서 정직화·tests·CI·sanitization 뒤 remote 연결 |

---

## 16. 하지 않을 것

- code-forge와 flow-toolkit 소스 병합
- 새 orchestration 기능을 hooks에 구현
- 무제한 retry
- 모든 phase마다 새 subagent 생성
- HIGH라는 이유만으로 planner, architect, critic, team 자동 호출
- 기본 fan-out 2개 초과 또는 새 미해결 질문 없는 세 번째 lane
- LLM 다수결을 검증으로 취급
- 강제 토론 합의와 고정 round·100점 팀 평가
- 파일 확장자만 보고 specialist 고정 호출
- package manager, React, Toss 구조를 범용 기본값으로 가정
- eval 근거 없는 xhigh, max, ultra 자동 선택
- raw transcript를 canonical state로 저장
- raw 사용자 입력·오류 로그를 shell argv에 보간
- screenshot과 trace를 무조건 git에 커밋
- public evidence upload 기본 활성화
- 규칙 자동 영구 승격
- 초기부터 graph UI, 원격 runner, 50개 session 운영
- auto merge
- git add ., 자동 commit, push, PR
- 자동 네트워크 update와 기본 Flow 연동
- append-only 상태의 무잠금 GC·앞부분 삭제·재작성
- 상태 파일을 우회해 직접 읽거나 쓰는 외부 consumer
- @${CLAUDE_PLUGIN_ROOT}로 선택 상세 eager include
- build-guide, review-guide, coding-standards의 무조건 적재 복구
- 전역 skill 일괄 설치, symlink farm, 사용자 홈 자동 수정
- AGENTS.md 금지 표의 폐지 workflow와 현재 diff에서 삭제한 legacy instruction 문서 부활
- canonical 문서를 복사한 새 중복 가이드
- 기존 /start --auto 의미 변경
- flow가 준비되기 전 code-forge 기본 동작의 필수 의존성으로 전환

---

## 17. 전체 완료 조건

- [ ] code-forge 기본 경로는 flow 없이 계속 동작
- [ ] /start façade가 6 KiB 이하 또는 관측 1,500 tokens 이하
- [ ] flow v2 schema와 transition tests 통과
- [ ] concurrent run 유실 0
- [ ] crash 후 resume 가능
- [ ] current-worktree 동시 변경을 fingerprint로 탐지
- [ ] stable REQ/AC/TC ID와 traceability 존재
- [ ] spec, TC, plan, code 결정적 gate가 구조화 결과를 반환
- [ ] routing 조건을 만족한 경우만 fresh critic을 호출하고 실제 호출을 telemetry에 기록
- [ ] required source/AC/TC coverage 100%
- [ ] required SKIP 0
- [ ] blocking finding 0
- [ ] stale artifact/evidence 0
- [ ] tested SHA와 final SHA, tested fingerprint와 final fingerprint 일치
- [ ] provisioned browser UI evidence에 screenshot, trace, JSON, console/network digest 존재
- [ ] 같은 failure signature와 같은 가설·조치 반복 0
- [ ] 개선 후보가 baseline/candidate/holdout 평가를 통과
- [ ] canonical rule 승격은 사람 승인
- [ ] forge-glow는 bin/forge status --json만 소비
- [ ] Claude native 동작, Codex bridge 부분 지원, Codex native 설계/P1·P2 상태가 정확히 문서화
- [ ] route model/effort는 resolver 전까지 advisory로 남음
- [ ] 기존 /start default, --auto, --flow, FORGE_FLOW_AUTO 회귀 없음
- [ ] 대표 fixture에서 token·품질·latency baseline 비교 완료

### 17-1. code-forge 리팩터링 필수 검증

CF-BASE-001과 이후 code-forge change set은 최소 다음을 실행한다.

- [ ] `bash scripts/check-doc-integrity.sh`
- [ ] `bash scripts/check-route-concurrency.sh`
- [ ] `bash scripts/check-progress-archive.sh`
- [ ] `bash scripts/check-status-contract.sh`
- [ ] `shellcheck -S warning hooks/*.sh bin/* scripts/*.sh tools/*.sh`
- [ ] `bash -n hooks/*.sh bin/* scripts/*.sh tools/*.sh`
- [ ] `.claude-plugin/plugin.json`, `hooks/hooks.json`, `templates/policy/*.json` JSON parse
- [ ] 모든 `skills/*/SKILL.md`의 frontmatter name과 directory name 일치
- [ ] hooks/hooks.json의 command가 실제 파일을 가리킴
- [ ] 모든 `agents/*.md`에 model frontmatter 존재
- [ ] `git diff --check`

check-status-contract.sh는 status --json v1 필드의 additive compatibility, Flow 미설치 시 정상 조회, 외부 consumer가 내부 상태 파일을 직접 읽을 필요가 없음을 golden fixture로 검증한다.

shellcheck 같은 검증 도구 자체가 없으면 환경 prerequisite로 별도 보고하고, 나머지 검증을 계속한다. bin/forge doctor의 route stale, quality 기록 없음, /setup 미실행, Flow 미설치는 환경 상태일 수 있으므로 코드 검증 실패와 섞지 않는다.

### 17-2. 구현 완료 보고 계약

각 code-forge milestone의 최종 보고에는 다음을 빠뜨리지 않는다.

1. 기존 Paperthin 참고 대규모 리팩터링과 새 구조 개선을 파일·의미 단위로 어떻게 병합했는지
2. 삭제하거나 canonical 문서로 통합한 legacy 잔재와 의도적으로 보존한 사용자 변경
3. model class, effort, fan-out 정책의 실제 동작과 아직 telemetry/advisory인 부분
4. Claude native, Claude→Codex bridge, Codex native의 정확한 지원 수준
5. 실행한 검증 명령, PASS/FAIL/SKIP, 환경 prerequisite와 증거 경로
6. 범위·위험·근거 때문에 의도적으로 남긴 후속 작업

---

## 18. 구현 시작 규칙

이 문서를 기준으로 다음 작업을 시작할 때는 P0부터 진행한다.

1. 현재 code-forge의 대규모 미커밋 diff를 구현 baseline으로 사용한다.
2. CF-BASE-001에서 기존 Paperthin 참고 리팩터링을 검증하고 새 불변 조건과 의미적으로 합친다.
3. 파일을 편집하기 직전에 해당 파일의 diff를 다시 보고, 기존 hunk를 보존한 최소 patch만 적용한다.
4. commit이나 branch 생성을 기준점의 필수 조건으로 삼지 않는다. 이번 범위에서는 commit, push, PR, release를 하지 않는다.
5. flow-toolkit이 쓰기 가능한 workspace로 제공되면 clean HEAD를 다시 확인한 뒤 FT-001을 시작한다.
6. 각 change set 완료 후 이 문서의 checkbox와 실제 근거 경로를 갱신한다.
7. milestone을 건너뛰지 않는다.
8. runtime 변경, release, remote push는 각각 별도 검증과 사용자 권한을 따른다.

권장 기본 선택은 다음과 같다.

| 항목 | 기본값 |
|---|---|
| 저장소 | code-forge와 flow-toolkit 분리 |
| 첫 host | Claude native, 계약은 host-neutral |
| Codex | bridge 부분 지원 유지, native는 dry-run P1 → opt-in P2 |
| 실행 모드 | shadow → plan-only → opt-in autopilot |
| artifact 위치 | runtime은 ~/.flow, 공유 truth만 선택적 .policy |
| PR | 명시 허용 시 Draft |
| merge | 사람 |
| rule promotion | 사람 |
| docs polish | code-forge 내부, 사람용 Markdown에만 |

---

## 19. 참고 근거

내부:

- [설계 원칙](../docs/design-principles.md)
- [Claude–Codex 공존 설계](../docs/codex-coexistence.md)
- [통합 계약](../docs/contracts/INTEGRATION.md)
- [상태 계약](../docs/contracts/state-schema.md)
- [이벤트 계약](../docs/contracts/event-schema.md)
- [라우팅 정책](../references/routing-policy.md)
- [E2E 설계 계약](../docs/e2e-forge-loop-design.md)
- [테스트 아키텍처](../docs/testing-architecture.md)
- [현재 /start](../skills/start/SKILL.md)
- [현재 /e2e](../skills/e2e/SKILL.md)
- 당시 로컬 개발 문서 윤문 가이드: `skills/docs-polish/references/developer-writing.md`. 별도 미추적 WIP이므로 이번 계획 문서 커밋에는 포함하지 않으며, 배포된 참조로 취급하지 않는다.

외부:

- [im-not-ai](https://github.com/epoko77-ai/im-not-ai)
- [I Made Codex Desktop QA My Pull Requests Every Hour](https://theaiplatform.app/blog/automating-pull-request-qa-with-codex-desktop/)
- [Labor0를 만든 이유](https://kdy1.dev/2026-8-22-labor0)

---

## 20. 문서 변경 기록

| 날짜 | 변경 |
|---|---|
| 2026-08-31 | 현재 Paperthin 참고 diff를 baseline으로 통합하고 thin spine, routing SSOT, Codex 지원 수준, 상태 잠금, worktree fingerprint, migration, 검증 행렬을 2차 반영 |
| 2026-08-31 | 현재 code-forge·flow-toolkit 감사, 외부 사례 비판 검토, 저장소 경계·상태·evidence·context·자가개선·단계별 구현 계획 확정 |
