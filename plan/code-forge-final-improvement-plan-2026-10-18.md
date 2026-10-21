# CodeForge 멀티모델 전환과 검증 플랫폼 최종 개선 계획안

작성일: 2026-10-18. 최종 개정: 2026-10-21. 10월 18일 통합본의 Codex·Claude 검수는 역사적 기록이다. 이번 완전관리형 제품·개인화·보안 요구사항 개정은 Codex가 반영했으며 Claude 재검수는 수행하지 않았다. 문서 반영은 제품 구현·보안 인증·배포 완료를 뜻하지 않는다.

[2026-10-21 서비스 상세 계획](../docs/agentops/13.hosted-personalized-service-plan.md)은 이 문서의 제품·보안·학습·사업 요구사항을 구체화한다. [시각화 HTML](../docs/agentops/codeforge-service-design-review-2026-10-21.html)은 검토용 설명 자료다. 실행 순서와 완료 조건은 이 문서를 따른다.

이 문서를 **통합 실행 순서의 단일 기준**으로 사용한다. `docs/agentops/09·11·11b·12`는 제품 목적과 세부 요구사항, 8·9월 계획은 이력으로 보존한다. 단계·지원 범위·기술 선택이 다르면 이 문서의 단계표와 결정 상태를 따른다. [통합 검수 기록](../docs/agentops/evidence/2026-10-18-integrated-plan-review.md)에 변경 근거와 남은 검증을 기록한다.

## 만들려는 제품과 기존 시스템

사용자는 저장소와 개선 목표를 맡기고, CodeForge는 기준 상태 측정 → 작은 변경 후보 → 독립 재검증 → 검토·승인 → 실제 반영 확인을 이어 준다. 기능과 안전성을 유지한 채 코드의 결함·병목과 에이전트 비용을 줄인다. 질문이 생긴 작업만 기다리고 다른 독립 작업은 계속한다.

현재 CodeForge의 규칙·스킬·Smith는 저장소에 맞는 작업 환경을 구성한다. Claude·Codex는 분석·코딩 실행기, Herdr는 터미널 제어, Glow는 세션 표시, Hermes는 선택형 예약·전송 기능을 제공한다. 새 core는 이 기능들을 연결하면서 작업 기준·검증 결과·승인·복구 기록을 유지한다. 기존 도구를 재사용하는 범위와 새로 구현하는 책임은 §2의 표를 따른다.

기존 `code-forge`는 독립적으로 유용한 무료 OSS로 유지한다. 이를 사용하는 완전관리형 개인화 제품은 별도 제품 저장소를 권고하되, G0b에서 pack 소비·설치 분리 실험 후 확정한다. 새 core 저장소를 먼저 만드는 것은 선행 조건이 아니다. Atelier는 제품 이름 후보이며 이름 변경·상표 확인·새 저장소 생성은 아직 하지 않았다. 제품은 승인된 개인 지식과 판단 기준을 필요한 만큼 사용하고, 코드 개선 결과를 독립 검증한다. 같은 Work의 실행 원장은 하나만 둔다.

멀티모델은 기존 계획에 이미 포함돼 있었다. 다만 현재 로컬은 Claude 중심 구현과 Codex 부분 지원 상태이며, 공통 정책을 썼다는 사실만으로 네이티브 지원이나 자동 라우팅이 완성된 것은 아니다. **기존 제품의 두 native pack과 새 코어의 두 runtime을 각각 출시 조건으로 둔다.** G2의 단일 runtime 실증은 내부 alpha이며, Claude/Codex 양쪽을 통과한 G3에서 멀티모델 제품 지원을 선언한다. GLM·Qwen 등은 같은 계약을 통과한 작업 유형부터 확장한다.

사용자처럼 판단하도록 돕는 Blueprint와 개인 프로필을 보존한다. 새 코어는 장기 실행·독립 검증·질문·승인·복구를 책임지고, 작은 작업은 호스트의 직접 실행을 유지한다. 원장·Inbox를 포함한 10월 제품 목적은 유지하되 모든 작업에 같은 절차를 강제하지 않는다.

## 1. 찾아낸 계획과 현재 증거

| 자료 | 확인한 내용 | 이번 계획에서의 지위 |
|---|---|---|
| [로컬 멀티런타임 설계](../docs/codex-coexistence.md) | Claude native, Claude→Codex bridge, Codex native를 구분. 공통 소스에서 skills·agents·hooks 생성, dry-run→opt-in 설치→배포 계획 | 기존 저장소의 멀티호스트 구현 요구사항으로 유지 |
| [로컬 라우팅 정책](../references/routing-policy.md) | FAST/BALANCED/DEEP와 effort·fan-out 분리. 실제 resolver 구현 전에는 advisory | 공통 정책 원본으로 유지. 실행 시점 강제와 기록은 새 코어가 담당 |
| [8월 자율 개발 계획](autonomous-development-loop-plan.md) | 2026-08-31. 기존 구조 유지, flow-toolkit에 opt-in 실행 상태·증거·재시도 위임 | 역사 자료로 보존. 검증·무효화 요구와 opt-in 원칙을 계승하고, 필수 실행 엔진은 새 코어로 대체 제안 |
| [9월 리팩토링 정본](https://github.com/ggombee/code-forge/blob/3c856754f1d01d1b8cfe0557465b1ac906e81df8/docs/code-forge-refactoring-plan.md) | 9월 22일 결정 진행. 구현 저장소는 code-forge. 안전성·상태 수리·적재·프롬프트 평가 중심. Codex 전용 플러그인과 별도 엔진은 당시 범위 제외 | 안전성 수리와 평가 방법을 계승. 당시 범위 제외를 장기 금지로 해석하지 않음 |
| [10월 AgentOps 문서 지도](https://github.com/ggombee/code-forge/blob/e05552cd35939dc7e5d50709dd0963c8c2abfe3e/docs/agentops/README.md) | 10월 16일 최신 커밋. 새 host-neutral core 모노레포, 기존 CodeForge의 adapter·policy pack 전환 명시 | 제품 목적과 저장소 분리 방향의 기준 |
| [10월 제품·기술 설계](https://github.com/ggombee/code-forge/blob/e05552cd35939dc7e5d50709dd0963c8c2abfe3e/docs/agentops/11.codeforge-public-service-architecture-debate.md) | 측정→최소 변경→독립 검증→승인→반영. Claude/Codex·저비용 모델, capability·realm·예산 설계 | 새 코어의 상위 요구사항 |
| [10월 무인 실행 설계](../docs/agentops/12.night-runner-reference-audit-and-design.md) | durable 원장, 재시작, 질문 분리, 준비와 실제 반영 분리 | 공개 가능한 합성 사례로 검증할 상태·권한·복구 수용 조건 |
| 저장소 밖 `workspace/plan/code-forge-final-upgrade-plan.md`, `code-forge-harness-upgrade-plan.md` | 2026-03-27의 하네스 강화·AGENTS 도입 계획 | 역사 자료. 당시 점수·개수·지원 정보는 현재 사실로 재사용하지 않음 |

초기 조사 checkout의 `main` HEAD는 `1779c8a`였다. 당시 미커밋 코드·훅·스킬은 문서 커밋에 포함되지 않았다. 이번 통합은 원격 `docs/agentops-platform-plan`의 `e05552cd`와 원격 `main`의 `e9b9c1f`를 계획 브랜치에서 합친 `243eb1a`를 검수 기준으로 삼는다. 원본 작업트리의 미커밋 파일은 별도로 보존하며, 문서 통합을 구현 baseline 보존으로 계산하지 않는다.

9월 문서의 런타임 검사 23건·상태 검사 9건은 초기 조사 checkout의 결과가 아니었다. 이번에는 원본 작업트리의 미추적 `lib/`·`tests/`를 확인하고 두 검사를 다시 실행해 각각 23건·9건 통과를 확인했다. 이 코드는 계획 브랜치에 들어 있지 않으며 실호스트·CI·설치본 검증도 남아 있다. 계획 브랜치의 `hooks/quality-gate.sh`는 macOS Bash 3.2 구문 검사에서 실패했다. G0a에서 복원 리허설을 거쳐 재사용하고, G1a의 완료 여부는 통합된 코드로 다시 판정한다.

추가 검수 범위는 `forge-glow`, `forge-hearth`, `flow-toolkit`, `anvil-voice`, `coding-practice`, marketplace의 연결 계약이다. 초기 조사에서 기록한 설치·remote 상태는 해당 checkout의 snapshot이다. 이번에 확인한 Glow는 커밋된 `0.8.0`과 미커밋 `0.9.0`이 다르며, 후자는 세션별 표시를 유지하면서 `hud/lib/parse-forge.sh`를 제거하는 중이다. 따라서 기존 v1 consumer가 현재 존재한다고 가정하지 않는다. G0a에서 접근 가능한 source·설치본·remote를 구분해 기록하고, 없는 저장소는 `unavailable`로 남긴다. 공개 문서에는 실제 사용자 경로·계정·비공개 자료를 복사하지 않는다.

10월 원안의 Go daemon·CLI + TypeScript PWA 결정과 이번 TypeScript 단일 구현 후보는 서로 다르다. 언어 선택은 유지보수 비용·설치·signal/cancel·SQLite 동시성·복구 실험으로 재결정하고 ADR에 대체 이유를 남긴다. 지식 검색과 고급 언어 최적화는 뒤로 미루되, 원안이 요구한 실제 context·출처·언어·revision 기록은 첫 실행부터 유지한다.

## 2. 저장소를 나누는 이유와 소유권

| 선택 | 이점 | 비용과 판단 |
|---|---|---|
| 기존 저장소의 분리된 패키지에서 실증 | 한 저장소에서 개발·리뷰 가능 | 설치물·배포·의존성을 분리할 수 있는지 G0b에서 검증. 실험 단계의 유효한 선택 |
| 기존 제품을 폐기하고 새 저장소로 전부 이동 | 새 구조에 일괄 정리 | 사용자 설정·배포·미커밋 개선 이관 부담이 큼. 제외 |
| 기존 제품 개선과 새 코어 분리 | 기존 사용자 호환성을 유지하며 중립 실행 플랫폼 구축 | 버전 협상·통합 검증 필요. **권고안** |

CodeForge는 기존 OSS의 이름으로 유지하고, 새 관리형 제품의 이름과 저장소 경계는 별도 결정한다. 아래의 `core`는 논리적 실행 책임이며 반드시 독립 저장소나 마이크로서비스를 뜻하지 않는다. Claude/Codex별로 원본 저장소를 나누지 않는다. 기존 제품은 가입·유료 서버 없이 독립 사용 가능해야 한다. 새 제품은 Claude 플러그인 설치 없이 versioned pack artifact·저장소 profile·runtime adapter로 실행한다. pack은 설치 때 pin하며 세션 시작에 원본 저장소를 자동 갱신하지 않는다.

| 대상 | 책임 | 갖지 않는 책임 |
|---|---|---|
| 기존 `code-forge` | rules·references·skills·Smith 원본, 호스트별 pack compiler, 설치·제거·진단, 기존 CLI 호환 | 전역 Work 원장, 별도 무인 scheduler, 독립 승인 DB |
| 새 `code-forge-core` 가칭 | Work 계약, 원장, 실행 권한 집행, canonical Work Compiler API, runtime adapter, 독립 verifier, Decision/Approval Inbox, apply/readback | 기존 스킬 전체 복제, 자체 모델 서버·IDE·PTY·agent loop 재구현 |
| `flow-toolkit` | legacy 상태 보존·read-only importer 후보, 비즈니스 policy/spec/TC capability 평가 | 새 코어와 같은 Work를 별도 기록·재시도·최종 판정 |
| `forge-glow` | session/live HUD, versioned 상태 조회와 표시 | Work 완료 판정·승인·원장 수정 |
| `forge-hearth` | 휴면 상태 보존. 재채택 시 다중 source의 Markdown 보고서 생성 | Work·Decision·Approval 기록과 실제 반영 |
| Herdr | 선택형 터미널·pane·workspace·interactive agent 제어 adapter | Work 완료 판정·core 승인 대체 |
| Voice / `anvil-voice` | 기존 STT·단축키·입력 경로 보존, provider adapter와 접근 가능한 질문·응답 | 자연어 응답만으로 승인 scope 확대 |
| Whetstone / `coding-practice` | 개인 연습·사람이 승인한 프로필 원본 | 개인 연습 데이터의 공개 pack 번들·자동 규칙 승격 |
| `forge-market` | catalog 원본, host별 marketplace manifest·호환 BOM 생성 | runtime scheduler·Work 원장 |

새 코어의 초기 모듈은 `contracts`, `ledger`, `policy`, `verification`, `runtime-adapters`, `execution`, `cli`, `inbox`, `conformance`다. 이는 책임 분리이며 처음부터 개별 서비스나 별도 패키지를 뜻하지 않는다. 로컬 원장은 SQLite WAL을 기준으로 검증하고, 언어·DB 드라이버·배포 방식은 G0b 실험 뒤 확정한다. 기존 shell을 일괄 재작성하거나 범용 workflow DSL을 만들지 않는다.

### 메타포와 실행 책임

| 개념 | 보존할 의미와 경계 |
|---|---|
| Forge | 전체 작업·학습 환경. 저장소 수와 동일시하지 않음 |
| Blueprint | 사고 원칙과 정책 원문. 개인 판단 방식을 기계적 금지 목록으로 바꾸지 않음 |
| Smith | STATE+ACT 모델링과 정적 agent 컴파일. 프로젝트 컨벤션인 modules와 구분하고 runtime router 역할은 맡기지 않음 |
| Anvil | `/start`, CLI, Inbox client, Voice 등 사람과의 접점. 같은 Work Compiler API를 사용 |
| Assayer | AC/BDD/테스트 작성자. 자신이 작성한 테스트의 통과 선언만으로 최종 verdict를 만들지 않음 |
| Bellows | 관찰·성찰용 이벤트. core ledger의 권위 상태 전이와 구분 |
| Whetstone | 사람의 연습과 점진적 힌트 제거. 반복 패턴의 규칙 후보와 사람 학습을 같은 기능으로 취급하지 않음 |

Assayer가 제안한 테스트와 `RepositoryProfile`이 고정한 recipe를 구분한다. 독립 verifier는 후보와 분리된 실행 환경에서 고정 recipe·fixture·threshold로 검증한다. 기존 `forge whet` 이름은 호환 명령으로 유지하고, 채택 전 후보라는 상태를 보존한다. Fading은 Whetstone의 사람 학습 원칙으로 유지하며, 별도로 task eval을 통해 작업 지침·개입을 줄인다.

### 판단 원칙·권한·최종 판정

| 규칙 종류 | 예시 | 집행 주체 |
|---|---|---|
| `advisory` | 기존 코드 관찰, 가설·트레이드오프 판단 | host pack이 전달하고 agent가 판단 |
| `preference` | 개인 추상화·설명·표현 선호 | 승인된 profile의 관련 절만 선택 적재 |
| `invariant` | 허용 경로·계정·realm·실행 예산 | 검사 가능한 항목을 core/host가 강제 |
| `approval_boundary` | push·공개·merge·배포 등 지정 action | 정확한 action의 유효 승인과 host permission을 모두 확인 |

개인 preference는 조직·저장소의 강제 정책을 우회하지 못한다. 현재 작업 지시와 정책이 충돌하면 임의로 한쪽을 무시하지 않고 충돌 원문과 해소 조건을 제시한다. 근거가 있는 가역적 선택은 profile로 판단하고, 결과·권한을 바꾸는 미해결 선택만 질문한다.

standalone 작업은 host-native 검증 계약을 따르고, managed Work의 최종 판정은 core만 내린다. managed 실행 중 native hook 결과는 Evidence이며 별도 최종 PASS가 아니다. host의 도구 승인과 core의 action 승인은 서로 대체하지 않는다. 취소·승인 철회·만료가 관측되면 신규 action을 중지하고 진행 중 action의 결과를 readback으로 조정한다. 호환성 오류는 해당 연결만 차단하고, 무관한 native 작업은 계속 사용할 수 있어야 한다.

### 한 원본과 한 원장의 원칙

- 규칙·스킬 원본은 기존 저장소에 둔다. 배포 pack에 버전·source revision·digest를 넣고 코어가 해당 버전을 pin한다. 코어에 수정 가능한 사본을 두지 않는다.
- `forge-status/v1`과 기존 관찰 계약은 당분간 기존 저장소가 소유한다. Work·Attempt·Approval·Evidence·Receipt와 core read model은 새 코어가 소유한다. legacy Hearth `sources v2`는 별도 계약으로 동결한다. 각 adapter는 지원 protocol·pack 범위를 선언하고 unknown field와 미지원 major를 구분한다.
- 기존 단독 사용 상태는 기존 `bin/forge` 호환 범위에서 유지한다. 코어 관리 Work는 코어만 쓴다. 같은 Work에 두 scheduler나 두 writer를 두지 않는다.
- `.claude/state`를 즉시 옮기지 않는다. 기존 소비자는 `bin/forge status --json`을 유지하고, 코어 관리 Work는 별도 ID와 versioned 조회 결과로 구분한다. 경로 이관은 consumer 호환 검증 후 별도 작업이다.
- 새 CLI의 실제 이름은 G0b에서 정해 기존 `forge`와의 충돌을 피한다. 내부 파일 경로를 저장소 간 API로 사용하지 않는다.
- core ledger는 managed 실행 사실의 정본이다. 프로젝트의 `progress.md`, ADR, Jira/GitHub와 개인 프로필은 각 소유자가 선언한 위치를 정본으로 유지하고 core에는 pointer·revision·receipt만 둔다. DecisionReceipt를 프로젝트 설계 결정으로 자동 승격하지 않는다.
- 공개 상태 API는 접근 규격을 뜻하며 인터넷 공개를 뜻하지 않는다. realm별 조회 권한·삭제·보존 기간을 정의한다. Glow/Hearth는 허용된 projection만 읽고 서로 다른 realm의 원문을 기본으로 합치지 않는다.

## 3. 멀티모델 지원의 정확한 범위

서로 다른 세 가지를 별도로 검증한다. **멀티호스트**는 Claude Code와 Codex가 같은 규칙·스킬을 각자 발견하고 실행하는 것이다. **멀티런타임**은 코어가 실행기별 session·event·취소·권한을 연결하는 것이다. **멀티모델**은 허용된 runtime/provider 안에서 작업에 맞는 모델을 선택하고 실제 선택·비용·결과를 남기는 것이다.

| 경로 | 조사 시점 상태 | 목표와 출시 기준 |
|---|---|---|
| 기존 Claude plugin | 로컬 구현 존재. 이번 조사에서 실호스트 재검증하지 않음 | 기존 동작·설치·제거 회귀 검사 |
| Claude→Codex bridge | 로컬 wrapper·문서 존재 | 교차 검토 경로 유지. Codex native 완료 근거로 사용하지 않음 |
| Codex native pack | 로컬 계획 존재, compiler·설치 완료 증거 없음 | dry-run 생성, 선택 설치, 실제 discovery·권한·제거 검증 |
| 코어→Codex runtime | 새 코어 미구현 | 최초 연결 후보. 구조화 이벤트·취소·결과 회수 conformance |
| 코어→Claude runtime | 새 코어 미구현 | 초기 제품의 두 번째 필수 runtime. 같은 Work/검증 계약 통과 |
| GLM·Qwen·로컬 endpoint | 10월 설계 후보 | provider·runtime·작업 유형별 eval 후 opt-in. 첫 출시 필수 아님 |

Codex 공식 문서는 app-server가 thread·turn·event·approval을 제공하며, `exec`와 SDK는 다른 통합 수준임을 설명한다. 따라서 제품의 session 제어에는 app-server를 우선 실증하고, 단발 CLI를 같은 capability로 취급하지 않는다. [공식 OpenAI 설명](https://developers.openai.com/blog/codex-as-a-platform).

로컬에서 확인한 것은 `codex-cli 0.163.0` 설치뿐이다. 실제 요청·계정 접근·취소·재개 검사는 수행하지 않았다. Claude API와 다른 provider의 최신 사양·계정 조건 역시 이번 문서에서 지원 완료로 선언하지 않는다. P0에서 설치 버전과 공식 문서 기준으로 능력표를 만들고 인증된 실험 결과를 붙인다. 기존 계획의 `.codex/agents`·hooks 경로도 목표 출력 후보이며 설치 버전의 schema를 확인한 뒤 확정한다.

### native와 managed 진입

- `native`: 호스트가 직접 실행·검증하고 필요한 Blueprint·skills를 선택한다. 명확하고 가역적인 작은 작업의 기본 경로다.
- `managed`: 장기·다중 작업이나 독립 검증·복구가 필요한 목표를 명시적으로 core에 접수한다. Work 원장·Inbox·apply/readback을 사용한다.

core 설치만으로 모든 `/start`를 managed로 바꾸지 않는다. native→managed 전환은 scope·budget·Work ID를 고정하고, managed 실행의 장애·결과 불명 상태에서는 native로 자동 재실행하지 않는다. 같은 action의 중복을 조정한 뒤에만 새 Attempt를 연다.

### 호스트 pack과 실제 권한

공용 skill 본문은 재사용하고 host 전용 도구·trigger·경로만 변환한다. Codex portable plugin은 루트 `skills/`를 지원하므로 `.agents/skills` 복제를 유일한 설치 방식으로 고정하지 않는다. lifecycle hooks가 포함된 pack은 신뢰 검토와 수동 desktop 설치가 필요한 경로로 구분한다. hook 없는 공개 pack과 로컬 자동화 pack의 배포 조건을 각각 검증한다. [공식 plugin 패키징](https://developers.openai.com/plugins/build/plugins)

Codex custom agent는 부모의 sandbox·approval·provider 설정을 상속한다. `.codex/agents/*.toml`만으로 별도 read-only sandbox를 만들 수 있다고 가정하지 않는다. 강한 권한 격리가 필요한 critic은 제한된 부모 session 또는 별도 프로세스에서 검증하고 MCP·API·plugin·hook의 부수효과도 함께 통제한다. [공식 Subagents 문서](https://learn.chatgpt.com/docs/agent-configuration/subagents)

compiler의 최소 descriptor는 stable component ID·기존 alias·trigger/negative trigger·필수 reference·capability·source digest·생성 파일 소유권을 담는다. 호스트 간 parity는 파일 내용의 일치보다 핵심 제약·발견·권한·행동의 일치로 판정한다. 공식 문서 확인은 로컬 설치본의 conformance 통과를 대신하지 않는다.

### 공통 runtime 계약

`RuntimeAdapter`는 protocol version과 함께 invocation, events, start/cancel/resume, permission, identity, artifacts, recovery, usage의 능력·한계를 각각 보고한다. `unsupported`, `unknown`, `verified`를 구분한다. 실행 필수 능력이 없으면 그 작업을 배정하지 않는다.

`Attempt`에는 runtime ID·버전, provider·model의 요청값과 관측값, account alias, realm, capability digest, policy/pack digest, effort 요청값과 실제값, 시간·사용량·비용을 남긴다. 관측할 수 없는 값은 `unknown`이며 0원·성공으로 채우지 않는다. 자격증명 원문은 기록하지 않는다.

모델 라우팅 순서는 realm·데이터 허용 범위 → 필요한 capability → 위험·검증 가능성 → 작업별 품질 근거 → 비용·quota다. FAST/BALANCED/DEEP를 실제 모델 ID로 바꾸는 설정은 adapter에 두고 공통 정책에는 넣지 않는다. 미지원 effort를 조용히 무시하지 않는다. 강제할 수 없는 값은 advisory로 표시한다.

실패 시 다른 provider로 넘기는 것은 새 Attempt다. 허용 계정·데이터 정책·예산을 다시 검사하고 기존 부분 결과를 격리한다. fallback도 허용된 realm·endpoint를 유지하며 외부 작업을 중복 실행하지 않아야 한다. 초기 자동 routing은 정적 규칙으로 시작한다.

다른 모델의 리뷰는 유용한 추가 관점이지만 테스트·정적 분석·readback을 대체하지 않는다. 모델 다수결이나 실행기의 자기 평가로 완료를 판정하지 않는다. OpenAI 호환 API를 받는다는 사실만으로 tool 사용·장기 복구·권한 처리까지 호환된다고 보지 않는다.

## 4. 기존 CodeForge에서 먼저 개선할 것

1. **복구 가능한 재기준화.** tracked diff의 binary patch 또는 private WIP snapshot과 미추적 파일의 실제 내용을 백업한다. digest는 복원 자료의 무결성 확인에 사용한다. 임시 checkout에서 복원하고 원본과 비교한 뒤 구현 worktree를 분기한다. 설치 cache·source·remote 기준선을 따로 기록한다.
2. **실행 안전성.** quality gate가 미실행·설정 오류·검사 실패를 PASS로 만들지 않는지 재현한다. cleanup의 경로 범위, 상태 동시 쓰기, Bellows 실제 payload·미확인 필드, handoff의 HEAD·dirty 재확인을 수리한다. 9월 지적을 현재 결함으로 단정하지 않고 fixture로 판별한다.
3. **공통 pack compiler.** 선택된 기본 workflow만 임시 디렉터리에 생성한다. 공용 본문과 logical reference를 재사용하고 host 문법·manifest·tool mapping만 변환한다. 생성물에 cache 버전 절대경로를 넣지 않는다. source·의존성·compiler hash로 Smith 출력의 신선도를 검사하고 기존 Must/Never·권한 의도가 보존되는지 비교한다.
4. **선택 설치와 제거.** 생성 파일 manifest, 충돌 preview, 사용자 파일 병합·보존, 재실행 idempotency, uninstall을 구현한다. 사용자 홈이나 기존 설정을 기본값으로 덮어쓰지 않는다.
5. **호스트 검증.** Claude/Codex의 실제 instruction discovery, positive/negative trigger, 권한 제한, hook capability와 설치·제거를 확인한다. fixture 통과와 실제 호스트 통과를 별도로 기록한다.
6. **코어 연결.** `/start`와 새 CLI는 같은 Work Compiler 계약을 사용한다. managed Work의 재시도·원장·최종 판정은 core에 위임한다. 작은 native 작업과 core 미설치 상태도 회귀 검사한다. 기존 agent·명령 alias와 `status --json` v1 reader는 최소 두 릴리스 유지하고, 의미상 parity와 실제 복구를 확인한 뒤 폐기한다.
7. **기존 사용자 회귀.** `/start`, `/test`, `/handoff`, `/voice`의 입력·출력·승인 의미, Smith 프로젝트 정책, Glow golden, Voice hotkey·symlink·Hammerspoon 경로를 기록한다. agent 대량 삭제로 경량화를 시작하지 않고 hook 지연·false-pass·중복 절차부터 평가한다. 기존 Herdr·Orca 등 사용자 hook을 설치·제거 과정에서 보존한다.

`agents/`는 직접 편집하되 프로젝트 Smith 출력 `.claude/agents/`는 수정하지 않는다. 기존 `rules/` 삭제와 `presets/` schema 변경은 이 계획 범위에 넣지 않는다.

## 5. 새 코어의 첫 완성 범위

첫 내부 실증은 공개 코드 저장소 하나에서 다음 흐름을 끝까지 수행한다. 첫 고객용 alpha는 GH의 완전관리형 환경에서 제공하며 로컬 설치를 가입 조건으로 삼지 않는다.

```text
개선 목표와 저장소 선택
 → WorkSpec·PolicySnapshot·RepositoryProfile 고정
 → baseline 측정과 격리 Attempt
 → 최소 변경 후보
 → 독립 검증과 CandidatePackage
 → 질문·검토·승인함
 → 승인된 action의 apply와 readback
 → Receipt와 개선 보고서
```

다른 허용 작업 유형도 데이터 계약에서 배제하지 않는다. 다만 DB·인프라·결제·외부 메시지의 실제 실행을 첫 코드 수직 단면의 완료 조건에 섞지 않는다. 해당 실행기는 별도 profile·권한·검증이 있을 때 추가한다. 이는 10월 무인 계획의 전체 범위를 유지하면서 첫 출시 검증 범위를 좁힌 제안이다.

### 계약과 상태

G0b에서 `WorkSpec`, `PolicySnapshot`, `RepositoryProfile`, `VerificationRecipe`, `Attempt`, `CheckResult`, `Evidence`, `Receipt`의 최소 fixture를 먼저 연결한다. `CandidatePackage`, `DecisionRequest/Receipt`, `ApprovalGrant`, `ActionRequest`, `ApplicationReceipt`, `RunPolicy`, `ContextEnvelope`는 같은 v0 계약의 해당 흐름에서 검증한다. v0를 범용 SDK의 영구 schema로 고정하지 않는다. RunPolicy는 시도·retry·시간 상한, PolicySnapshot은 해석된 집행 항목·원문 참조·digest를 맡는다.

상태는 Work, Attempt, 검사 결과, 외부 Action을 분리한다. `QUEUE_DRAINED`나 provider의 turn 완료는 Work 검증 완료가 아니다. action의 `PREPARE → PROPOSE → APPLY → POST_APPLY_VERIFY`와 Attempt 내부 GAVA의 코드 작성 `APPLY`는 namespace로 구분한다. 각 전이에 필요한 증거와 실패·취소 경로를 표로 정의한다. 질문이 필요한 노드만 `WAITING_DECISION`으로 두고 독립 노드는 계속 진행한다. 버전이 달라진 질문의 답은 자동 적용하지 않는다.

로컬 실증은 SQLite WAL을 후보로 사용하고 관리형 저장소는 tenant 격리·동시성·백업 실험 뒤 결정한다. migration, transaction outbox, lease·heartbeat·recovery를 구현한다. 네트워크를 포함한 exactly-once를 가정하지 않는다. 외부 action 결과가 불명확하면 idempotency key 또는 readback으로 조정하기 전 재시도하지 않는다. 만료된 worker가 새 worker 결과를 덮어쓰지 못하도록 attempt/lease 세대를 검사한다.

첫 결합 시험은 사람이 검토한 WorkSpec 파일을 core CLI에 넣고 runtime 하나·폐기 가능한 worktree 하나·고정 검증·CLI 승인·로컬 반영·readback을 연결한다. 로컬 반영 대상도 별도 폐기 가능한 브랜치로 제한한다. 이후 같은 G2에서 durable 복구·질문·반응형 Inbox·별도 apply executor와 단일 장비의 OS wake/restart를 완성한다. `/start`의 managed 연결은 G2 후반, 두 호스트의 parity는 G3에서 검증한다. `exec` 기반 단발 실험은 해당 capability만 입증하며 structured session·cancel·resume 통과를 대신하지 않는다.

G0b의 합성 Git fixture는 공개 가능한 소스만 사용하며 다음 입력과 기대 결과를 먼저 고정한다. 모델이 만든 검사를 정답으로 삼지 않는다.

| 사례 | 기대 결과와 판정 기준 |
|---|---|
| 설정 오류·도구 부재를 성공으로 처리하는 결함 수정 | 실패 상태를 정확히 구분하고 정상 입력도 통과. 심어 둔 false PASS 사례 수 2 → 0을 고정 oracle로 확인 |
| 테스트·fixture·threshold·CI 약화 후보 | 검사 실행이 성공해도 `REVIEW_REQUIRED` |
| 필수 검사 미실행·실행 오류 | 원인을 보존하고 `VERIFIED_CANDIDATE` 생성 금지 |
| 승인 뒤 base·artifact·policy 변경 | stale 승인 거부, 반영 0회 |
| 반영 직후 응답 유실·재시작 | 결과 확인 전 재실행 금지, 조정 후 실제 effect 1회 |
| 질문 대기와 다른 Work, 잘못된 realm의 응답 | 의존 Work만 대기, 독립 Work 진행, 다른 realm 응답 거부 |

이 fixture는 판정기의 정확성을 검증한다. G2는 별도의 공개 저장소 profile에서도 결함 또는 병목 개선 한 건을 재현하고 correctness·보조 지표 비퇴행을 입증해야 한다. 최초 실제 profile 후보는 안전성 검사를 가진 CodeForge 고정본이며 G0b에서 명령·환경·기준 SHA를 확정한다. 처리 속도·token·비용의 개선 주장은 해당 비교 자료가 있을 때만 한다.

### 실제 context와 개인 판단 기준

`ContextEnvelope`는 실제 전달한 규칙 절·skill·profile·지식 source의 ID, URI/revision/digest, 우선순위, locale, realm을 기록한다. pack digest만으로 실제 적재를 입증하지 않는다. `LanguageProfile`을 평가하지 않았으면 원문 언어를 유지하고, 모델·작업별 언어 평가와 지식 검색 UI는 P4에서 확장한다.

개인 프로필은 Whetstone의 승인된 원본과 프로젝트 overlay를 연결하되 원문 전체를 공개 core에 번들하지 않는다. 프로젝트의 강제 정책을 우선하고, 허용된 개인 선호와 기본 Blueprint를 그 아래 적용한다. 반복 관찰→후보→사람 승인→profile 개정 흐름을 보존한다. 근거 없는 전체 profile 상시 주입이나 자동 규칙 승격은 하지 않는다.

G0b fixture에는 realm별 경로·최소 파일 권한과 원문·credential 미수집 기본값을 둔다. 실제 DB·artifact의 redaction, retention/GC, export/delete와 백업 정책은 G2의 첫 managed 결합 시험 전에 확정한다. 첫 실행부터 출처를 기록한다.

### 독립 검증과 최적화

검사 결과는 `pass`, `fail`, `measured`, `error`, `not_run`, `unavailable`, `blocked`, `n_a`를 보존한다. 필수 검사가 실행되지 않았으면 검증 완료가 아니다. 검증 명령은 저장소 profile이 제공하고, 모델이 같은 변경에서 test·threshold·fixture·CI를 약화했으면 자동 통과시키지 않는다.

baseline과 candidate는 같은 환경·fixture·도구 버전에서 비교한다. 기능 비퇴행을 전제로 주 지표 개선과 보조 지표 비퇴행을 확인한다. 임계값·반복 횟수는 실행 전에 profile에 고정한다. 비용은 단순 token 감소가 아니라 검증 완료당 비용·재시도·사람 수정 시간과 함께 평가한다. 비용이 미확인이면 비용 개선을 주장하지 않는다.

host-native, 현재 full harness 고정본, 얇은 공통 pack, 작업별 skill 추가를 같은 작업에서 비교한다. Claude/Codex별로 성공·프로젝트 정책 준수·실제 검증 실행·사용자 교정·불필요한 질문·범위 이탈·시간·비용을 측정한다. 개인 사고모델은 사람이 판별한 선택 사례와 holdout 작업으로 평가한다. 희귀한 안전 정책은 사용 빈도가 낮다는 이유로 제거하지 않는다.

첫 수직 단면 뒤 성격이 다른 두 번째 공개 저장소를 같은 계약으로 검증한다. 예를 들어 shell 중심 도구와 테스트 가능한 애플리케이션을 선택한다. 두 저장소를 통과하기 전에 첫 profile의 편의를 범용 SDK로 고정하지 않는다.

### 승인과 실제 반영

준비 worker와 apply executor의 권한을 분리한다. 승인은 artifact digest·base SHA·policy digest·target·account·action·만료 시각에 묶고, 변경되면 재승인한다. 승인된 범위만 실행하고 결과를 readback으로 확인한다. Goal 생성이나 구현 승인만으로 push·PR·merge·배포 권한이 생기지 않는다.

반응형 Inbox에는 후보 diff·검사·미확인·비용, 질문과 실제 반영 action을 구분해 보여 준다. G2는 단일 public realm의 내부 실증과 다른 realm 거부 검사를 포함한다. 고객의 웹·모바일 접근은 GH의 인증·tenant·전송 검증을 통과한 관리형 환경에서 제공한다. G4는 이후 개인 로컬·조직 환경 연결을 뜻하며, GH로 회사 컴퓨터의 원격 제어 권한이 생기지 않는다. 각 realm의 credential·원문·원장은 분리한다.

### 개인화와 정보 경계

검색 전에 realm·source ACL·기기·작업 권한을 검사하고, 허용 자료 안에서 관련성·최신성·중복·토큰 예산으로 선택한다. 회사 원문을 개인 세션으로 읽은 뒤 마스킹하는 방식은 금지한다. 업무 존재 자체도 기본 비공개이며, 조직이 별도로 승인한 최소 상태 projection만 대상·TTL·철회 정책에 따라 개인 화면에 표시할 수 있다. 요약·임베딩도 원본 분류를 상속한다.

직접 요청, 에이전트의 위임 프롬프트, 실제 전달문, 독립 검증 결과, 사용자 교정을 Work/Attempt로 연결한다. 원문 장기 보관·학습은 별도 동의와 realm 정책을 따른다. 에이전트 작성문을 사용자 선호로 자동 승격하지 않는다. 승인된 메모리와 프롬프트 생성기 최적화는 별도 흐름으로 관리한다. 상세 데이터 계약·공격 사례·삭제 범위는 서비스 상세 계획 §3~5를 따른다.

기존 계획 승인·core의 Decision/Approval·host의 도구 승인을 같은 화면에서 관련 요청으로 묶고, 이미 허용된 범위를 반복 질문하지 않는다. 다만 한 종류의 승인이 다른 권한을 만들지는 않는다. 기존 Voice 입력을 보존하고 G3에서 질문 확인·응답·승인 범위 재확인을 연결한다. 답변을 잘못 인식했거나 version이 바뀌면 실행하지 않는다.

### Family 연결과 Hearth 재평가

- **Glow**: 현재 session-local HUD를 보존하고 managed projection은 선택 기능으로 연결한다. 기존 v1 reader가 있는 지원 버전에는 consumer-first 전환을 적용한다. reader가 제거된 버전에는 adapter를 별도로 합의하고 테스트하며 기존 기능으로 가정하지 않는다. 명시적으로 해석한 실행 경로를 사용하고 cache의 가장 높은 버전을 임의 선택하지 않는다. 조회 실패를 PASS나 0원으로 표시하지 않는다.
- **Hearth**: G0에서 백업·동결하고 초기 출시 필수 항목에서 제외한다. core 비관리 프로젝트까지 모으는 Markdown 보고서 수요가 있을 때 재평가한다. 유지 시 core projection과 legacy progress adapter를 읽고 source·관측 시각을 표시한다. 수동 `done`·checkbox를 검증 완료로 승격하지 않는다.
- **Hearth 활성화 조건**: sources/preset schema, Node/Python 공통 fixture 또는 단일 normalized read model, shell 보간 제거, project/preset ID와 출력 경로 검증, 명시적 demo 모드, realm별 config/output, 비파괴 installer를 갖춘다. 현재 옛 설치 URL·누락 schema·repo 내부 생성물 경로를 수리한 뒤 설치한다.
- **Hearth 거취**: 다중 source·portable Markdown의 실사용이 있으면 독립 유지한다. core 데이터만 쓰고 출력만 필요하면 core report로 흡수한다. 수요가 없으면 이력·복원 가능한 archive를 보존한다. 지금 즉시 병합·삭제하지 않는다.
- **Flow**: 비즈니스 policy/spec/TC는 선택 capability로 평가한다. legacy workflow state는 importer 또는 외부 참조로 읽고 같은 managed Work에 두 원장·scheduler를 붙이지 않는다. `flow sync`의 cache 경로 결합을 새 구조에 이식하지 않는다.
- **Herdr**: 관찰과 mutating capability를 별도로 선언한다. pane/agent prompt·worktree 생성/제거의 권한·취소·결과 확인을 검사하며 terminal의 `done`을 Work 완료로 사용하지 않는다. Herdr 미설치 상태의 direct runtime도 지원한다.
- **Voice/Whetstone**: 기존 Voice 경로를 새 설치·smoke test 전에 이동하지 않는다. Anvil의 provider 차이를 adapter로 분리한다. Whetstone의 개인 연습·프로필은 별도 소유이며 core에는 허용된 참조만 둔다.

## 6. 구현 순서와 병렬 작업 경계

이 문서의 P0a/P0b~P4는 통합 계획의 단계명이며 G0a/G0b~G4는 완료 단위다. 과거 문서의 단계 번호는 아래 매핑을 적용한다.

| 단계 | 결과 | 진입과 종료 조건 |
|---|---|---|
| P0a baseline 복구 | WIP 복원·접근 가능한 family inventory·기존 동작과 설치본 기준선 | G0a 복원 리허설 뒤 lane A 시작 가능 |
| P0b 실행 계약 | 책임 ADR, 정답 fixture, host 능력표·runtime 실증·예산 | G0b에서 해당 작업의 blocking 결정만 해소. B는 host 능력표, C~F는 최소 schema 뒤 시작 |
| P1 기반 병렬 구현 | 안전성 수리 뒤 host pack·설치, ledger·verifier·runtime stub·Inbox mock | P0 뒤 서로 독립된 모듈만 병렬. G1a 안전성·G1b 두 host pack을 구분하고 공통 schema는 단일 담당 |
| P2 첫 수직 단면 | 단일 runtime의 격리 변경·독립 검증·질문·승인·반영·복구·단일 장비 무인 준비 | 작은 로컬 결합 시험 뒤 전체 수직 단면 완료. 실제 repo 개선·provenance·OS wake/restart·취소·stale 승인 검증 |
| PH 완전관리형 alpha와 유료 파일럿 | 설치·키 없는 샘플 → 최소 권한 연동 → 격리 실행 → 독립 검증 → 보호된 preview → 승인된 반영 | G2 핵심 계약과 GH 격리·인증·예산·복구·삭제 검증 후 고객 제공. G1b/G3 미완료 시 지원 범위를 단일 runtime alpha로 명시 |
| P3 멀티모델 출시 검증 | Claude/Codex 두 runtime·두 pack·서로 다른 repo profile, Glow·Voice·설치·복구 | 동일 핵심 계약, native/managed 독립 가치, 정책 위반·허위 PASS·중복 action 부재와 작업 효과 검증 |
| PL 학습 평가 | 승인된 메모리·프롬프트 생성기 후보·모델별 평가·rollback | 수집·동의·출처는 G2/GH부터. GL의 독립 holdout과 보안·품질 기준을 충족한 뒤 GEPA 배치 최적화. 모든 요청에 최적화 실행 금지 |
| P4 선택 확장 | G4 로컬 connector·조직 BYOC·사내망, 별도 authority/worker, 이후 폐쇄망·추가 provider·고급 hosting | GH/G3 뒤 수요와 보안 검증별 Goal. 개인 웹·모바일은 GH, 조직 원격 접근은 별도 허가. Flow/Hearth는 선택 사항 |

| 기존 문서의 단계 | 이 통합 계획에서의 위치 |
|---|---|
| 9월 리팩터링의 기준선·안전성·기록 수리 | G0a → G1a. prompt 파일럿의 합성 평가 방법은 보존하고 생성기 승격은 GL |
| 09번 Phase 0, 11번 P0 계약, 12번 P0 계약 | G0b의 최소 fixture → P1 core 기반. 전 객체의 영구 schema 고정을 선행 조건으로 두지 않음 |
| 09번 Phase 1, 11번 P1, 12번 P1 개인 수직 단면 | G2. 공개 코드 profile 하나·runtime 하나, 단일 장비 무인 준비 포함 |
| 09번 Phase 2, 11번 P2, 12번 P2의 두 runtime | G3. 두 native pack은 별도 G1b 검증 |
| 09번 Phase 3, 11번 P3, 12번 P2의 원격·모바일·별도 worker | 관리형 웹·모바일은 GH, 로컬·조직 connector는 G4. 단일 장비 복구와 구분 |
| 09번 Phase 4~6, 11번 P4~P6, 12번 P3, 8월 Flow 실행 엔진 | 학습 기반은 G2/GH·최적화는 GL, 조직/고급 확장은 P4. Flow는 필수 엔진으로 채택하지 않음 |
| `codex-coexistence.md`의 pack 단계 | G1b의 생성·설치·실호스트 검증. core runtime 단계와 구분 |

첫 runtime 후보는 현재 CLI가 있는 Codex지만, P0 실증에서 구조화 이벤트·인증·필수 권한 경계가 안 맞으면 Claude를 먼저 연결한다. **연결 순서가 바뀌어도 P3의 두 runtime 조건은 유지한다.** native pack은 개발 호스트의 사용성이고 runtime adapter는 코어 실행 능력이므로 각각 테스트한다.

### 병렬 lane

| lane | 저장소와 소유 범위 | 선행 조건 | 완료 산출물 |
|---|---|---|---|
| A 기존 제품 안전성 | code-forge hooks·상태 유틸·회귀 fixture | baseline 고정 | 결함 재현, 수정, 실제 payload 결과 |
| B 멀티호스트 pack | code-forge compiler·설치·생성 manifest | P0 host 능력표 | dry-run·설치·제거와 Claude/Codex 발견 증거 |
| C 원장과 정책 | core contracts·ledger·policy | P0 schema | migration·중복·재시작·realm 검사 |
| D 독립 검증 | core verification·repo profiles | P0 schema | 허위 PASS·weakening·baseline 비교 검사 |
| E runtime 연결 | core runtime-adapters | P0 capability 계약 | 두 runtime adapter와 conformance |
| F 검토와 반영 | core inbox·execution | P0 mock으로 시작, C/D 연결 뒤 완료 | stale 승인 차단·apply/readback·질문 재개 |

lane 수는 동시 에이전트 수가 아니다. P1은 A+B와 코어 기반 중 준비된 작업을 최대 2개 lane부터 실행하고, 완료된 lane을 D/E/F로 교체한다. 공유 파일이 겹치면 직렬화한다. A/B의 `bin/forge`, CI, setup 접점은 통합 담당자 한 명이 맡고 각 lane은 독립 모듈과 테스트부터 만든다. core 공통 schema·lockfile·루트 CI도 단일 소유자만 수정한다.

각 lane은 별도 worktree·브랜치를 사용한다. 결과에는 기준 SHA, 변경 범위, 실제 검사 명령·결과, 미확인, 다음 의존성을 남긴다. merge 후 통합 HEAD에서 재검증한다. 독립 reviewer는 수용 조건·diff·증거를 받고 작성자의 장문 추론을 근거로 삼지 않는다. 서로 다른 모델 사용은 가능한 경우의 검증 강화이며 결정적 검사를 대체하지 않는다.

통합 담당자는 marketplace catalog/BOM, Glow consumer-first·parity, Voice 경로와 provider, 개인 profile 전달 fixture, 기존 사용자 hook 보존을 조정한다. 인접 저장소 변경은 해당 Goal의 허용 경로에 포함한 뒤 수행한다. Hearth/Flow의 재활성화를 A~F의 선행 조건으로 두지 않는다.

## 7. 검수 후 설정할 Goal 초안

다음은 향후 Goal 문구이며 이번 문서 작성에서 Goal을 생성하거나 실행하지 않았다. 전체 플랫폼을 하나의 끝없는 Goal로 묶지 않고 검증 가능한 단위로 닫는다.

| Goal | 완료 조건 | 제외 범위 |
|---|---|---|
| G0a 복구 가능한 baseline | WIP 실제 백업·복원, 설치본/source 구분, 접근 가능한 family·기존 동작 baseline | 기능 구현·새 저장소 공개·배포 |
| G0b 최소 실행 계약 | 책임 ADR, 정답 fixture, profile/context, host 능력표·runtime 실증, 언어·저장 방식 ADR·실행 상한 | 전 객체 영구 SDK·모든 외부 action |
| G1a 기존 제품 안전성 | 재현된 gate·state·hook·handoff 결함 수리, 기존 alias·Smith 정책·Voice·Glow 회귀 | 전역 무인 원장 |
| G1b 두 호스트 pack | 공용 본문·descriptor, Claude/Codex 발견·권한·설치·재설치·제거, 사용자 설정·기존 hook 보존, core 없는 사용 | core runtime 지원 완료 주장 |
| G2 코어의 개인 수직 단면 | runtime 하나·repo 하나의 실제 개선·독립 검증·질문/승인·반영/readback, provenance·단일 realm과 타 realm 거부·OS wake/restart·취소 | 모든 provider·외부 action·원격 모바일·새 Voice 승인 기능·팀 서버 |
| GH 관리형 고객 alpha | G2 핵심 계약, tenant 격리·웹/모바일 인증·짧은 토큰·취소/복구, no-key 샘플, 최소 권한 repo 연동, 보호 preview, 비용 예약/정산·삭제·운영 대응 | 조직 장비 접근·무제한 실행·상시 앱 hosting 포함 주장. 상세 계획 §2·7의 출하 검사 필수 |
| GL 개인화 개선 | 수집 동의·출처·승인 메모리, 계보별 분리 eval/holdout, 모델별 품질·보안 비퇴행, 후보 검토·점진 배포·rollback·삭제 전파 | 모델 가중치 튜닝·모든 모델 최적 보장·조직 자료의 개인 학습 전용 |
| G3 멀티모델과 family 출시 gate | 두 runtime·두 pack·두 profile, native/managed·Glow·Voice·호환성·복구·실제 효과 보고 | GLM/Qwen·Hearth 지원 완료 주장 |
| G4 로컬·조직 연결 | connector·BYOC·조직 IdP/기기 정책·realm별 저장소/키·egress 통제, disconnect·전원 장애·중복 응답 검사. 폐쇄망은 별도 오프라인 공급망·무통신 검사 | 개인 인증으로 회사 자료 접근·외부 모델 자동 fallback·임의 provider 지원 |

각 Goal에는 repo·branch·base SHA·쓰기 허용 경로·선행 Goal·소유 파일·검증 명령·중단 조건·token/시간/비용/동시성 상한을 붙인다. G0b의 인증 실증 전에는 허용된 account alias·realm·호출 범위와 실행 상한을 확인한다. 기존에 유효하게 허용된 범위는 재사용하고 새로운 유료 예산은 별도 결정한다. 결정 대기는 해당 실증만 차단하며 G0a·G1a의 독립 작업은 계속할 수 있다. 같은 실패 원인이 반복되고 새 증거가 없으면 해당 경로만 중단·보고한다.

## 8. 출시와 완료 판정

| 검증 범위 | 요구하는 증거 |
|---|---|
| 기존 사용자 보호 | 작업 전후 사용자 diff·설정 보존, 충돌·부분 설치·제거·rollback fixture |
| 상태 안전성 | concurrent write, crash/restart, stale lease, duplicate event, 알 수 없는 외부 결과 처리 |
| 호스트와 모델 | 실제 두 호스트 discovery·권한, 두 runtime event/cancel·결과 회수, 미지원 기능 표시 |
| 판정 정확성 | 실패·미실행·도구 부재가 PASS로 바뀌지 않음, tested SHA 일치, 증거 digest 확인 |
| 권한 경계 | stale approval·realm 혼합·무허가 fallback 차단, 준비 worker의 반영 권한 부재 |
| 개선 효과 | 고정 profile의 correctness·보조 지표 비퇴행과 주 지표 개선. 개선 실패도 정직한 기각 결과로 보존 |
| 설치본 일치 | 소스 fixture, 실제 host, 배포 설치본을 구분해 기록하고 핵심 흐름 재검증 |
| 사고모델 보존 | 승인된 profile·Blueprint의 실제 선택 적재, 프로젝트 제약 보존, 사용자 판단 일치·질문·범위 이탈 비교 |
| family 호환 | 기존 alias·Smith semantic golden·status v1·Glow·Voice와 사용자 hook 보존, Flow dual-write 부재 |
| 데이터 수명 | realm별 경로·조회 권한·redaction·retention·삭제·복원 검증 |

문서 검토·mock 통과·실호스트 통과·배포 완료는 서로 다른 상태다. 자동 최적화 후보가 기각돼도 판정 시스템은 정상일 수 있지만, 실제 개선 효과를 주장하려면 재현된 성공 사례가 필요하다.

기존 플러그인 버전을 올릴 때는 `CHANGELOG.md`와 `.claude-plugin/plugin.json`을 같은 커밋에서 갱신한다. 배포 단계에서는 저장소 AGENTS.md의 main push→project/local plugin update→캐시 핵심 변경 spot-check를 따른다. 소스 수정만으로 배포 완료를 선언하지 않는다. 새 코어는 별도 버전과 pack/protocol 호환표를 갖고, 두 제품의 지원 조합을 CI에서 확인한다.

`forge-market`의 catalog 하나에서 host별 manifest와 호환 BOM을 생성한다. 제품 version·source SHA·tag·artifact digest·contract 범위를 연결하고 같은 version에 다른 artifact를 배포하지 않는다. stable/dev를 분리하며 stable 설치는 runtime `git pull`로 바꾸지 않는다. 이 문서 커밋은 plugin version bump·배포가 아니다.

복구 검증은 설치물의 검증 후 원자 전환·이전 버전 복원, 소유한 설정 조각만 제거, candidate worktree 폐기, ledger migration 백업/복구, 외부 action readback/보상으로 나눈다. core 중지 시 새 managed 실행을 차단하고 기존 결과를 조정한다. native 작업은 독립적으로 유지하되 미확정 managed Work를 자동 인계하지 않는다. 지원할 N/N-1 또는 정확한 protocol·pack 조합을 선언하고 실제 설치·복구 drill로 검사한다.

## 9. 이번 검수에서 결정할 사항

| 항목 | 권고안 | 결정이 필요한 시점 |
|---|---|---|
| 저장소 경계 | CodeForge 무료 OSS 유지 + 이를 소비하는 별도 제품 권고. 신규 core repo 필수 아님 | G0b packaging·consumer 실증 후 |
| 제품·메타포 | CodeForge OSS, Atelier 가칭 제품. Library/Workbench/Inspector는 설명용 책임 이름 | G0 ADR·상표 검토 전 이름 확정 금지 |
| 첫 고객 경험 | 완전관리형 GH, 로컬/BYOK는 선택. 실행·임시 preview·상시 앱 hosting 비용 분리 | G0b 비용/격리 실증, 고객 제공 전 GH |
| 수익 구조 | 기본 구독 + 제한된 사용량 + 명시적 추가 구매. 가격은 가설, 무제한 약속 금지 | 유료 파일럿 전 실제 원가·약관 검증 |
| 기존 계획과의 관계 | 이 통합 계획을 실행 순서 기준으로 채택. 기존 문서는 요구사항·이력으로 보존 | G0 시작 전 |
| 직접/관리 실행 | 작은 작업은 native, 장기 목표는 명시적 managed. 설치만으로 자동 전환 금지 | G0 계약 |
| 정책·판정 권위 | advisory/preference와 집행 항목 구분, managed verdict는 core, host permission 별도 | schema fixture 전 |
| 상태·계약 정본 | 기존 status v1·프로젝트 progress·개인 profile 보존, 새 Work 계약만 core 소유 | schema fixture 전 |
| flow-toolkit | 필수 엔진으로 부활시키지 않음. 검증 요구만 계승 | G0 시작 전 |
| Hearth | 휴면 백업. 다중 source Markdown 수요와 안전성·schema·parser gate 뒤 유지/흡수/archive | G0 동결, P4 재평가 |
| Glow·Herdr | Glow는 projection, Herdr는 권한 있는 제어 adapter. 실제 설치·능력 별도 검증 | G0 능력표 |
| Voice·Whetstone | 접근성 경로·승인된 개인 프로필·사람 학습 보존, 자동 규칙 승격 금지 | G1 baseline 전 |
| context·언어 | 권한 선검사·최소 선택·출처는 G2/GH부터. 고급 검색 UI·자동 언어 최적화는 후속 | G0 최소 fixture, GH 누출 검사 |
| 멀티모델 범위 | Claude/Codex 두 runtime·두 native pack을 초기 출시 gate로 지정 | G0 시작 전 |
| 첫 실증 범위 | 공개 코드 저장소 한 곳과 구조화 runtime 하나, 이후 두 번째로 범용성 확인 | G0에서 repo·runtime 확정 |
| 기술 재결정 | 10월 Go+TS 결정과 TS 단일 후보를 설치·복구·SDK 실험으로 비교, SQLite WAL 검증 | G0 실험 뒤 ADR |
| 배포·호환·복구 | 단일 catalog·불변 artifact·stable/dev·호환 기간·종류별 rollback drill | G0 정의, G1/G3 검증 |
| 비용과 계정 | 허용 계정·realm·외부 action·예산·실행 시간 명시 | 유료·인증 실행 전 |
| 데이터 보존 | realm별 DB·artifact·원문 수집 범위·retention·export/delete·백업 정책 | 첫 managed 실행 전 |
| 공개와 라이선스 | 새 저장소 공개 범위·라이선스는 별도 확정. 비공개 참고 코드 복사 안 함 | 저장소 공개·배포 전 |

이번 개정은 공개 문서 통합이며 새 교차 모델 검수는 수행하지 않았다. Goal·새 저장소·runtime 계정 연결·인접 저장소 변경·배포는 별도 구현 단계다. 구현 시작 시 G0a에서 복원 가능한 baseline을 확보하고, G0b에서 packaging과 관리형 격리·원가를 함께 실증한다. 로컬 개발 실증을 고객의 설치 의무로 해석하지 않는다.
