# CodeForge 개인화 코어와 멀티모델 어시스턴트 구현 계획

> **최신 상세 정본:** [터미널 UX를 반영한 통합 최종안](../docs/imported/codeforge-final-plan-with-terminal-ux.md). 상세 설계·지원 범위·실행 gate는 이 정본을 우선한다. 이 문서는 기존 실행 계획과 유효한 호환·검증 요구를 보존하고 후속 확정 사항과 결정 차이를 보완한다. 상세 원문은 변경하지 않는다. 현재 상태와 다음 행동은 [CURRENT](../docs/improvement-plan-2026-09.md)에서 읽는다.
>
> **게시 상태와 2026-11-07 추가 후보 범위:** 기존 기획 문서 네 개는 `docs/agentops-platform-plan`의 `a2ecb128d9928e7645a345f5fccd14a35b1028ee`로 게시됐고 실제 원격 readback의 SHA 일치까지 확인됐다. 이번 선택의 문서 반영·commit/push 승인은 이미 받았으나 이번 호출은 문서 두 개의 후보 준비·검증만 하며, 이번 추가 commit/push는 아직 하지 않았다. main·릴리스·제품 배포와 구현·기각 디자인 재개는 승인 범위에 포함되지 않는다. 이번 추가 후보를 이미 게시한 것으로 기록하지 않으며 최종 커밋 자신의 SHA를 본문에 넣지 않는다.

> 전체 그림부터 보려면 **[서비스 한눈에 보기](../docs/agentops/README.md)** — 사용자 흐름·구성도·기존 CodeForge와의 관계·구현 순서.

작성일: 2026-10-18 · 기존 본문 개정: 2026-10-25 · 정본 연결: 2026-11-05 · 결과 작업대 중심·TUI/원격 우선 선택·결정 상태 보완: 2026-11-07. 기존 개인화 코어·공통 기억 기반·Reflexion·어시스턴트와 실행 에이전트의 구분을 유지한다. 10월 개정과 이번 후보 준비에서는 새 교차 모델 검수·제품 구현·배포를 수행하지 않았다.

[서비스 계획](../docs/agentops/13.hosted-personalized-service-plan.md)과 이 문서는 최신 상세 정본에 모순되지 않는 사용자 경험·개인화·사업성·구현 요구를 보존한다. 충돌하는 단계·지원 범위는 최신 상세 정본을 따른다. 기존 과거 설계와 HTML은 당시 이력이며, 이번에 기각된 시안과 그 파일은 반입하지 않는다. [이전 통합 검수 기록](../docs/agentops/evidence/2026-10-18-integrated-plan-review.md)은 당시 증거다.

## 만들려는 제품과 기존 시스템

**여러 모델이 사용자의 공통 기억과 판단 기준을 활용해, 함께 일할수록 더 잘 맞는 개인 어시스턴트가 되는 환경**을 만든다. 코어가 프로젝트 지식·승인된 선호·작업 경험·결과를 지속적으로 관리하고, 현재 목표에 맞는 맥락과 모델별 지시를 구성한다. 사용자 교정과 검증된 실행 결과는 다음 작업의 판단 개선으로 이어진다. 첫 적용 분야는 개발이며 터미널·웹·모바일은 이 코어의 접점이다.

| 개념 | 책임 |
|---|---|
| 개인 어시스턴트 | 사용자에게 이어지는 작업 경험. 특정 모델·세션·서브에이전트와 동일시하지 않음 |
| 개인화 코어 | 공통 기억의 정본·출처·수명·권한, 작업별 맥락·지시 구성, 교정·결과 기반 개선, 작업 상태·예산·검증·승인·복구 |
| 실행 에이전트 / 서브에이전트 | 선택된 모델·도구로 현재 작업 / 위임된 부분 작업 수행. 임시 실행 종료 후에도 코어의 허용된 기억·결과는 유지 |
| 기존 CodeForge OSS | 규칙·스킬·지식 조합·결정적 도구와 호스트별 설치·업데이트. 코어가 재사용할 원본 제공 |
| 터미널·웹·모바일, Glow·Herdr·Voice | 요청·작업·질문·결과에 접근하는 접점. 기억의 별도 정본이나 독립 완료 판정기를 만들지 않음 |

‘내가 하는 것처럼’은 허용된 선호·판단 기준·위임 범위를 행동과 결과에 반영한다는 뜻이다. 모델이 사용자를 완전히 알거나 같은 답변을 보장한다는 뜻은 아니다. 기억 부재·충돌·미지원 능력을 드러내고 근거 있는 반론을 유지한다. 작은 작업은 주 실행 에이전트가 직접 처리하며 필요한 경우에만 스킬·서브에이전트를 선택한다.

기존 CodeForge는 무료 독립 사용을 유지한다. 관리형 코어의 저장소 분리는 G0b 실증 후 정하며 새 저장소부터 만드는 것을 선행 조건으로 두지 않는다. 개인화 데이터의 공통 저장 기반은 공개 제품 코드 저장소와 별개다. Atelier는 이름 후보이며 최초 고객 alpha는 단일 runtime으로 가능하다. 두 native pack과 두 runtime을 각각 검증한 G3에서 Claude/Codex 멀티모델 지원을 선언한다.

## 1. 찾아낸 계획과 현재 증거

최신 상세 정본 §1·9 및 말미의 검토 범위에는 실제 Claude 독립 검토와 개인 Codex 대조·별도 감사가 기록돼 있다. Claude 검토는 당시 승인 bundle, 개인 대조는 당시 지정 자료에 한정된다. 이번에는 그 기록을 지닌 승인된 정본만 읽었으며 리뷰 원문·bundle·실행 로그를 추가 조회하거나 반입하지 않았다. 사업·설계·인프라·보안·수익성에 대한 계획 검수는 제품 구현·시장 검증·격리 실증의 완료가 아니다.

아래 수치·버전·Git 기준과 ‘이번 조사’는 10월 본문 작성 당시의 기록이다. 2026-11-05 후보 준비에서 앱·호스트·실행기 smoke, 테스트·formatter, 추가 모델 검토를 수행했다는 뜻이 아니다.

<details>
<summary>계획 이력과 조사 당시 증거 — 구현 담당자 참고</summary>

| 자료 | 확인한 내용 | 이번 계획에서의 지위 |
|---|---|---|
| [로컬 멀티런타임 설계](../docs/codex-coexistence.md) | Claude native, Claude→Codex bridge, Codex native를 구분. 공통 소스에서 skills·agents·hooks 생성, dry-run→opt-in 설치→배포 계획 | 기존 저장소의 멀티호스트 구현 요구사항으로 유지 |
| [로컬 라우팅 정책](../references/routing-policy.md) | FAST/BALANCED/DEEP와 effort·fan-out 분리. 실제 resolver 구현 전에는 advisory | 공통 정책 원본으로 유지. 실행 시점 강제와 기록은 새 코어가 담당 |
| [8월 자율 개발 계획](../archive/docs/agentops/autonomous-development-loop-plan.md) | 2026-08-31. 기존 구조 유지, flow-toolkit에 opt-in 실행 상태·증거·재시도 위임 | 역사 자료로 보존. 검증·무효화 요구와 opt-in 원칙을 계승하고, 필수 실행 엔진은 새 코어로 대체 제안 |
| [9월 리팩토링 정본](https://github.com/ggombee/code-forge/blob/3c856754f1d01d1b8cfe0557465b1ac906e81df8/docs/code-forge-refactoring-plan.md) | 9월 22일 결정 진행. 구현 저장소는 code-forge. 안전성·상태 수리·적재·프롬프트 평가 중심. Codex 전용 플러그인과 별도 엔진은 당시 범위 제외 | 안전성 수리와 평가 방법을 계승. 당시 범위 제외를 장기 금지로 해석하지 않음 |
| [10월 AgentOps 문서 지도](https://github.com/ggombee/code-forge/blob/e05552cd35939dc7e5d50709dd0963c8c2abfe3e/docs/agentops/README.md) | 10월 16일 최신 커밋. 새 host-neutral core 모노레포, 기존 CodeForge의 adapter·policy pack 전환 명시 | 제품 목적과 저장소 분리 방향의 기준 |
| [10월 제품·기술 설계](https://github.com/ggombee/code-forge/blob/e05552cd35939dc7e5d50709dd0963c8c2abfe3e/docs/agentops/11.codeforge-public-service-architecture-debate.md) | 측정→최소 변경→독립 검증→승인→반영. Claude/Codex·저비용 모델, capability·realm·예산 설계 | 새 코어의 상위 요구사항 |
| [10월 무인 실행 설계](../docs/agentops/12.night-runner-reference-audit-and-design.md) | durable 원장, 재시작, 질문 분리, 준비와 실제 반영 분리 | 공개 가능한 합성 사례로 검증할 상태·권한·복구 수용 조건 |
| 저장소 밖 `workspace/plan/code-forge-final-upgrade-plan.md`, `code-forge-harness-upgrade-plan.md` | 2026-03-27의 하네스 강화·AGENTS 도입 계획 | 역사 자료. 당시 점수·개수·지원 정보는 현재 사실로 재사용하지 않음 |

초기 조사 checkout의 `main` HEAD는 `1779c8a`였다. 당시 미커밋 코드·훅·스킬은 문서 커밋에 포함되지 않았다. 이번 통합은 원격 `docs/agentops-platform-plan`의 `e05552cd`와 원격 `main`의 `e9b9c1f`를 계획 브랜치에서 합친 `243eb1a`를 검수 기준으로 삼는다. 원본 작업트리의 미커밋 파일은 별도로 보존하며, 문서 통합을 구현 baseline 보존으로 계산하지 않는다.

9월 문서의 런타임 검사 23건·상태 검사 9건은 초기 조사 checkout의 결과가 아니었다. 이번에는 원본 작업트리의 미추적 `lib/`·`tests/`를 확인하고 두 검사를 다시 실행해 각각 23건·9건 통과를 확인했다. 이 코드는 계획 브랜치에 들어 있지 않으며 실호스트·CI·설치본 검증도 남아 있다. 계획 브랜치의 `hooks/quality-gate.sh`는 macOS Bash 3.2 구문 검사에서 실패했다. G0a에서 복원 리허설을 거쳐 재사용하고, G1a의 완료 여부는 통합된 코드로 다시 판정한다.

추가 검수 범위는 `forge-glow`, `forge-hearth`, `flow-toolkit`, `anvil-voice`, `coding-practice`, marketplace의 연결 계약이다. 초기 조사에서 기록한 설치·remote 상태는 해당 checkout의 snapshot이다. 이번에 확인한 Glow는 커밋된 `0.8.0`과 미커밋 `0.9.0`이 다르며, 후자는 세션별 표시를 유지하면서 `hud/lib/parse-forge.sh`를 제거하는 중이다. 따라서 기존 v1 consumer가 현재 존재한다고 가정하지 않는다. G0a에서 접근 가능한 source·설치본·remote를 구분해 기록하고, 없는 저장소는 `unavailable`로 남긴다. 공개 문서에는 실제 사용자 경로·계정·비공개 자료를 복사하지 않는다.

10월 원안의 Go daemon·CLI + TypeScript PWA 결정과 이번 TypeScript 단일 구현 후보는 서로 다르다. 언어 선택은 유지보수 비용·설치·signal/cancel·SQLite 동시성·복구 실험으로 재결정하고 ADR에 대체 이유를 남긴다. 지식 검색과 고급 언어 최적화는 뒤로 미루되, 원안이 요구한 실제 context·출처·언어·revision 기록은 첫 실행부터 유지한다.

</details>

## 2. 저장소를 나누는 이유와 소유권

| 선택 | 이점 | 비용과 판단 |
|---|---|---|
| 기존 저장소의 분리된 패키지에서 실증 | 한 저장소에서 개발·리뷰 가능 | 설치물·배포·의존성을 분리할 수 있는지 G0b에서 검증. 실험 단계의 유효한 선택 |
| 기존 제품을 폐기하고 새 저장소로 전부 이동 | 새 구조에 일괄 정리 | 사용자 설정·배포·미커밋 개선 이관 부담이 큼. 제외 |
| 기존 제품 개선과 새 코어 분리 | 기존 사용자 호환성을 유지하며 중립 실행 플랫폼 구축 | 버전 협상·통합 검증 필요. **권고안** |

CodeForge는 기존 OSS의 이름으로 유지하고, 새 관리형 제품의 이름과 저장소 경계는 별도 결정한다. 아래의 `core`는 개인화와 실행 관리의 논리적 책임이며 반드시 독립 저장소나 마이크로서비스를 뜻하지 않는다. 호스트별 구현은 우선 같은 저장소에서 관리하되, Claude 중심 파일 구조나 동일 본문을 다른 호스트·모델에 강제하지 않는다. 호스트별 자동 적재 파일·설정·skill과 평가로 채택한 모델별 본문을 별도로 둘 수 있다. 저장소 분리도 금지하지 않으며, 공통 저장소 안의 특화로 해결되지 않는 배포·의존성·소유권 문제가 실증되면 G0b 이후 ADR로 결정한다. 기존 제품은 가입·유료 서버 없이 독립 사용 가능해야 한다. 새 제품은 Claude 플러그인 설치 없이 versioned pack artifact·저장소 profile·runtime adapter로 실행한다. pack은 설치 때 pin하며 세션 시작에 원본 저장소를 자동 갱신하지 않는다.

| 대상 | 책임 | 갖지 않는 책임 |
|---|---|---|
| 기존 `code-forge` | rules·references·skills·Smith 공통/특화 원본, 필요한 지침을 구성하는 compiler와 결정적 로컬 도구, 선택 pack과 호스트별 출력·설치·갱신·진단, 기존 CLI 호환 | 전역 Work 원장, 별도 무인 scheduler, 독립 승인 DB |
| 새 `code-forge-core` 가칭 | 개인 기억·경험의 정본과 수명, 맥락/개인화 지시 구성·Reflexion 후보 관리, Work 원장·권한·runtime adapter·독립 검증·질문/승인·apply/readback | 기존 스킬 전체 복제, 자체 모델 서버·IDE·PTY·agent loop 재구현 |
| `flow-toolkit` | legacy 상태 보존·read-only importer 후보, 비즈니스 policy/spec/TC capability 평가 | 새 코어와 같은 Work를 별도 기록·재시도·최종 판정 |
| `forge-glow` | session/live HUD, versioned 상태 조회와 표시 | Work 완료 판정·승인·원장 수정 |
| `forge-hearth` | 휴면 상태 보존. 재채택 시 다중 source의 Markdown 보고서 생성 | Work·Decision·Approval 기록과 실제 반영 |
| Herdr | 선택형 터미널·pane·workspace·interactive agent 제어 adapter | Work 완료 판정·core 승인 대체 |
| Voice / `anvil-voice` | 기존 STT·단축키·입력 경로 보존, provider adapter와 접근 가능한 질문·응답 | 자연어 응답만으로 승인 scope 확대 |
| Whetstone / `coding-practice` | 이미 별도 Git 저장소인 개인 연습 도구. 본 서비스의 설치·실행·출시 범위에서 제외 | core의 필수 profile 저장소·학습 엔진·필수 의존성. 선택적 승인 profile 참조만 별도 허용 |
| `forge-market` | catalog 원본, host별 marketplace manifest·호환 BOM 생성 | runtime scheduler·Work 원장 |

새 코어의 초기 모듈은 `contracts`, `memory/context`, `ledger`, `policy`, `verification`, `runtime-adapters`, `execution`, `cli`, `inbox`, `conformance`다. 이는 책임 분리이며 처음부터 개별 서비스나 별도 패키지를 뜻하지 않는다. 로컬 원장은 SQLite WAL을 기준으로 검증하고, 언어·DB 드라이버·배포 방식은 G0b 실험 뒤 확정한다. 기존 shell을 일괄 재작성하거나 범용 workflow DSL을 만들지 않는다.

### 최신 통합안과 외부 참고의 지위

Core 권위·controlled OMP fork·upstream 선택 반입·host/renderer 교체성은 최신 상세 정본 §1~6을 적용한다. 아래의 직접 runtime adapter·설치·pack 설계는 그 경계 안의 후보와 호환 요구로 유지하며, OMP를 우회하는 별도 agent loop·terminal/PTY/GPU/framework 재구현을 초기 필수로 추가하지 않는다.

상세 정본 §6의 [Paperthin](https://github.com/LilMGenius/paperthin)·Hermes Agent는 선택 참고 후보다. 해당 절의 기능 설명은 정본이 전달한 참고 내용이며, 이번 반영에서 공식 구현·최신 기능·가격·라이선스의 확인 근거를 추가 확보하지 않았다. 필수 의존성이나 도입 완료로 해석하지 않는다. 실제 자산 채택은 정본의 출처·권리·version/digest·평가·rollout gate 뒤 결정한다. OMP·SDK의 고지와 사용자에게 보이는 제품 브랜딩의 구분은 정본 §2·6을 따른다.

### 범용화를 위한 의존성 경계

개인화 코어와 관리형 실행을 논리적으로 분리한다. **코어의 기억·맥락 기능은 CodeForge pack, Git 저장소, 관리형 Work, 웹 화면 없이 호출할 수 있어야 한다.** 관리형 실행은 그 코어를 소비하고 추가 실행 계약을 집행한다. 처음에는 같은 저장소·프로세스의 모듈로 구현하며 배포·보안·소유권상 실제 필요가 생길 때 물리적으로 나눈다.

| 경계 | 공통 책임과 교체 가능한 부분 |
|---|---|
| 개인화 ↔ 관리형 실행 | 공통은 신원·realm·기억 수명·맥락 선택·교정 근거. Work 원장·scheduler·실행 승인·apply/readback은 관리형 실행 책임. 기억 호출에도 접근·전송·수정 권한과 사용량 제한·감사 근거 적용 |
| 코어 ↔ CodeForge 개발 기능 | 목표·근거·산출물·수용 기준은 공통. repo·SHA·PR·테스트 명령·Smith·개발 스킬은 개발 adapter에 둠. 비개발 작업에 Git·테스트 PASS를 필수 필드로 강제하지 않음 |
| 모델 제공자 ↔ 에이전트 호스트 | 모델 입력·context 한도·usage와 호스트 자동 적재·도구 권한·이벤트 능력을 별도로 해석. 어댑터가 실제 전달·관측 범위를 보고하며 동일 프롬프트나 동일 결과를 강제하지 않음 |
| 기억 정본 ↔ 저장·검색 엔진 | 권한·출처·동의·revision·철회가 제품 계약. DB·벡터/그래프 인덱스는 교체 가능. 검색 인덱스는 파생물이며 export/import·복구 시 삭제된 기억과 철회 권한을 되살리지 않음 |
| 피드백 ↔ 개선 전략 | 명시 교정과 결과 기록은 기본. Reflexion·검색 최적화·추가 모델 평가를 교체 가능한 전략으로 두고 매 요청의 필수 호출로 만들지 않음 |
| 코어 ↔ 접점·외부 도구 | 터미널·웹·모바일·STT·MCP는 선택 접점. `.claude` 경로·`bin/forge`·특정 OS·마이크·IDE를 공통 기능의 필수 의존성으로 두지 않음 |

의존 방향은 접점·실행 모듈·분야별 adapter가 공통 계약을 소비하도록 둔다. 조립 지점에서 저장·모델·도구 구현을 연결하고, 코어가 특정 플러그인을 import해 동작하지 않게 한다. 기존 엔진 재사용과 자체 구현은 동일한 권한·수명·비용 기준으로 비교한다. 모든 DB·모델·프로토콜의 공개 SDK를 먼저 구축하지 않는다.

G0b에서는 작은 비개발 fixture 하나로 경계를 설계한다. 예를 들어 문서 작성 선호의 기억 → 관련 맥락 구성 → 교정·철회를 Git·CodeForge pack·관리형 Work 없이 표현할 수 있는지 본다. G2에서 그 최소 흐름을 구현 검증하고 실제 개발 작업의 개인화 평가와 함께 확인한다. 이는 비개발 서비스 출시나 성능 입증을 뜻하지 않는다. G3의 두 실제 호스트 검증 전에는 모의 전달만으로 멀티모델 지원을 선언하지 않는다.

### 제품 형태 재검토: 플러그인 중심에서 지침 구성·결정적 도구 중심으로

업데이트 전달을 위해 선택한 플러그인 포맷을 서비스 전체의 중심 구조로 고정하지 않는다. **CodeForge의 중심을 재사용 가능한 정책·지침 원본, 필요한 내용만 구성하는 compiler, 결정적 로컬 도구로 옮기는 방향을 권고한다.** 기존 플러그인은 로컬 호스트의 발견·호출·설치 접점으로 유지하되, 관리형 서비스는 승인된 모듈과 산출물을 직접 소비한다. 장문의 `/start` 지침과 전체 plugin catalog를 매 실행에 이식하는 구조로 확장하지 않는다. 이는 형태 변경 권고이며 현재 구현의 성능 열위를 입증했다는 뜻은 아니다.

| 대안 | 비용을 줄일 수 있는 경로 | 전체 서비스에 미치는 영향과 판단 |
|---|---|---|
| 현재 통합 플러그인을 중심으로 확장 | 기존 기능·설치·업데이트 재사용 | 상시 목록과 선택된 큰 workflow, host 의존 절차가 서비스에도 이어질 수 있다. 변경 비용은 낮지만 관리형의 기본 구조로 채택하지 않는다. 비교 기준선으로 보존 |
| 필요한 기능만 담은 작은 플러그인 | 상시 metadata·큰 workflow 축소, 선택 skill 사용 | 변경 비용이 가장 작다. 이 방식만으로 목표를 달성하면 compiler·라이브러리 확장을 추가하지 않는다. 첫 비교 후보 |
| 프로젝트 설정 생성 CLI만 제공 | 설정 시점에 정적 내용 준비, 일상 모델 호출 경로 단순화 | 불필요한 지침까지 root 파일에 모으면 오히려 비싸진다. 동적 context·managed 복구·독립 검증을 대체하지 못하므로 로컬 경로의 일부로 사용 |
| 지침 구성 compiler + 결정적 도구 + 최소 host 접점 | 반복 판독·정규화·기록을 코드로 처리, 작업별 지침·짧은 결과 전달 | **권고 방향.** native에는 선별 pack/설정, managed에는 직접 재사용하는 모듈·산출물 제공. 구성·검증·호환 유지 비용을 포함해 순이득 검증 후 확대 |
| 모든 기능을 MCP/원격 API로 제공 | 공통 기능과 갱신을 중앙화 | 도구 schema·호출 왕복·중간 결과·서버 운영 비용이 생긴다. 자동 적재·hook·오프라인 동작을 모두 대체하지 못한다. 필요한 capability에만 선택 사용 |
| 독자 실행기 또는 관리형 서비스로 전부 흡수 | context와 도구 표면 제어 범위 확대 가능 | agent loop·권한·인증·복구·배포 책임과 서비스 의존 증가. 현재 runtime을 재사용하는 core 범위를 넘어선다. 토큰 절감만으로 새 실행기를 만들거나 무료 독립 사용을 없애지 않는다. |

효율의 직접 원인은 포맷이 아니라 **실제로 전달되는 context와 모델에게 맡기는 작업**이다. 같은 본문·도구·호출 흐름을 plugin에서 CLI/MCP로 옮기기만 하면 token 절감을 기대할 근거가 없다. Claude는 plugin의 상시 목록 비용과 실행 시 본문 비용을 구분하고, Codex도 skill metadata를 먼저 노출하고 선택된 본문을 나중에 적재한다. hook 코드는 그 자체로 workflow 전문을 모델에 넣는 것과 다르며, 출력 context와 실행 시간은 따로 계량한다. [Claude 비용 문서](https://code.claude.com/docs/en/plugins/measure), [Codex Skills](https://learn.chatgpt.com/docs/build-skills)

2026-10-24 작업트리의 정적 확인에서 `skills/start/SKILL.md`는 28,927 bytes, `skills/setup/SKILL.md`는 27,660 bytes다. `/start`에는 Flow 상태 정규화·명령 호출 예시·이벤트 기록 등 결정적 절차와 판단 지침이 함께 있다. 기존 사용자 변경에는 LOW 직접 수행과 점진 적재 개선도 있어, 모든 요청이 전체 agent 체인을 실행한다고 단정하지 않는다. 파일 크기는 청구 token이나 실제 적재량이 아니며 설치본의 사용량·지연·성공률은 이번에 측정하지 않았다.

책임을 다음처럼 옮기는 것을 비교한다.

- **코드가 처리할 부분:** manifest 판독, 명시 옵션 정규화, template 생성, digest·revision 검사, 결과 형식화·이벤트 직렬화, 정해진 검사 실행과 로그 추출. 짧은 명령과 구조화 결과로 제공해 모델이 매번 shell 절차를 재작성하거나 긴 원문을 옮기지 않게 한다. 코드로 옮겨도 권한·실행·도구 출력 비용은 남는다.
- **모델이 판단할 부분:** 목표 해석, 모호한 요구, 구현 선택·trade-off·개인 선호 적용, 결과 설명. Blueprint의 사고 원칙을 단순 금지 목록이나 결정적 분기로 바꾸지 않는다. 매 요청에 별도 LLM router를 붙이지 않고 명시 선택·간단한 조건부터 사용한다.
- **적재할 부분:** 최소 필수 계약과 선택된 지침·근거·관련 profile만 제공한다. native에서는 host의 실제 능력 안에서 작은 root 파일·선별 pack을 생성하며, 이미 읽은 skill 전문을 임의로 phase별 제거할 수 있다고 가정하지 않는다. managed에서는 core가 권한 검사·정책 해석 뒤 선택한 ContextEnvelope를 runtime adapter가 전달한다. realm·권한·profile/revision이 다르면 cache를 그대로 재사용하지 않는다.

이 compiler는 기존 host pack/Smith 구성 로직을 확장하는 책임이며 별도 영구 SDK나 서비스의 선행 구축을 뜻하지 않는다. canonical Work Compiler API·managed policy 집행·원장·독립 verifier·승인·apply/readback은 계속 core 소유다. native host의 agent loop를 다른 loop로 감싸지 않고, managed도 plugin의 `/start`·hook scheduler를 두 번째 실행 원장으로 사용하지 않는다. 공통 도구의 정책 검사 결과는 입력·증거이며 core 권위를 대체하지 않는다.

관리형 worker가 plugin 설치·전체 catalog 발견·host별 설정 이관을 실행의 선행 조건으로 삼는 구조를 피할 수 있다. 대신 모듈 배포·권한·캐시 무효화·profile 삭제 전파와 운영 호환을 직접 책임진다. 로컬 사용자는 작은 plugin/pack이나 설정 생성 경로로 독립 사용을 유지한다. MCP는 필요한 연결 표면으로만 쓰고 도구 정의·중간 원문을 대량 주입하지 않는다. 코드 안에서 데이터를 처리해 짧은 결과를 전달하는 공개 사례는 있으나, 그 절감률을 CodeForge에 적용하지 않는다. [Anthropic context 설계](https://www.anthropic.com/research/effective-context-engineering-for-ai-agents), [코드 실행과 MCP](https://www.anthropic.com/engineering/code-execution-with-mcp)

G0b는 필수 정책이 같은 host-native 최소 기준선, 현재 고정본, 작은 plugin, compiler/도구 직접 소비의 비교 설계를 정한다. 대규모 재작성보다 manifest 판독·상태 정규화·검사 결과 전달 중 작은 경계 하나를 실증 대상으로 고른다. G1b/G2/GH에서 준비된 해당 경로만 비교하고 다음을 기록한다.

1. 모든 모델 호출의 cached/uncached 입력·출력·추론 usage와 도구 호출/결과, 별도 선택·검색·검증·재시도 비용. 제공자가 reasoning을 output에 포함하면 이중 합산하지 않는다.
2. native 실제 세션과 managed 실행의 cold/warm·짧은/긴 작업별 성공률·정책 준수·허위 PASS·사용자 교정·지연·검증 완료당 비용. managed는 같은 runtime·profile·권한·독립 검증으로 비교하고 미구현 전체 서비스의 성능을 실측으로 채우지 않는다.
3. 구성·설치·갱신·검사·지원의 유지 비용과 managed compute·저장·전송 비용. 매 요청 반복 컴파일과 긴 도구 출력이 절감을 상쇄하지 않는지 확인한다. 전환 비용은 일회 비용으로 따로 보고하고 예상 재사용에서 회수 가능한지 판단한다.

품질·권한·필수 검증을 통과하고 반복·holdout에서 순이득이 있는 범위만 옮긴다. 작은 plugin과 직접 소비가 같은 효과면 변경·유지 비용이 낮은 쪽을 채택한다. host-native만으로 더 나은 작업에는 추가 CodeForge workflow를 강제하지 않는다. 결과가 불확실하면 형태 우위·절감률을 확정하지 않는다. 기존 alias·사용자 설정·업데이트 경로의 호환을 검증한 뒤 단계적으로 전환한다.

### 프로젝트 특화 에이전트와 Smith의 유지 판단

개인 어시스턴트의 지속성은 기억·판단·결과의 연속성으로 만든다. 프로젝트별 역할 파일 생성은 선택적 실행 구성이다. 일반적인 ‘React 전문가’ 같은 역할은 신규 기본 추천에서 제외하는 방향으로 평가하고, 고유 도메인·실패 사례·반복 작업에 실제 이득이 있는 특화만 유지·고도화한다. 기존 사용자의 Smith 설정·원본·수정 파일은 §8의 전환 계약으로 보존한다.

현재 setup은 Smith 활성화 시 ‘사용 (권장)’으로 안내한다. 기존 사용자 변경에는 이미 근거 기반 분석과 일반론 생성 방지가 있으므로 보존한다. STATE+ACT의 정적 재사용과 권한 의도 보존은 별도 검증하며 역할 수·생성 파일 수를 효용으로 계산하지 않는다.

공개 연구도 조건부다. SkillsBench v4, SWE-Skills-Bench, WebDev 연구는 서로 다른 과제·모델의 skill/context 효과를 다루며 CodeForge의 개인화나 생성 agent를 직접 입증하지 않는다. 최신 모델에서 기존 구성이 필요한지 다시 평가한다. [SkillsBench v4](https://arxiv.org/abs/2602.12670v4), [SWE-Skills-Bench](https://arxiv.org/abs/2603.15401), [WebDev 연구](https://arxiv.org/abs/2608.23067), [harness 재평가](https://claude.com/resources/articles/harnessing-claudes-intelligence)

### 기본 profile 재사용과 agent 생성의 분리

프로젝트 profile은 검사 명령·수정 경계·고유 예외·자료 위치와 출처를 담는다. manifest·기존 지침이 충분하면 중복 파일을 만들지 않는다. 개인 선호·코드 사실·검사 기준·현재 작업 상태를 하나의 거대 profile로 합치지 않는다. 모델에는 권한과 유효성을 확인한 관련 내용만 전달한다.

| 비교 | 확인할 효과 |
|---|---|
| 기본 기억·지침·도구를 잘 설정한 native 실행 | 기존 도구만으로 달성하는 품질·개인화·비용 기준선 |
| 같은 기반 + 관련 프로젝트 지식·개인화 맥락 | 반복 탐색·교정·원치 않는 판단이 줄어드는지. 이미 전달한 정보는 추가 가치로 중복 계산하지 않음 |
| 같은 맥락 + 기본/영구/임시 subagent | 정보 자체와 위임·격리·별도 역할의 추가 효과를 분리. 단순 작업의 직접 실행과도 비교 |
| 반복 특수 작업용 도구·검사 구성 | 도메인 과제에서 일반 지침보다 추가 이득이 있는지 |

필수 정책·권한·수용 기준을 맞추고 모델·버전·작업·cold/warm 조건을 기록한다. 생성·갱신·선택·읽기·위임·인계·재시도·검증·유지 비용을 포함한다. 비용 이득은 `초기/갱신 비용 ÷ 실제 재사용 횟수 + 작업당 비용`으로 비교하고 token과 사람 시간을 근거 없이 더하지 않는다. 품질 향상에 비용을 더 쓴 선택은 절감으로 표시하지 않는다. 자동 적재·cache 효과와 지식 효과를 구분한다. [Codex 설정](https://learn.chatgpt.com/docs/customization/overview), [OpenAI caching](https://developers.openai.com/api/docs/guides/prompt-caching)

G0b는 한 흐름의 기준선과 비교 계획을 정하고 G1b/G2/G3에서 필요한 조합만 검증한다. 지식 추가만 유익하면 역할 생성은 줄인다. 이득 없는 신규 추천을 중단하더라도 기존 정의는 호환·지원 종료 절차를 따른다. 어시스턴트의 시간에 따른 개인화 효과는 §5에서 별도로 검증한다.

### 작업별 임시 에이전트 구성과 종료

기본은 주 실행 에이전트의 직접 수행이다. 독립적인 질문·산출물과 위임 이득이 있을 때, 기존 skill·STATE/ACT·근거에서 최소 지침을 조립해 native subagent에 전달한다. 별도 실행 설정이 필요한 경우에만 지원되는 임시 custom 정의를 쓴다. 매 작업마다 긴 페르소나나 새 agent 파일을 생성하지 않는다.

| 단계 | 필수 경계 |
|---|---|
| 구성 | 목표·제외 범위·허용 경로·정책·출처/revision·필요 도구·완료 조건·결과 형식. 부모 대화·전체 기억을 기본 복제하지 않음 |
| 실행 | Work/Attempt 또는 native ID 연결. 부모 권한·남은 시간/비용·동시성·취소를 따르며 하위 호출이 예산을 초기화하지 않음 |
| 회수 | 산출물·diff·실제 검사·미확인·usage·인계 근거를 회수. 자기 완료 선언이나 작성한 테스트만으로 최종 판정하지 않음 |
| 종료 | 성공·실패·취소·timeout·crash 뒤 잔여 실행과 action 결과를 확인. 자격증명·lease와 소유한 scratch/임시 정의만 정리 |
| 재개·재사용 | 권한과 source/revision을 재확인. 결과 불명 action 재실행 금지. 반복 이득이 검증된 구성만 승인된 범위에서 재사용 |

임시 정의를 정리해도 코드·검증 증거·미해결 상태와 허용된 코어 기억은 수명 정책에 따라 남는다. 기존 `.agents/agents/` 원본·`.claude/agents/` 출력·사용자 정의를 지우지 않는다. 파일 삭제로 이미 사용한 token이나 provider 기록이 지워지는 것은 아니다. 생성한 위임문은 사용자 선호나 승인으로 승격하지 않는다.

실행 중 discovery·권한·종료 방식은 호스트별로 확인한다. Claude의 session 범위 정의와 Codex의 기본/custom subagent는 동일 설치 절차로 가정하지 않는다. read-only 선언만으로 sandbox가 생기지 않으며 미지원 설정은 표시한다. [Claude subagents](https://code.claude.com/docs/en/sub-agents), [Codex subagents](https://learn.chatgpt.com/docs/agent-configuration/subagents)

### 메타포와 실행 책임

<details>
<summary>기존 이름과 구현 책임의 대응 — 호환성 참고</summary>

| 개념 | 보존할 의미와 경계 |
|---|---|
| Forge | 전체 작업·학습 환경. 저장소 수와 동일시하지 않음 |
| Blueprint | 사고 원칙과 정책 원문. 개인 판단 방식을 기계적 금지 목록으로 바꾸지 않음 |
| Smith | STATE+ACT 정적 컴파일을 선택 기능으로 보존. 근거 있는 지식·반복 작업 profile을 조합하고 실증된 경우 agent로 출력. 일반 역할 생성이 항상 유익하다고 가정하지 않으며 runtime router 역할은 맡기지 않음 |
| Anvil | `/start`, CLI, Inbox client, Voice 등 사람과의 접점. 같은 Work Compiler API를 사용 |
| Assayer | AC/BDD/테스트 작성자. 자신이 작성한 테스트의 통과 선언만으로 최종 verdict를 만들지 않음 |
| Bellows | 관찰·성찰용 이벤트. core ledger의 권위 상태 전이와 구분 |
| Whetstone | 별도 `coding-practice` 저장소의 사람 연습 기능. 본 서비스에 포함하지 않으며 개인화·규칙 후보 기능과 구분 |

Assayer가 제안한 테스트와 `RepositoryProfile`이 고정한 recipe를 구분한다. 독립 verifier는 후보와 분리된 실행 환경에서 고정 recipe·fixture·threshold로 검증한다. 기존 `forge whet`는 반복 패턴의 규칙 후보를 만드는 호환 명령으로 유지하고 채택 전 후보 상태를 보존한다. 이 명령과 GL의 개인화는 사람의 코딩 연습이나 `coding-practice` 설치를 요구하지 않는다.

</details>

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

- 공통 정책·검증 기준과 호스트/모델별 특화 원본은 기존 저장소에서 명시적으로 소유한다. 특화 원본에는 적용 조합·대체할 component ID·이유·평가 근거를 연결한다. 같은 component/조합에 활성 정본은 하나만 두며, 같은 문장만 허용한다는 뜻은 아니다. 배포 pack에 공통·특화 source revision·digest를 넣고 코어가 해당 버전을 pin한다. 코어에 수정 가능한 사본을 두지 않는다.
- `forge-status/v1`과 기존 관찰 계약은 당분간 기존 저장소가 소유한다. Work·Attempt·Approval·Evidence·Receipt와 core read model은 새 코어가 소유한다. legacy Hearth `sources v2`는 별도 계약으로 동결한다. 각 adapter는 지원 protocol·pack 범위를 선언하고 unknown field와 미지원 major를 구분한다.
- 기존 단독 사용 상태는 기존 `bin/forge` 호환 범위에서 유지한다. 코어 관리 Work는 코어만 쓴다. 같은 Work에 두 scheduler나 두 writer를 두지 않는다.
- `.claude/state`를 즉시 옮기지 않는다. 기존 소비자는 `bin/forge status --json`을 유지하고, 코어 관리 Work는 별도 ID와 versioned 조회 결과로 구분한다. 경로 이관은 consumer 호환 검증 후 별도 작업이다.
- 새 CLI의 실제 이름은 G0b에서 정해 기존 `forge`와의 충돌을 피한다. 내부 파일 경로를 저장소 간 API로 사용하지 않는다.
- core ledger는 managed 실행 사실의 정본이다. 프로젝트의 `progress.md`, ADR, Jira/GitHub와 외부 연결한 기존 개인 profile은 원본 위치를 유지하고 pointer·revision으로 연결한다. 서비스에서 새로 승인한 개인 기억과 재사용 교훈은 코어의 비공개 저장 기반이 정본을 소유한다. 동일 항목에 쓰기 권위를 둘로 두지 않으며 DecisionReceipt를 프로젝트 설계 결정으로 자동 승격하지 않는다.
- 공개 상태 API는 접근 규격을 뜻하며 인터넷 공개를 뜻하지 않는다. realm별 조회 권한·삭제·보존 기간을 정의한다. Glow/Hearth는 허용된 projection만 읽고 서로 다른 realm의 원문을 기본으로 합치지 않는다.

## 3. 멀티모델 지원의 정확한 범위

아래 직접 Codex/Claude 연결 표는 10월의 후보·미구현 상태를 보존한 것이다. 최신 controlled OMP fork 경로의 실제 provider/runtime 능력과 두 runtime conformance를 G0b/G3에서 확인하며, 과거 후보를 이미 구현된 통합으로 취급하지 않는다.

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

- `native`: 호스트가 직접 실행·검증하고 필요한 Blueprint·skills를 선택한다. 명확하고 가역적인 작은 작업의 기본 경로다. 선택적으로 개인화 코어의 기억·맥락을 연결할 수 있으며 이 연결만으로 managed Work를 만들지 않는다. 실행과 완료 판정은 호스트에 남는다.
- `managed`: 장기·다중 작업이나 독립 검증·복구가 필요한 목표를 명시적으로 core에 접수한다. Work 원장·Inbox·apply/readback을 사용한다.

core 설치만으로 모든 `/start`를 managed로 바꾸지 않는다. native→managed 전환은 scope·budget·Work ID를 고정하고, managed 실행의 장애·결과 불명 상태에서는 native로 자동 재실행하지 않는다. 같은 action의 중복을 조정한 뒤에만 새 Attempt를 연다.

### 호스트 pack과 실제 권한

재사용할 수 있는 정책·skill 절은 공유하되, host 전용 도구·trigger·경로 변환에 더해 절차·예시·본문의 특화도 허용한다. Claude용 본문을 기계적으로 변환하는 방식이 충분하다고 가정하지 않는다. Codex portable plugin은 루트 `skills/`를 지원하므로 `.agents/skills` 복제를 유일한 설치 방식으로 고정하지 않는다. lifecycle hooks가 포함된 pack은 신뢰 검토와 수동 desktop 설치가 필요한 경로로 구분한다. hook 없는 공개 pack과 로컬 자동화 pack의 배포 조건을 각각 검증한다. [공식 plugin 패키징](https://developers.openai.com/plugins/build/plugins)

Codex custom agent는 부모의 sandbox·approval·provider 설정을 상속한다. `.codex/agents/*.toml`만으로 별도 read-only sandbox를 만들 수 있다고 가정하지 않는다. 강한 권한 격리가 필요한 critic은 제한된 부모 session 또는 별도 프로세스에서 검증하고 MCP·API·plugin·hook의 부수효과도 함께 통제한다. [공식 Subagents 문서](https://learn.chatgpt.com/docs/agent-configuration/subagents)

compiler의 최소 descriptor는 stable component ID·기존 alias·trigger/negative trigger·필수 reference·capability·공통/특화 source digest·적용 host/model 조합·생성 파일 소유권을 담는다. 호스트 간 parity는 동일한 답변·실행 순서를 뜻하지 않는다. 핵심 정책·권한·검증 계약을 각각 통과하고 작업 품질·비용이 수용 범위인지 판정한다. 공식 문서 확인은 로컬 설치본의 conformance 통과를 대신하지 않는다.

### 자동 적재와 호스트·모델별 특화 — 2026-10-24 검토

저장소의 개수, 배포되는 파일의 개수, 모델이 실제로 받는 context는 별개다. 한 저장소에서 `CLAUDE.md`, `AGENTS.md`, 필요한 다른 호스트 파일과 모델별 템플릿을 만들 수 있다. 디스크에 여러 파일이 있다는 이유로 전부 주입하지 않는다. 지원 조합에 필요한 내용만 호스트가 직접 적재하도록 구성한다. 필수 정책은 다른 호스트 문서를 자연어로 읽으라는 지시 뒤에 숨기지 않고, 상세 참고 자료는 필요할 때 읽는다.

| 확인한 근거 | 설계에 적용할 판단 |
|---|---|
| Codex는 실행 시작에 `AGENTS.md` 계층을 적재하며 override·fallback·합산 크기 제한을 적용한다. fallback은 같은 디렉터리의 AGENTS 파일에 추가되는 파일이 아니다. [공식 지침 로딩](https://learn.chatgpt.com/docs/agent-configuration/agents-md) | Codex용 필수 계약을 자동 적재 경로에 직접 제공한다. `AGENTS.md`에서 `CLAUDE.md`를 읽으라는 지시만으로 동등 지원을 주장하지 않는다. |
| Claude는 `CLAUDE.md`와 `@` import를 적재한다. 최신 공식 문서는 조건부 `AGENTS.md` 지원도 설명하지만 버전·설정·CLAUDE 파일 존재에 따라 달라진다. 일반 문장의 읽기 지시는 파일을 실제로 열어야 효력이 생긴다. [공식 메모리 문서](https://code.claude.com/docs/en/memory) | native import와 모델의 후속 Read를 구분한다. 파일이 공존할 때의 우선순위·중복·누락을 지원 버전마다 검사한다. |
| Gemini CLI는 `GEMINI.md` 계층·import·파일명 설정을 제공한다. [공식 context 문서](https://geminicli.com/docs/cli/gemini-md/) | 다른 호스트도 자체 적재 방식을 사용한다. 조사 사례이며 Gemini 지원을 출시 범위에 추가한 것은 아니다. |
| 로컬 추론에서는 모델의 chat template와 tool-call 형식이 중요하다. 잘못된 제어 토큰은 성능을 저하시킬 수 있고, Qwen3는 권장 도구 형식을 별도로 설명한다. [Transformers](https://huggingface.co/docs/transformers/main/en/chat_templating), [Qwen](https://qwen.readthedocs.io/en/stable/framework/function_call.html) | 파일을 읽는 주체는 모델 가중치가 아니라 host/runtime다. 로컬 모델 지원은 파일명뿐 아니라 정확한 모델·tokenizer/template·서버·도구 parser·context 한도 조합으로 검증한다. Qwen3 사례를 모든 모델에 일반화하지 않는다. |

현재 작업트리의 `skills/start/SKILL.md`에는 `CLAUDE_PLUGIN_ROOT`·Claude 도구 전제가, `hooks/session-init.sh`에는 Claude SessionStart 주입 경로가 남아 있다. 이는 파일 참조 추가만으로 이식되지 않는 구체적 접점이다. 이번에는 읽기와 문서 개정만 했으며 호스트 실행·token 절감·동작 parity를 측정하지 않았다.

자동 적재는 읽기 도구 호출과 누락 가능성을 줄일 수 있지만, 적재한 본문도 입력 context와 비용을 사용한다. 간접 참조는 호출·출력·추가 추론을 유발할 수 있으나 선택적 문서까지 항상 적재하는 것보다 저렴할 수도 있다. cache 적중은 context 길이와 별개이며, 호스트·제공자별 실제 usage로 비교한다. [OpenAI caching](https://developers.openai.com/api/docs/guides/prompt-caching), [Claude Code caching](https://code.claude.com/docs/en/prompt-caching)

공개 연구도 단일 결론을 주지 않는다. 10개 저장소·124개 PR 연구는 시간·출력 토큰 감소를 보고했고, 다른 연구는 자동 생성 context의 비용 증가와 성공률 하락을 보고했다. 두 호스트를 비교한 후속 연구도 제한된 Python 과제에서 정확성 향상을 검출하지 못했으며 주입 채널 차이 등의 한계가 있다. 어떤 결과도 이 저장소의 공용본 또는 특화본 우위를 입증하지 않는다. [효율 연구](https://arxiv.org/html/2601.20404v1), [AGENTbench 연구](https://arxiv.org/html/2602.11988v1), [두 에이전트 비교](https://arxiv.org/html/2607.27250v1)

G0b는 비교할 조합·동일한 필수 정책·작업·판정 기준·반복·예산을 정한다. G1b/G3는 다음 비교를 실제 지원 호스트에서 수행한다. 파일을 더 만드는 선택에 GEPA나 GL 완료를 요구하지 않는다.

1. **적재 경로 비교:** 같은 필수 내용을 자연어 참조로 읽는 방식과 host-native 자동 적재 방식으로 비교한다. fresh session의 첫 도구 실행 전에 들어온 필수 계약, root/subdirectory·override·크기 상한·두 파일 공존·재개/압축 뒤 누락·중복을 확인한다. 질문·금지 action fixture로 실제 준수도 검사하며 모델의 자기 보고만으로 적재를 판정하지 않는다.
2. **본문 비교:** 호스트 기본 기능과 최소 정책만 쓰는 기준선, 공용 본문을 직접 적재하는 pack, host/model별로 절차·예시·도구 설명을 특화한 pack을 같은 작업·정책·도구 권한에서 비교한다. 한 호스트 안에서 효과를 먼저 판단해 모델 능력 차이를 파일 구조 효과로 계산하지 않는다.
3. **전체 비용 비교:** cold/warm 조건, 초기 입력·선택 skill·도구 schema·참조 Read·중복 입력, cached/uncached·출력/추론 token, 호출 수·재시도·지연·사용자 교정과 성공률을 기록한다. 검증 완료당 비용은 실패·재시도 비용까지 포함한다. 로컬 추론은 prefill·전체 시간·메모리·측정 가능한 자원비를 쓰며 API 비용 0을 총비용 0으로 간주하지 않는다. 관측 불가 항목은 unknown으로 남긴다.

고정 안전성·권한·검증 gate를 먼저 통과해야 한다. 그 안에서 공용본이 품질·비용 기준을 충족하면 재사용하고, 특화본의 이득이 반복·holdout 작업에서 재현되고 유지·회귀 검사 비용을 감당할 수 있으면 별도 원본을 채택한다. 특화는 단순한 설정 차이부터 독립 본문까지 허용한다. 차이가 불확실하면 결론을 유보하며 모든 조합에 대한 동작 보장을 선언하지 않는다. 저장소 분리는 자동 적재 성능의 해결책으로 가정하지 않고 배포·의존성·소유권과 변경 전파 비용까지 별도 평가한다.

### 공통 runtime 계약

`RuntimeAdapter`는 protocol version과 함께 invocation, events, start/cancel/resume, permission, identity, artifacts, recovery, usage의 능력·한계를 각각 보고한다. `unsupported`, `unknown`, `verified`를 구분한다. 실행 필수 능력이 없으면 그 작업을 배정하지 않는다.

`Attempt`에는 runtime ID·버전, provider·model의 요청값과 관측값, account alias, realm, capability digest, policy/pack digest, effort 요청값과 실제값, 시간·사용량·비용을 남긴다. 관측할 수 없는 값은 `unknown`이며 0원·성공으로 채우지 않는다. 자격증명 원문은 기록하지 않는다.

모델 라우팅 순서는 realm·데이터 허용 범위 → 필요한 capability → 위험·검증 가능성 → 작업별 품질 근거 → 비용·quota다. FAST/BALANCED/DEEP를 실제 모델 ID로 바꾸는 설정은 adapter에 두고 공통 정책에는 넣지 않는다. 미지원 effort를 조용히 무시하지 않는다. 강제할 수 없는 값은 advisory로 표시한다.

실패 시 다른 provider/model/account로 조용히 전환하지 않는다. 사전 허용된 변경만 새 Attempt로 처리하고, 허용 계정·데이터 정책·예산을 다시 검사하며 기존 부분 결과를 격리한다. fallback도 허용된 realm·endpoint를 유지하며 외부 작업을 중복 실행하지 않아야 한다. 초기 자동 routing 후보는 정적 규칙이며, BYOK·허용 OAuth·local endpoint와 managed 선택지의 조건은 최신 상세 정본 §6·9를 따른다.

다른 모델의 리뷰는 유용한 추가 관점이지만 테스트·정적 분석·readback을 대체하지 않는다. 모델 다수결이나 실행기의 자기 평가로 완료를 판정하지 않는다. OpenAI 호환 API를 받는다는 사실만으로 tool 사용·장기 복구·권한 처리까지 호환된다고 보지 않는다.

## 4. 기존 CodeForge에서 먼저 개선할 것

1. **복구 가능한 재기준화.** tracked diff의 binary patch 또는 private WIP snapshot과 미추적 파일의 실제 내용을 백업한다. digest는 복원 자료의 무결성 확인에 사용한다. 임시 checkout에서 복원하고 원본과 비교한 뒤 구현 worktree를 분기한다. 설치 cache·source·remote 기준선을 따로 기록한다.
2. **실행 안전성.** quality gate가 미실행·설정 오류·검사 실패를 PASS로 만들지 않는지 재현한다. cleanup의 경로 범위, 상태 동시 쓰기, Bellows 실제 payload·미확인 필드, handoff의 HEAD·dirty 재확인을 수리한다. 9월 지적을 현재 결함으로 단정하지 않고 fixture로 판별한다.
3. **호스트별 pack compiler.** 선택된 기본 workflow만 임시 디렉터리에 생성한다. 공통 정책과 logical reference에 host/model별 특화 원본을 합성해 해당 호스트의 자동 적재 파일·skill·manifest·tool mapping을 만든다. 전문을 공유할지 별도 작성할지는 §3의 비교로 정하고 필수 계약을 후속 Read에 의존시키지 않는다. 생성물에 cache 버전 절대경로를 넣지 않는다. 공통·특화 source·의존성·compiler hash로 Smith 출력의 신선도를 검사하고 기존 Must/Never·권한 의도가 보존되는지 비교한다.
4. **선택 설치와 갱신·제거.** 생성 파일 manifest, 충돌 preview, 사용자 파일 병합·보존, 재실행 idempotency, update·rollback·uninstall을 구현한다. 플러그인 관리자가 소유한 cache를 별도 updater로 고치지 않고 설치 경로별 갱신 주체를 하나로 둔다. 사용자 홈이나 기존 설정을 기본값으로 덮어쓰지 않는다. 갱신 다운로드·현재 세션 활성화·프로젝트 생성물 이관은 §8에 따라 각각 확인한다.
5. **호스트 검증.** Claude/Codex의 실제 instruction discovery, positive/negative trigger, 권한 제한, hook capability와 설치·제거를 확인한다. fixture 통과와 실제 호스트 통과를 별도로 기록한다.
6. **코어 연결.** `/start`와 새 CLI는 같은 Work Compiler 계약을 사용한다. managed Work의 재시도·원장·최종 판정은 core에 위임한다. 작은 native 작업과 core 미설치 상태도 회귀 검사한다. 기존 agent·명령 alias와 `status --json` v1 reader는 최소 두 릴리스 유지하고, 의미상 parity와 실제 복구를 확인한 뒤 폐기한다.
7. **기존 사용자 회귀.** `/start`, `/test`, `/handoff`, `/voice`의 입력·출력·승인 의미, Smith 프로젝트 정책, Glow golden, Voice hotkey·symlink·Hammerspoon 경로를 기록한다. agent 대량 삭제로 경량화를 시작하지 않고 hook 지연·false-pass·중복 절차부터 평가한다. 기존 Herdr·Orca 등 사용자 hook을 설치·제거 과정에서 보존한다.

### 현재 스킬과 서비스의 연결 검토

2026-10-24 작업트리의 스킬 본문·hook·CLI를 읽어 검토했다. 기존 사용자 개선이 포함된 source의 관찰이며 설치본·실호스트·새 core의 동작 증거는 아니다. 목록은 `rg --files skills -g 'SKILL.md'`로 확인한다. 현재 스킬은 대화 지침과 host 전용 명령을 포함하므로 재사용할 내용이 있다는 사실을 호출 가능한 공통 API가 이미 있다는 뜻으로 해석하지 않는다.

| 현재 접점 | 확인한 결합·공백 | 서비스 연결과 완료 조건 |
|---|---|---|
| `setup`, `smith-create-agent`, `smith-build` | 설정 생성·스타일 분석·선택 agent 생성이 onboarding에 연결 | 읽기 기반 환경 확인과 파일 생성/갱신 분리. 설치·변경 때만 필요한 생성 수행. 매 Work마다 전체 setup·profile 분석·agent 생성 금지 |
| `start` | 분석·구현·테스트·확인 질문·커밋/PR까지 묶은 local 흐름 | native 호환 진입점 유지. managed에서는 목표·범위·기존 승인을 Work로 전달. core가 전문을 다시 실행해 두 번째 scheduler·승인 루프를 만들지 않음 |
| `test`, `generate-test`, `e2e` | 검사 실행과 테스트 생성이 함께 라우팅되고 하위 수정 loop 존재. `test`는 경로 패턴, `start`는 행동 변화로 검사 선택 | 기존 검사·테스트 작성/수정·환경 준비를 구분. 행동·수용 기준과 고정 recipe 우선. 검사 부재를 자동 통과나 묵시적 생성으로 대체하지 않음 |
| `setup-test`, `setup-e2e` | 의존성 설치·설정·sample 생성 등 쓰기 동작 | 환경 변경 작업으로 별도 범위·예산 적용. verifier가 몰래 호출하거나 baseline 검사 환경을 바꾸지 않음. runner/lockfile·지원 stack 확인 |
| `research`, `debate`, `codex` | 조사·반증·교차 모델과 자체 호출/라운드 존재 | 독립 질문에 필요한 경우만 선택. managed 모델 호출은 허용 runtime/account·전체 budget에 귀속. bridge·자기 검토는 Evidence이며 verifier 통과를 대신하지 않음 |
| `figma-to-code`, `crawler` | Emotion 중심 template 또는 외부 탐색·connector 전제 | stack·source ACL·도구가 맞는 선택 capability. URL·주석의 링크만으로 새 인증·외부 전송을 허용하지 않음. 미지원 표시, alpha 범위 자동 확대 금지 |
| `handoff` | progress 문서·clipboard·다음 세션 지침 | native 보존. managed는 checkpoint·질문/승인 revision·미확정 action을 원장에서 복원하며 clipboard·수동 kickoff에 의존하지 않음 |
| `forge-status`, `stats`, Bellows/Glow | legacy 상태와 호출 빈도·관찰 event 표시 | native v1과 managed projection을 ID/source로 구분. 호출 횟수는 효과·청구액이 아님. runtime/worker 계량과 반영 receipt로 결과·비용 표시 |
| `cleanup` | glob으로 test-results·report·임시 파일을 지우는 지침 | managed에 그대로 호출하지 않음. 소유 artifact와 보존 정책으로 정리하고 실패 trace·검사 증거·재개 자료를 먼저 보존. native 안전성은 G1a에서 수리 |
| `voice`, `setup-channels`, `setup-agent-teams` | 장비·host 설정, 자동 입력, 알림/팀 기능 | 설치와 요청 입력 adapter 분리. 일반 실행이 STT 설치·daemon·팀 구성을 유발하지 않음. 텍스트·음성·승인 화면은 같은 작업/권한 계약에 연결 |
| `docs-polish`, `startup-validator` | 문서 표현 또는 사업 가설 검토 | 필요한 산출물에서만 선택. 일반 작업의 필수 선행 분석이나 서비스 최종 판정으로 사용하지 않음 |

선택한 스킬의 최소 계약은 입력·지원 환경·source/version, 읽기/쓰기/네트워크 효과, 필요한 도구·권한, 산출물·검사 근거, 잔여 budget·취소/재개 의미다. 소수 기능의 fixture로 먼저 연결하며 전체 catalog의 영구 SDK나 범용 workflow DSL부터 만들지 않는다. agent가 기능과 다음 행동을 선택하고 host/core는 실제 허용 범위와 상태 전이를 검사한다. 설명·파일 경로만 같다는 이유로 다른 host에서도 같은 capability가 있다고 판단하지 않는다.

### profile의 원본과 수명

| 현재 자료 | 맡길 책임과 갱신 경계 |
|---|---|
| `.claude/profile.json`, manifest·lockfile | stack/환경 설정의 기존 source. 프로젝트 사실은 manifest와 대조하고 생성 file 소유권 기록 |
| `.candidate/profile.md`와 기존 승인 개인 profile | 코딩 선호·판단 기준. 새 추론을 파일 존재만으로 승인 취급하지 않으며 강제 정책 우회 금지 |
| AGENTS/CLAUDE·프로젝트 정책·ADR | 프로젝트 최소 계약과 근거. 개인 선호나 agent 정의에 전체 복제하지 않음 |
| `RepositoryProfile`·`VerificationRecipe` | 해당 실행의 환경·명령·독립 검사 기준을 revision으로 고정. 기존 profile 대체 사본을 무조건 만들지 않음 |
| `ContextEnvelope`·임시 agent 구성 | 권한 검사 뒤 선택한 실제 전달 내용. 작업에서 사용하고 근거·보존 정책에 따라 인계/정리 |

이를 새 거대 profile 파일로 합치지 않는다. 사실·선호·검사 기준·일회 상태를 구분하고 변경 source에 관련된 구성만 무효화한다. 현재 candidate-profile 지침의 선호 우선순위와 누락 시 질문 규칙은 향후 강제 정책 우선·가역적 선택의 자율 판단 계약에 맞춰 검사할 대상이다. 이번 검토에서는 원본 profile·rules·스킬을 변경하지 않았다.

`agents/`는 직접 편집하되 프로젝트 Smith 출력 `.claude/agents/`는 수정하지 않는다. 기존 `rules/` 삭제와 `presets/` schema 변경은 이 계획 범위에 넣지 않는다.

## 5. 새 코어의 첫 완성 범위

첫 내부 실증은 공개 코드 저장소 하나에서 다음 흐름을 끝까지 수행한다. 과거 GH 완전관리형 alpha는 후속 제공 형태의 후보로 유지하며 초기 확정 기본값으로 삼지 않는다. 초기 연결·고객 제공 조건은 최신 상세 정본 §6·8을 따른다. 로컬 개발 실증을 고객의 설치 의무로 해석하지 않는다. 아래는 코드 변경 작업의 계약 경계이며 스킬 호출의 고정 순서가 아니다.

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

### 터미널·웹·모바일의 동일 작업 접근

관리형 서비스에서도 기존처럼 터미널에서 대화하고 코드 작업을 할 수 있어야 한다. native/managed는 작업 관리 방식이며 terminal/web/mobile은 사용자 접점이다. 터미널이라는 이유로 native로 제한하거나 managed 사용을 위해 웹으로 이동하도록 강제하지 않는다. CLI와 지원 host 연동을 통해 같은 Work의 요청·진행·질문 답변·승인·취소·재개를 제공한다. 터미널에서 시작해 모바일로 답하고 웹에서 결과를 확인해도 Work ID·권한·예산·검증 결과는 이어진다.

동일 작업 조회·이어가기, 동시 응답·stale 승인·연결 중단 뒤 복구와 중복 실행 방지는 유지할 수용 조건이다. 최신 상세 정본 §3·8에 따라 G2는 ANSI TUI와 지원 Tern 향상, 로컬 web chat·반응형 질문/승인을 연결하고, G3는 두 runtime·두 pack과 지원 조합을 검증한다. 원격 모바일·상시 authority/worker는 G4에서 검증한다. 과거 GH라는 이름만으로 원격 제공 gate를 앞당기지 않는다. 터미널 client 연결과 사용자 로컬 장비의 원격 worker 제어는 별도 범위다. 기존 세션 편입은 현재 변경·기발생 action을 확인해 명시적으로 연결하며 모든 세션을 자동 편입하지 않는다.

### 정보 구조 선택과 TUI·원격 우선 순서 — 2026-11-07

구현 계획을 단계적으로 확정하는 첫 실제 결정에서 사용자는 **데스크톱의 ‘작업 진행 중’ 기본 구조로 결과 작업대 중심을 선택했다.** 홈페이지·문서·기타 산출물이 중앙의 주인공이고, 대화는 결과를 지시하는 열고 닫는 보조 영역이다. 작업 탐색은 얇게 두고 질문·변경·검증·승인은 해당 결과와 연결해 접근한다.

첫 요청 순간에는 비개발자의 쉬운 채팅 진입점을 유지한다. 모바일은 채팅을 기본으로 결과·검토로 이동한다. 개발자 TUI는 같은 Work의 의미·상태·행동을 키보드로 제공하며 웹 레이아웃을 복제하지 않는다. 이 선택으로 기존 Work 계약이나 접점별 검증 gate를 완료 처리하지 않는다.

**승인 범위는 정보 구조 방향뿐이다.** 색·폰트·세부 레이아웃·구현·실제 prototype은 승인되지 않았다. 첫 시안은 사용자가 ‘완전 클로드 디자인 그 자체’라고 거절하고 ‘그냥 멈춰’라고 중단했으며, 여전히 기각·중단 상태로 재사용 금지다. 자동 재개하지 않는다. 결과 작업대 선택을 ‘다크 3단 패널이 곧 차별성’이라는 결론으로 바꾸지 않는다. CodeForge의 대장간 메타포와 제품 고유성을 보존한다. 기각 시안의 HTML/CSS/JS·디자인 명세·스크린샷·runner/browser tooling·로컬 로그는 이번 기획 문서에 포함하지 않는다.

두 번째 실제 선택에서 사용자는 **개발자 TUI와 원격 사용 우선**을 명시적으로 선택했다. 웹·모바일과 결과 작업대 방향은 후속 단계로 유지한다. 웹의 필수 정보·작업 흐름, 시각 방향·실제 레퍼런스·작은 와이어프레임 검토도 후속이며 첫 Core 구현의 선행 조건이 아니다.

최초 수직 흐름 목표는 **TUI 요청 → 실제 실행 → 검증 → 필요한 승인 → 반영 후 확인(readback) → 원격 접속을 끊었다 다시 연결해 같은 Work 확인**이다. TUI는 authoritative 작업 상태의 소유자가 아니며 화면 단절과 작업 수명을 분리한다. 실행 계약은 상태·action·검증·승인·반영 후 readback과 접속 단절/재접속/취소/복구를 포함한다. 중단 후 결과가 불명확한 외부 작업을 무조건 재시도·재반영하지 않고 실제 상태를 확인해 중복 실행을 막는다.

초기 원격은 사용자 자신이 관리하는 머신·서버에 SSH로 접속하는 경로를 우선 검토한다. 이는 공개 인터넷용 다중 tenant SaaS·격리 완성이나 G4 통과를 뜻하지 않는다. 모델 credential은 보호된 실행 환경에 남기고 메신저로 받지 않는다. 모델·계정 silent fallback 금지와 사용자별 격리 원칙을 보존한다.

텔레그램 등은 후속 접점으로 알림·상태조회·간단 요청부터 검토한다. 게시·삭제·비용 발생 승인은 사용자·권한·대상 버전·유효성·중복 방지 경계가 갖춰진 뒤 검토한다. 처음부터 원격 shell·포괄 승인 권한을 주지 않으며 텔레그램 구현·새 bot 생성은 현재 승인 범위가 아니다. 네이티브 데스크톱·모바일 앱은 OS 통합·알림·기기 기능의 실제 필요를 확인한 뒤 선택하며 첫 구현 범위에서 제외한다.

**다음 한 단계는** 실제 OMP에서 재사용할 범위와 첫 실행 환경을 읽기 전용으로 확인하고, 위 최초 수직 흐름을 위한 G0b 작업 하나의 실행 계약을 좁히는 것이다. 저장소·언어·기술 스택·controlled OMP fork 실제 변경 범위·파일 경로·첫 실행 환경은 코드 조사 전이므로 미확정이다. 구현 착수·실증 완료나 새 디자인·프로토타입 재개를 뜻하지 않으며 기존 상세 설계 전체를 여기서 다시 복제하지 않는다.

### 자율 선택과 서비스 집행의 연결

managed에서 직접 실행한다는 것은 서브에이전트 없이 주 실행 agent가 일한다는 뜻이다. 실행 agent 수와 관계없이 해당 Work의 권한·예산·원장·검증 계약을 적용한다.

설정/배포는 작업 실행과 별도 수명주기다. 이미 준비된 환경에서는 목표 → 허용된 환경 확인 → 필요한 근거 선택 → agent의 행동 선택·실행·관찰 → 수용 조건 확인으로 진행한다. 검토·기존 검사 실행·코드 변경·테스트 환경 설치를 같은 요청으로 취급하지 않는다. 사용자가 요청한 산출물까지만 수행하며 PR·배포·학습 승격은 필요한 권한과 별도 조건이 있을 때 이어진다.

| 경계 | agent가 정할 것 | host/core가 확인·기록할 것 |
|---|---|---|
| 요청 접수 | 목표·산출물·불확실성 해석, 필요한 질문만 선택 | 인증된 대상 realm/repo, 요청 ID와 mode. native/managed는 명시하며 `--auto`만으로 전환하지 않음 |
| 환경·근거 | 존재하는 manifest·가까운 패턴부터 읽고 추가 profile/skill 선택 | source ACL·허용 도구·지원 stack·필수 정책·사용 버전. 필수 능력 부재는 blocked/unavailable |
| 계획·실행 | 직접 작업·스킬·임시 subagent·새 판별 실험을 필요에 따라 조합 | 허용 경로·외부 효과·lease·잔여 budget. native는 host, managed는 core가 실행 상태를 소유 |
| 질문·범위 조정 | 결과를 바꿀 미해결 사항만 질문. 가역적 선택은 근거로 판단 | 해당 요청 revision으로 답변 적용. 대기 노드만 정지. 기존 유효 승인을 재사용하며 변경 범위만 다시 확인 |
| 검사·후보 확정 | 행동·수용 기준에 맞는 검사 제안, 오류의 새 가설과 최소 수정 | 고정된 recipe의 독립 실행, 실제 tested SHA/digest·미실행/오류 보존. 검사 작성과 최종 verdict 분리 |
| 반영·확인 | 승인 대상으로 diff·증거·미확인을 제시 | action/대상/base/artifact에 묶인 승인, 별도 apply 권한, 중복 방지와 readback. 준비 worker가 직접 공개/배포하지 않음 |
| 보고·인계 | 결과·미해결·다음 행동 설명 | 실제 수행·증거·승인/반영 상태·비용의 receipt/projection. 실패·취소도 보존하며 적용 전 후보를 적용 완료라 표시하지 않음 |

native는 core 없이 필요한 스킬을 선택해 수행한다. 이후 managed로 맡길 때는 범위·현재 변경·이미 발생한 action을 확인하고 Work를 만든다. 미확정 action을 무시한 이중 실행이나 local 성공을 소급해 managed 검증 완료로 승격하지 않는다. managed에서는 같은 요청에 하나의 Work 감독·재시도 권위만 두고 agent의 작업 계획을 그 안에서 실행한다. core의 durable scheduling은 프로세스·질문·승인·복구를 관리하며 스킬을 고정 순서로 강제하는 별도 agent planner가 아니다.

현재 `/start`의 checkpoint, `/test`의 실행 확인, E2E의 실패 처리, Stop hook을 연달아 독립 관문으로 붙이지 않는다. 단일 감독자가 상위 RunPolicy의 남은 시간·비용·검사/시도 상한을 하위 호출에 배정한다. 하위의 기존 상한은 추가 제한이며 부모의 budget을 초기화하지 않는다. 새 가설이나 사용자 답변도 전체 budget을 자동 갱신하지 않는다. 과제 내 테스트 수정은 같은 Work의 새 candidate/evidence로 이어 가며 `/start`를 재귀 호출해 새 승인·원장을 만들지 않는다.

`--plan-only`는 구현하지 않고 계획을 반환한다. managed의 `--skip-test`는 필수 검증을 없애는 권한이 아니며 recipe와 충돌하면 미검증·차단 상태를 반환한다. `test` 요청에서 환경 부재가 발견돼도 설치·생성으로 자동 확대하지 않는다. 필요하면 효과·비용을 드러내 범위를 추가하고 해당 검사 기준을 새 revision으로 고정한다.

mutating lint/format hook까지 끝난 candidate를 고정한 뒤 독립 verifier를 실행한다. verifier 환경에서는 테스트 작성·자동 수리·설정 변경 hook을 비활성화하거나 통제한다. Stop hook 결과는 host가 관찰한 증거로 연결하고 동일 SHA·환경·recipe의 검사를 목적 없이 중복 실행하지 않는다. 최종 검사 뒤 쓰기가 발생하면 그 후보의 검증과 승인을 무효화해 다시 확인한다. caller·하위 agent·hook에서 같은 사용량을 중복 청구하지 않도록 실행 ID와 실제 계량 근거를 대조한다.

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
| 기존 검사 요청인데 runner가 없음 | unavailable, 자동 패키지 설치·테스트 생성·허위 PASS 없음 |
| 생성/수정한 테스트만 성공 | 고정 recipe와 구분한 추가 증거로 보존. evaluator 약화나 필수 검사 생략을 통과로 바꾸지 않음 |
| 하위 E2E·agent·hook의 반복 실행 | 상위 budget을 공유하며 하위 재진입·사용자 답변으로 상한이 초기화되지 않음 |
| 검사 뒤 lint/format hook이 후보 변경 | tested digest 불일치로 기존 후보의 검증·승인 무효화 |
| handoff/cleanup 중 질문·미확정 action·실패 trace 존재 | 인계와 재인가 후 복구, 결과 확인 전 재실행 금지, 보존 대상 증거 정리 금지 |
| 텍스트·음성·모바일에서 같은 요청/승인 재전송 | 같은 작업/질문/action 식별자로 조정. 중복 생성·반영·승인 재사용 차단 |

이 fixture는 판정기의 정확성을 검증한다. G2는 별도의 공개 저장소 profile에서도 결함 또는 병목 개선 한 건을 재현하고 correctness·보조 지표 비퇴행을 입증해야 한다. 최초 실제 profile 후보는 안전성 검사를 가진 CodeForge 고정본이며 G0b에서 명령·환경·기준 SHA를 확정한다. 처리 속도·token·비용의 개선 주장은 해당 비교 자료가 있을 때만 한다.

### 개인화 코어와 공통 기억 기반

여러 지원 모델이 같은 개인화 기반을 읽고 작업 근거를 돌려준다. ‘하나의 베이스 저장소’는 사용자·영역별 정본을 일관되게 관리한다는 뜻이며 공개 Git 저장소나 모든 개인/회사 자료를 합친 단일 DB를 뜻하지 않는다. 저장 방식은 G0b에서 정하되 기존 개인 profile과 프로젝트 문서의 정본을 복제하지 않는다. 모델별 기억은 허용된 입력 후보 또는 버전 있는 전달본이며 코어와 경쟁하는 정본으로 만들지 않는다. 제공자 자체 기억과 코어 지시가 함께 적재되면 중복·충돌·우선순위를 관측하고, 통제 불가능한 조합은 일관성 검증 완료로 표시하지 않는다. 제공자가 기록을 영구 보존·자동 동기화해 준다고 가정하지 않는다.

| 코어가 관리할 것 | 원본·수명·사용 경계 |
|---|---|
| 사용자 판단 기준 | 명시적 선호·이유·적용 범위·승인 근거·버전·수정/철회. 사용자 기억이 작업 실행 권한을 만들지 않음 |
| 프로젝트 지식 | 정책·도메인 사실·검사 recipe와 원본 포인터. 변하는 코드·환경은 사용 시 재확인 |
| 작업 경험 | 목표·관련 맥락·행동 요약·검사 결과·교정·한계. 원문 전체와 장기 기억의 보존을 구분 |
| 재사용할 교훈 | 근거가 있는 반성 후보와 적용 조건·반례·검증 상태. 모델의 추측과 확인 사실을 구분 |
| 진행 중인 일 | Work/Attempt·질문·승인·미확정 action과 복구 근거. 개인 성향이나 영구 선호로 저장하지 않음 |

코어는 현재 의도 → 권한 확인 → 관련 기억·근거 선택 → 사용자 기준과 모델별 절차를 반영한 지시 구성 → 실행으로 연결한다. 공통 의도·개인 기준은 보존하고 문법·예시·도구 설명은 호스트에 맞춘다. 매 요청에 별도 생성형 router를 강제하지 않으며 작은 조립부터 비교한다. 실제 전달한 source ID·URI/revision/digest·우선순위·locale·realm을 `ContextEnvelope`에 기록한다. 평가하지 않은 언어는 원문을 유지하고 고급 언어 최적화는 후속 검증한다.

명시적인 ‘기억해 줘’는 지정한 허용 범위에 반영하고 같은 요청을 재승인받지 않는다. 추정 선호는 후보로 남기거나 사전 허용된 좁은 갱신 정책을 따른다. 일회 예외·장기 변경·강제 정책을 구분하고 충돌·동시 수정·철회를 처리한다. 모델별 cache·전달본은 revision으로 무효화하며 철회 뒤 새 행동 전에 관련 내용을 재확인한다. 실행 결과와 원문을 소급해 없던 일로 만들지는 않는다.

기억 조회·수정·삭제·내보내기·끄기를 G2/GH에 포함한다. 기존 승인 원본은 선택 연결하고 `coding-practice` 없이도 동작한다. 원문 최소 수집, realm별 권한·redaction·retention/GC·백업·복원·삭제 정책을 첫 managed 결합 시험 전에 정한다. 공유 기반 장애 때 오래된 권한·철회 기억으로 계속 실행하지 않는다. 영향받는 작업만 대기하거나 명시적인 기억 없는 경로로 전환하고 제한을 알린다.

### Reflexion과 개인화 검증

Reflexion은 작업 피드백을 언어로 정리해 이후 시도의 맥락에 사용하는 방식이며 모델 가중치 갱신을 전제하지 않는다. 원 논문의 과제 성과는 장기 초개인화나 여러 모델의 동일 결과를 입증하지 않는다. [Reflexion 원 논문](https://arxiv.org/abs/2303.11366)

코어에는 **실행 → 외부 검사·사용자 교정 → 짧은 반성 후보 → 조건부 재적용 → 다음 결과 확인**을 작은 경계부터 도입한다. 반성은 관측 결과·원인 가설·다음 변경·적용 조건·근거를 담고 내부 사고 과정 전체를 수집하지 않는다. 같은 실패·재교정 등 의미 있는 신호에서만 실행하며 반성·재시도 비용도 부모 예산에 포함한다. Actor·Evaluator·Reflection은 책임 구분이며 세 모델을 상시 호출하라는 뜻이 아니다.

현재 작업의 수정 가설은 바로 시험할 수 있다. 장기 교훈으로 재사용할 때는 근거·권한·적용 범위와 독립 검증 또는 사용자 확인을 요구한다. 사용자 의도와 무관한 결과를 선호로 추론하지 않고, ‘테스트를 없애니 통과했다’는 반성을 채택하지 않는다. 검증되지 않은 후보를 사실로 누적하거나 여러 모델의 동의를 정확성으로 간주하지 않는다. 실패하면 후보를 수정·철회하고 재사용 기록에서 영향을 추적한다.

G2는 명시적 기억·다음 작업 적용·수정/철회와 근거 기반 반성 한 흐름을 실증한다. GH는 고객별 기억 관리와 동일 작업 접근을, G3는 같은 승인 기억을 Claude/Codex 양쪽에 전달했을 때 판단 기준·제약이 유지되는지 검증한다. GL은 이 기반 위에서 지침·검색·반성 전략을 장기 평가하고 자동 최적화한다. 기본 개인화를 GL까지 미루지 않는다.

개인화 평가는 기억 기능까지 잘 설정한 native+CI, CodeForge의 개인화 켬/끔, 단순 피드백 재전달 대비 Reflexion 후보를 비교한다. 허용된 과거 정보를 동등하게 제공하고 초기·갱신·검색·반성·실행·검증 비용을 포함한다. 과거 기억으로 이후의 새로운 과제를 수행하며 미래 정답·교정의 유입과 동일 과제 암기를 차단한다. 모델 버전·난도·정보량 변화와 개인화 효과를 분리한다.

필수 회귀 사례는 잘못된 교훈, 일회 예외, 기준 변경·삭제, 다른 프로젝트·realm, 동시 기억 수정, 오프라인 전달본, 모델 교체다. 품질·정책 비퇴행을 지키면서 반복 설명·교정·불필요한 질문·원치 않는 선택·수용 결과당 검토/재작업 시간이 줄어드는지 본다. 효과가 없거나 악화되면 해당 기억·전략만 되돌린다. 기간·저장량·자기평가 점수를 발전의 증거로 삼지 않는다.

### 독립 검증과 최적화

검사 결과는 `pass`, `fail`, `measured`, `error`, `not_run`, `unavailable`, `blocked`, `n_a`를 보존한다. 필수 검사가 실행되지 않았으면 검증 완료가 아니다. 검증 명령은 저장소 profile이 제공하고, 모델이 같은 변경에서 test·threshold·fixture·CI를 약화했으면 자동 통과시키지 않는다.

baseline과 candidate는 같은 환경·fixture·도구 버전에서 비교한다. 기능 비퇴행을 전제로 주 지표 개선과 보조 지표 비퇴행을 확인한다. 임계값·반복 횟수는 실행 전에 profile에 고정한다. 비용은 단순 token 감소가 아니라 검증 완료당 비용·재시도·사람 수정 시간과 함께 평가한다. 비용이 미확인이면 비용 개선을 주장하지 않는다.

host-native 기준선, 현재 full harness 고정본, 얇은 공통 pack, host/model별 특화 pack과 작업별 skill 추가를 같은 작업에서 비교한다. §3에 따라 적재 경로와 본문 효과를 나눠 측정하고 Claude/Codex별 성공·정책 준수·실제 검증·사용자 교정·불필요한 질문·범위 이탈·시간·검증 완료당 총비용으로 채택한다. 개인 사고모델은 사람이 판별한 선택 사례와 holdout 작업으로 평가한다. 희귀한 안전 정책은 사용 빈도가 낮다는 이유로 제거하지 않는다.

첫 수직 단면 뒤 성격이 다른 두 번째 공개 저장소를 같은 계약으로 검증한다. 예를 들어 shell 중심 도구와 테스트 가능한 애플리케이션을 선택한다. 두 저장소를 통과하기 전에 첫 profile의 편의를 범용 SDK로 고정하지 않는다.

### 승인과 실제 반영

준비 worker와 apply executor의 권한을 분리한다. 승인은 artifact digest·base SHA·policy digest·target·account·action·만료 시각에 묶고, 변경되면 재승인한다. 승인된 범위만 실행하고 결과를 readback으로 확인한다. Goal 생성이나 구현 승인만으로 push·PR·merge·배포 권한이 생기지 않는다.

반응형 Inbox에는 후보 diff·검사·미확인·비용, 질문과 실제 반영 action을 구분해 보여 준다. G2는 단일 public realm의 내부 실증과 다른 realm 거부 검사를 포함한다. 고객의 터미널·웹·모바일 접근은 GH의 인증·tenant·전송 검증을 통과한 관리형 환경에서 제공한다. G4는 이후 개인 로컬·조직 환경 연결을 뜻하며, GH로 회사 컴퓨터의 원격 제어 권한이 생기지 않는다. 각 realm의 credential·원문·원장은 분리한다.

### 개인화와 정보 경계

검색 전에 realm·source ACL·기기·작업 권한을 검사하고, 허용 자료 안에서 관련성·최신성·중복·토큰 예산으로 선택한다. 회사 원문을 개인 세션으로 읽은 뒤 마스킹하는 방식은 금지한다. 업무 존재 자체도 기본 비공개이며, 조직이 별도로 승인한 최소 상태 projection만 대상·TTL·철회 정책에 따라 개인 화면에 표시할 수 있다. 요약·임베딩도 원본 분류를 상속한다.

직접 요청, 에이전트의 위임 프롬프트, 실제 전달문, 독립 검증 결과, 사용자 교정을 Work/Attempt로 연결한다. 원문 장기 보관·학습은 별도 동의와 realm 정책을 따른다. 반성 후보와 실행 에이전트 작성문을 사용자 선호로 자동 승격하지 않는다. 기억의 수명과 지시 생성기 최적화는 구분한다. 상세 데이터 계약·공격 사례·삭제 범위는 서비스 상세 계획 §3~5를 따른다.

기존 계획 승인·core의 Decision/Approval·host의 도구 승인을 같은 화면에서 관련 요청으로 묶고 이미 허용된 범위를 반복 질문하지 않는다. 한 종류의 승인이 다른 권한을 만들지는 않는다. Voice도 같은 질문·action revision을 사용하며 잘못 인식한 응답이나 stale 버전으로 실행하지 않는다. 관리형 음성은 GH, 기존 로컬 host 연동은 G3에서 각각 검증한다.

### 마이크 음성 지시의 서비스 연결

아래 GH/STT는 10월에 제안한 후속 선택 기능의 상세 요구다. 최신 상세 정본 §8에 따라 voice의 가치·접근성·비용 증거와 별도 gate가 필요하며, 새 음성 기능을 G2/G3의 일괄 필수 조건으로 두지 않는다. 기존 로컬 Voice의 호환·회귀 요구는 유지한다.

사용자가 말한 ‘마이크’는 Voice/STT 입력으로 확인했다. 현재 `voice` 스킬·`forge-voice.sh`·Lua 매크로는 macOS 녹음·로컬 Whisper·clipboard/paste·선택적 자동 제출 경로다. 웹·모바일 서비스에는 장비 설치나 terminal 매크로를 전제하지 않고 별도 입력 adapter를 둔다. 목표·후속 지시·질문 답변을 텍스트와 같은 인증된 요청에 연결한다.

GH의 첫 음성 경로는 누르고 녹음 → 전사 → 텍스트 확인/수정 → 전송이다. 짧은 전사 결과를 기존 작업의 요청/질문 ID에 붙이며 음성마다 새 Work를 만들지 않는다. live 대화·상시 wake word·TTS 응답은 후속 선택 기능이고 텍스트 입력·붙여넣기는 항상 제공한다. 마이크 거부·녹음 중단·지원되지 않는 browser·업로드/STT 실패가 agent 실행으로 이어지지 않게 한다. 브라우저 녹음은 secure context와 장치 권한을 필요로 하며 실제 지원 조합을 시험한다. [MDN microphone 권한](https://developer.mozilla.org/en-US/docs/Web/API/MediaDevices/getUserMedia)

STT는 로컬/서버/허용 공급자 중 환경·realm·동의·지연·원가에 맞춰 선택한다. 관리형 서버나 외부 STT로 음성을 보내는 경로를 로컬 처리로 설명하지 않는다. 모델 제공자의 전사 API는 구현 후보이며 특정 모델·요금·정확도를 고정하지 않는다. 기존 로컬 Voice는 별도 접근성 경로로 보존하고 기존 자동 제출 설정을 웹의 승인 정책으로 옮기지 않는다. [공식 전사 API 안내](https://developers.openai.com/api/docs/guides/speech-to-text)

질문 답변과 실제 반영 승인을 구분한다. ‘네’라는 전사만으로 push·merge·배포하지 않고 인증된 대상 작업·질문/action·artifact/version·유효 승인 범위에 응답을 묶는다. 음성 승인 제공 시 읽거나 표시한 정확한 대상과 사용자 확인을 연결하고 재생·중복 응답·다른 작업·오인식·만료를 검사한다. 전사는 입력 수단이며 새로운 권한이나 화자 인증을 만들지 않는다.

원본 음성은 기본 최소 보존하고 임시 업로드의 만료·삭제, 전사문·선택적 후처리의 동의/retention을 구분한다. 발화 내용·후처리 문장을 자동 영구 선호로 승격하지 않는다. STT·후처리·전송/저장·재시도 비용을 Work 또는 별도 입력 계량에 포함하되 이중 합산하지 않는다. GH에서는 첫 요청·후속 지시·질문 답변과 전사 수정/취소·중복을 시험하고, 음성으로 실제 반영을 승인하는 기능은 위 binding/재인증 gate를 통과한 지원 조합에만 연다. G3는 기존 로컬 hotkey·paste·수동 입력 회귀를 확인한다.

### Family 연결과 Hearth 재평가

- **Glow**: 현재 session-local HUD를 보존하고 managed projection은 선택 기능으로 연결한다. 기존 v1 reader가 있는 지원 버전에는 consumer-first 전환을 적용한다. reader가 제거된 버전에는 adapter를 별도로 합의하고 테스트하며 기존 기능으로 가정하지 않는다. 명시적으로 해석한 실행 경로를 사용하고 cache의 가장 높은 버전을 임의 선택하지 않는다. 조회 실패를 PASS나 0원으로 표시하지 않는다.
- **Hearth**: G0에서 백업·동결하고 초기 출시 필수 항목에서 제외한다. core 비관리 프로젝트까지 모으는 Markdown 보고서 수요가 있을 때 재평가한다. 유지 시 core projection과 legacy progress adapter를 읽고 source·관측 시각을 표시한다. 수동 `done`·checkbox를 검증 완료로 승격하지 않는다.
- **Hearth 활성화 조건**: sources/preset schema, Node/Python 공통 fixture 또는 단일 normalized read model, shell 보간 제거, project/preset ID와 출력 경로 검증, 명시적 demo 모드, realm별 config/output, 비파괴 installer를 갖춘다. 현재 옛 설치 URL·누락 schema·repo 내부 생성물 경로를 수리한 뒤 설치한다.
- **Hearth 거취**: 다중 source·portable Markdown의 실사용이 있으면 독립 유지한다. core 데이터만 쓰고 출력만 필요하면 core report로 흡수한다. 수요가 없으면 이력·복원 가능한 archive를 보존한다. 지금 즉시 병합·삭제하지 않는다.
- **Flow**: 비즈니스 policy/spec/TC는 선택 capability로 평가한다. legacy workflow state는 importer 또는 외부 참조로 읽고 같은 managed Work에 두 원장·scheduler를 붙이지 않는다. `flow sync`의 cache 경로 결합을 새 구조에 이식하지 않는다.
- **Herdr**: 관찰과 mutating capability를 별도로 선언한다. pane/agent prompt·worktree 생성/제거의 권한·취소·결과 확인을 검사하며 terminal의 `done`을 Work 완료로 사용하지 않는다. Herdr 미설치 상태의 direct runtime도 지원한다.
- **Voice**: 기존 경로를 새 설치·smoke test 전에 이동하지 않는다. local 장비 연동과 GH의 웹·모바일 입력을 구분하고 Anvil adapter에서 같은 요청·질문·승인 계약에 연결한다.
- **coding-practice / Whetstone**: 별도 Git root와 독립 GitHub origin이 있음을 읽기로 확인했다. 새 저장소를 중복 생성하거나 source를 이동할 필요가 없다. 사람 연습은 서비스·필수 pack·실행/출시 조건에서 제외하고 독립 유지한다. profile은 연습 저장소 없이 사용할 수 있어야 하며 기존 원본은 사용자가 선택한 외부 source로만 연결한다. 설치·문서의 연결 해제는 기존 사용자 호환을 지키는 후속 구현이며 이 검토에서 다른 저장소를 수정하지 않았다.

## 6. 구현 순서와 병렬 작업 경계

아래 두 표는 10월 계획의 P/G 단계 매핑으로 보존한다. 실행 gate와 완료 조건은 최신 상세 정본 §8을 따르되, 후속 확정된 개발 접점 순서는 §5의 TUI·원격 우선을 적용한다. 기존 plugin 수리(G0a→G1a)와 새 Core/controlled fork(G0b→G2→G3→G4)는 별도 track이며 G0b의 독립 계약 검토는 G0a와 병행할 수 있다. 먼저 OMP 읽기 전용 조사로 재사용 범위·첫 실행 환경과 G0b 작업 하나의 계약을 좁힌다. 웹·모바일의 결과 작업대와 시각 검토는 후속이며 첫 Core 구현의 선행 조건으로 두지 않는다. 이번 순서 선택으로 구현 착수 권한이나 gate 통과를 새로 부여하지 않는다.

차이는 G2의 TUI·로컬 채팅·반응형 질문/승인, G3의 지원 host 조합·입력/접근성·동시 결정 검증, G4의 원격 모바일·상시 authority/worker다. 아래 PH/GH는 조건부 관리형 제공·검사 항목의 과거 이름이고 GL은 후속 최적화 후보다. 이를 최신 G4 gate의 우회나 새 음성·모든 host의 선행 필수 조건으로 해석하지 않는다.

| 단계 | 결과 | 진입과 종료 조건 |
|---|---|---|
| P0a baseline 복구 | WIP 복원·접근 가능한 family inventory·기존 동작과 설치본 기준선 | G0a 복원 리허설 뒤 lane A 시작 가능 |
| P0b 실행 계약 | 한 작업의 최소 입력·스킬 효과·검사 recipe·상태/승인 fixture, 책임 ADR·runtime 실증·예산 | G0b는 해당 수직 단면의 blocking 결정만 해소. 전체 스킬 변환·모든 비교 실험·임시 agent 생성기 완성은 선행 조건이 아님 |
| P1 기반 병렬 구현 | 안전성 수리 뒤 host pack·설치, ledger·verifier·runtime stub·Inbox mock | P0 뒤 서로 독립된 모듈만 병렬. G1a 안전성·G1b 두 host pack을 구분하고 공통 schema는 단일 담당 |
| P2 첫 수직 단면 | 단일 runtime의 격리 변경·독립 검증·질문·승인·반영·복구·단일 장비 무인 준비 | 작은 로컬 결합 시험 뒤 전체 수직 단면 완료. 실제 repo 개선·기억의 다음 작업 적용·수정/철회·근거 기반 반성·OS wake/restart·취소·stale 승인 검증 |
| PH 완전관리형 alpha와 유료 파일럿 | 터미널·웹·모바일 접점 → 샘플/최소 권한 연결 → 텍스트/기본 STT 요청 → agent의 선택 실행 → 독립 검증 → 보호 preview → 승인 반영 | G2의 실행·기본 개인화와 GH 격리·인증·예산·복구·삭제 증거 뒤 고객 제공. 로컬 OS wake·두 native pack 전체 완료와 구분하며 G1b/G3 미완료면 단일 runtime alpha로 명시 |
| P3 멀티모델 출시 검증 | Claude/Codex 두 runtime·두 pack·서로 다른 repo profile, Glow·Voice·설치·복구 | 동일 핵심 계약, native/managed 독립 가치, 정책 위반·허위 PASS·중복 action 부재와 작업 효과 검증 |
| PL 개인화 고도화 | 지시 생성·맥락 선택·Reflexion 전략의 장기 평가·rollback | 기본 기억·교정·적용은 G2/GH에 포함. GL의 독립 holdout과 보안·품질 기준을 충족한 뒤 GEPA 배치 최적화. 모든 요청에 최적화 실행 금지 |
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

10월의 직접 Codex 우선·Claude 대안은 과거 연결 후보로 남긴다. 현재 우선 재사용 경로는 최신 상세 정본의 controlled OMP fork이며 실제 연결 조합은 G0b 능력·권한 실증으로 정한다. **연결 순서와 단일 runtime 내부 alpha를 G3의 두 runtime·두 pack 검증 완료로 바꾸지 않는다.** native pack은 개발 호스트의 사용성이고 runtime adapter는 코어 실행 능력이므로 각각 검증한다. 이는 이번 세션의 계정·모델 전환이나 추가 실행을 허용하지 않는다.

G0b에서 모든 profile·agent·pack·서비스 형태 비교를 끝내려고 하지 않는다. 먼저 현재 native 기준선과 필수 계약 하나를 연결하고, G1b/G2에서 필요한 스킬 adapter·검증/상태 경계를 실증한다. profile 선택·임시 agent·추가 모델은 실제 과제에서 생긴 공백을 해결하는 경우에 비교한다. GH는 같은 핵심 계약을 hosted 환경에서 검증하며, 각 증거의 출처를 연결하되 로컬 G2 전체나 G3가 끝났다고 표시하지 않는다. GL 최적화와 선택 connector는 그 뒤에 확장한다. 이 순서 변경은 구현 착수 요청이 아니다.

### 사업 검증과 기술 완료의 관계

비개발자 시장·쉬운 채팅 방향은 유지하며 개발자 dogfooding 성공만으로 비개발자 사용성·사업성을 입증했다고 보지 않는다. 사업 가설·2026-10-25 경쟁 비교·체감 가치·파일럿 설계는 [서비스 계획 §6](../docs/agentops/13.hosted-personalized-service-plan.md#6-가격수익-가설과-계약-검토)에 둔다. G0b에서 초기 고객·반복 작업 유형·기본 기억까지 설정한 native+CI 기준선·고객이 의미 있다고 보는 개선 폭을 정한다. G1/G2와 함께 동의한 고객의 실제 문제를 확인하고, 고객 실행·유료 파일럿은 GH의 필요한 격리·인증·운영 gate 뒤 제공한다. 모든 기술 구현이 끝나야 시장을 검토하는 순서로 만들지 않는다.

측정 중심은 반복 사용에 따른 설명·교정·검토·재작업 시간의 변화이며 품질·정책 준수·전체 비용·지연을 함께 본다. 기억·멀티모델·모바일·음성·백그라운드 실행 자체는 경쟁 우위로 계산하지 않는다. 실제 지불·반복 사용·변동 지원을 포함한 원가가 확인되지 않으면 관리형 범용 기능 확대를 보류하고 고객군·가격·범위를 재검토한다. 이는 기술 gate 통과를 사업 성공으로 오인하지 않기 위한 투자 판단이며, 유용한 무료 OSS 유지와 별개다. 이번 검토에서는 고객 연락·계량 수집·결제·구현을 시작하지 않았다.

### 병렬 lane

| lane | 저장소와 소유 범위 | 선행 조건 | 완료 산출물 |
|---|---|---|---|
| A 기존 제품 안전성 | code-forge hooks·상태 유틸·회귀 fixture | baseline 고정 | 결함 재현, 수정, 실제 payload 결과 |
| B 멀티호스트 pack | code-forge 공통/특화 원본·compiler·설치·생성 manifest | P0 host 능력표·적재/본문 비교 계획 | dry-run·설치·제거, Claude/Codex 자동 적재·발견·공용/특화 비교 증거 |
| C 원장과 정책 | core contracts·memory/context·ledger·policy | P0 schema | 기억 출처·revision·동시 수정/철회, migration·중복·재시작·realm 검사 |
| D 독립 검증 | core verification·repo profiles | P0 schema | 허위 PASS·weakening·baseline 비교 검사 |
| E runtime 연결 | core runtime-adapters | P0 capability 계약 | 두 runtime adapter와 conformance |
| F 검토와 반영 | core inbox·execution | P0 mock으로 시작, C/D 연결 뒤 완료 | stale 승인 차단·apply/readback·질문 재개 |

lane 수는 동시 에이전트 수가 아니다. P1은 A+B와 코어 기반 중 준비된 작업을 최대 2개 lane부터 실행하고, 완료된 lane을 D/E/F로 교체한다. 공유 파일이 겹치면 직렬화한다. A/B의 `bin/forge`, CI, setup 접점은 통합 담당자 한 명이 맡고 각 lane은 독립 모듈과 테스트부터 만든다. core 공통 schema·lockfile·루트 CI도 단일 소유자만 수정한다.

각 lane은 별도 worktree·브랜치를 사용한다. 결과에는 기준 SHA, 변경 범위, 실제 검사 명령·결과, 미확인, 다음 의존성을 남긴다. merge 후 통합 HEAD에서 재검증한다. 독립 reviewer는 수용 조건·diff·증거를 받고 작성자의 장문 추론을 근거로 삼지 않는다. 서로 다른 모델 사용은 가능한 경우의 검증 강화이며 결정적 검사를 대체하지 않는다.

통합 담당자는 marketplace catalog/BOM, Glow consumer-first·parity, Voice 경로와 provider, 개인 profile 전달 fixture, 기존 사용자 hook 보존을 조정한다. 인접 저장소 변경은 해당 Goal의 허용 경로에 포함한 뒤 수행한다. Hearth/Flow의 재활성화를 A~F의 선행 조건으로 두지 않는다.

## 7. 검수 후 설정할 Goal 초안

다음은 10월의 향후 Goal 초안이며 이번 후보 준비에서 Goal을 생성하거나 실행하지 않았다. §6에서 설명한 과거 GH/GL 지위를 적용하며, 충돌하는 원격 모바일·voice·host 범위와 의존성은 최신 상세 정본 §8로 대체한다. 아래의 유효한 안전성·데이터·호환 요구는 해당 gate에 보존한다. 후속 확정된 TUI·원격 우선 순서와 G0b 한 작업의 다음 단계는 §5~6을 적용한다. 사용자 관리 머신·서버의 SSH 재접속 확인을 공개 SaaS·원격 모바일·격리 gate 완료로 승격하지 않는다. 전체 플랫폼을 하나의 끝없는 Goal로 묶지 않고 검증 가능한 단위로 닫는다.

| Goal | 완료 조건 | 제외 범위 |
|---|---|---|
| G0a 복구 가능한 baseline | WIP 실제 백업·복원, 설치본/source 구분, 접근 가능한 family·기존 동작 baseline | 기능 구현·새 저장소 공개·배포 |
| G0b 최소 실행 계약 | 한 code-change/verify-only 흐름의 최소 스킬 입력·효과·결과/검사/질문/승인 fixture, 책임·공통 기억의 정본/수명·모델별 전달 및 개발/관리형 의존성 없는 최소 fixture, runtime 하나의 실증, 예산·기술 선택 ADR과 후속 비교/이관 계획 | 전체 catalog compiler·영구 SDK·모든 모델/스킬 비교 완료·임시 agent 생성기·새 repo 선행 구축 |
| G1a 기존 제품 안전성 | 재현된 gate·state·hook·cleanup·handoff 결함 수리, 사용자 수정·실패 증거 보존, 기존 alias·Smith 정책·로컬 Voice·Glow 회귀 | 전역 무인 원장·서비스 출시 완료 주장 |
| G1b 두 호스트 pack | 선택한 핵심 기능의 Claude/Codex 자동 적재·발견·권한·설치/갱신/제거, 입력·출력·효과 fixture, 공용/특화 비교, Smith 비사용·기존 활성 설정 호환, §8 안내·이관·복구, core 없는 사용 | 전체 스킬 동일 지원·core runtime 완료·모든 모델 동일 동작 보장 |
| G2 코어의 개인 수직 단면 | runtime 하나·repo 하나의 실제 개선·독립 검증·질문/승인·반영/readback, 검사/생성/설치 효과 구분·상위 retry budget, 공통 기억의 다음 작업 적용·수정/철회·근거 기반 반성, Git/pack/managed Work 없는 기억 흐름 검사, provenance·단일 realm과 타 realm 거부·OS wake/restart·취소 | 모든 provider/스킬·원격 모바일·새 Voice 승인 기능·팀 서버. GH는 증명된 핵심 계약을 소비하며 로컬 부가기능 미완료를 G2 완료로 표시하지 않음 |
| GH 관리형 고객 alpha | G2 실행·기본 개인화 증거, 고객별 기억 조회/수정/삭제/끄기, tenant 격리·터미널/웹/모바일 인증·동일 Work 이어가기·기본 STT 전사확인/텍스트 입력·짧은 토큰·취소/복구, no-key 샘플·최소 repo 연동·보호 preview, 비용 예약/정산·삭제·운영 대응 | 조직 장비 접근·상시 음성 대화·무제한 실행·상시 hosting 포함 주장. 음성 실제 반영 승인은 별도 binding gate, 상세 계획 §2·7의 출하 검사 필수 |
| GL 개인화 고도화 | 시간 순서·계보별 분리 eval/holdout, 지시/맥락/Reflexion 전략 비교, 모델별 품질·보안 비퇴행, 후보 검토·점진 배포·rollback·삭제 전파 | 모델 가중치 튜닝·모든 모델 최적 보장·조직 자료의 개인 학습 전용 |
| G3 멀티모델과 family 출시 gate | 두 runtime·두 pack·두 profile, 공통 개인 기억의 모델별 적용·회귀, native/managed·Glow·Voice·호환성·복구·실제 효과 보고 | GLM/Qwen·Hearth 지원 완료 주장 |
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
| 개인화 코어 | 공통 기억·출처·revision·모델별 실제 전달, 다음 작업의 교정 감소·기준 유지, 일회 예외·철회·동시 수정·반성 후보 오염·영역 누출·복원 검사 |
| family 호환 | 기존 alias·Smith semantic golden·status v1·Glow·Voice와 사용자 hook 보존, Flow dual-write 부재 |
| 데이터 수명 | realm별 경로·조회 권한·redaction·retention·삭제·복원 검증 |

문서 검토·mock 통과·실호스트 통과·배포 완료는 서로 다른 상태다. 자동 최적화 후보가 기각돼도 판정 시스템은 정상일 수 있지만, 실제 개선 효과를 주장하려면 재현된 성공 사례가 필요하다.

기존 플러그인 버전을 올릴 때는 `CHANGELOG.md`와 `.claude-plugin/plugin.json`을 같은 커밋에서 갱신한다. 배포 단계에서는 저장소 AGENTS.md의 main push→project/local plugin update→캐시 핵심 변경 spot-check를 따른다. 소스 수정만으로 배포 완료를 선언하지 않는다. 새 코어는 별도 버전과 pack/protocol 호환표를 갖고, 두 제품의 지원 조합을 CI에서 확인한다.

`forge-market`의 catalog 하나에서 host별 manifest와 호환 BOM을 생성한다. 하나의 제품 release ID에 host/model별 pack version·source SHA·tag·artifact digest·contract 범위를 연결하고 같은 pack version에 다른 artifact를 배포하지 않는다. 서로 다른 호스트 pack은 내용과 digest가 달라도 같은 제품 release의 승인된 조합에 속할 수 있다. stable/dev를 분리하며 stable 설치는 runtime `git pull`로 바꾸지 않는다. 이 문서 커밋은 plugin version bump·배포가 아니다.

### CodeForge의 배포 형태와 업데이트 계약 — 2026-10-24 검토

설치 후 개선을 계속 전달하려는 기존 플러그인의 목적을 유지한다. **제품의 중심 역할은 §2의 지침 구성 compiler·결정적 도구·공통/특화 원본이며, plugin/pack은 그 기능을 host에 전달하는 접점이다.** 배포는 버전 있는 묶음과 호스트별 native 경로·공통 설치/진단 로직을 사용한다. Claude 플러그인은 필요한 기능만 담아 계속 제공하고 관리형 서비스는 모듈·산출물을 직접 소비하는 방향을 실증한다. 공통 도구는 필요한 배포물에 함께 넣을 수 있는 논리적 모듈이며 별도 daemon·레지스트리·agent loop의 선행 구축이나 모든 사용자의 CLI 설치를 뜻하지 않는다. 작은 plugin만으로 같은 효율을 얻으면 더 큰 구조 변경을 진행하지 않는다.

현재 소스의 `hooks/session-init.sh`는 `FORGE_AUTO_UPDATE=1`인 개발용 Git clone에만 fetch/pull을 수행하고 `.git`이 없는 marketplace cache는 건너뛴다. 프로젝트 생성 버전이 달라지면 `/setup`과 Smith 재컴파일을 안내하는 경로도 있다. 따라서 현재 구현을 ‘모든 설치 사용자가 hook으로 즉시 최신 버전을 받아 적용’하는 시스템으로 설명하지 않는다.

| 사용 환경 | 배포·갱신 주체와 확인할 한계 |
|---|---|
| Claude Code | 기존 marketplace/plugin을 유지하고 native plugin manager가 패키지를 갱신한다. 공식 문서는 marketplace별 자동 업데이트 설정과 다운로드 후 다음 세션/명시적 reload의 활성화를 구분한다. 일반 third-party marketplace는 자동 업데이트가 기본 꺼짐이다. [공식 설치·업데이트 문서](https://code.claude.com/docs/en/discover-plugins) |
| Codex | 플러그인을 지원하는 desktop/CLI의 native 설치·갱신 경로를 우선 실증한다. Codex에 플러그인이 없다고 전제하지 않는다. portable manifest·marketplace 경로는 있으나 설치 표면과 hook 지원은 서로 다르다. 갱신 주기·자동 적용·고정·rollback 가능 여부를 Claude와 같다고 가정하지 않는다. [공식 사용 문서](https://learn.chatgpt.com/docs/plugins), [패키징 문서](https://developers.openai.com/plugins/build/plugins) |
| 플러그인 경로가 없는 host·로컬 실행 도구 | 버전 고정 pack과 설치·갱신 도구로 해당 host의 instruction/skill 경로를 관리한다. 자동 갱신은 host의 지원 기능 또는 사용자가 선택한 launcher/주기 실행 방식이 있을 때 제공한다. 지원이 없으면 명시적 갱신 경로와 제한을 안내하고 모든 세션의 자동 최신화를 약속하지 않는다. |
| 완전관리형 제품 | 운영자가 검증된 서버·pack·adapter 조합을 배포한다. 고객에게 Claude/Codex 플러그인 설치를 요구하지 않는다. 진행 중인 Work는 시작 시 고정한 조합을 유지하고 다음 Work부터 승인된 새 조합을 쓴다. |

호스트별 플러그인만 따로 운영하면 릴리스·진단이 분산되고, 모든 것을 단일 CLI로 강제하면 native 발견·설치·갱신 편의를 잃는다. 따라서 공통 release 계약을 두고 각 host의 배포 기능을 활용한다. CLI는 설치·설정 생성·검증·진단을 재사용하기 위한 수단이며 모델의 매 작업을 중계하는 필수 실행기로 만들지 않는다. 기존 `bin/forge` 확장과 배포 바이너리 형식은 G0b에서 결정한다. 갱신·복구 명령은 아직 구현하지 않았다.

업데이트의 공통 동작은 다음과 같이 정의한다.

1. **같은 릴리스 식별:** catalog와 host별 배포물, 프로젝트 생성물에 release/pack/source/compiler 식별자를 연결한다. 공개 채널별 배포·심사 지연은 별도 상태이며, 아직 제공되지 않는 pack을 배포 완료로 표시하지 않는다. 여러 marketplace의 동시 도착을 보장하지 않는다.
2. **다운로드와 활성화 분리:** 제공된 버전·설치된 버전·현재 세션이 적재한 버전·프로젝트 생성 버전을 구분해 진단한다. ‘캐시 다운로드 완료’를 적용 완료로 표시하지 않는다. session/managed Work는 실제 적재 digest를 고정하고 실행 중 원본을 교체하지 않는다. 자동 고정이나 적재 버전 관측이 불가능한 host는 해당 보장 미지원으로 표시한다. managed의 필수 고정·호환 검증에 실패하면 해당 실행을 시작하지 않는다.
3. **갱신 주체 단일화:** native manager가 설치한 패키지는 그 manager가 갱신한다. 공통 도구는 관측·호환 검사와 자신이 소유한 프로젝트 생성물만 담당한다. 독립 pack 설치에서는 공통 도구가 갱신을 맡는다. 같은 설치물에 plugin manager·hook·CLI가 동시에 쓰지 않는다.
4. **선택한 자동 업데이트:** 초기 설정에서 자동/수동과 허용 채널·범위를 고른다. 사전 허용된 호환 갱신은 매번 확인하지 않고 새 세션의 활성화 경계에서 적용한다. 새 실행 권한·hook·외부 연결이나 사용자 파일 충돌은 기존 허용으로 덮지 않는다. host가 버전 범위 제어를 지원하지 않으면 그 한계를 명시하고 수동 갱신 등 지원 가능한 경로를 제공한다. CodeForge 자체의 기본 SessionStart hook에는 네트워크 갱신을 추가하지 않는다. host manager의 background 갱신은 별도 설정이며 폐쇄망은 오프라인 묶음만 사용한다.
5. **프로젝트 생성물과 복구:** 패키지 갱신 뒤 instruction·Smith 출력도 source/compiler digest로 검사한다. 사용자 소유 영역을 보존하며 필요한 이관을 preview하고, 호환되는 활성 조합이 확인된 뒤 적용 완료로 판정한다. 중단·충돌 시 이전 유효 조합을 보존한다. native manager의 검증된 복구 경로와 독립 pack의 검증 후 원자 전환을 구분하고, 지원하지 않는 rollback은 가능하다고 표시하지 않는다.

G0b에서 host·설치 scope·갱신 주체·자동 갱신/고정/활성화/복구 지원표와 최소 fixture를 정한다. G1b/G3는 새 설치 → 기존 설치의 실제 업데이트 → 새 세션 적재 → 프로젝트 생성물 정합 → rollback/uninstall을 실제 host에서 확인한다. 동시에 두 host를 사용하는 프로젝트, 한쪽만 배포된 상태, native/독립 pack 중복 설치, 네트워크 단절·부분 다운로드·동시 갱신·사용자 수정·실행 중 업데이트를 검사한다. 같은 프로젝트의 승인된 release 조합에서 벗어나면 해당 연결을 호환 완료로 표시하지 않으며 managed 실행의 필수 조합 불일치는 차단한다. 설치 명령이나 UI가 같다는 이유로 일관성 통과를 선언하지 않는다.

복구 검증은 설치물의 검증 후 원자 전환·이전 버전 복원, 소유한 설정 조각만 제거, candidate worktree 폐기, ledger migration 백업/복구, 외부 action readback/보상으로 나눈다. core 중지 시 새 managed 실행을 차단하고 기존 결과를 조정한다. native 작업은 독립적으로 유지하되 미확정 managed Work를 자동 인계하지 않는다. 지원할 N/N-1 또는 정확한 protocol·pack 조합을 선언하고 실제 설치·복구 drill로 검사한다.

### 기존 사용자의 전환·안내와 Smith 호환

패키지 업데이트와 사용자 프로젝트 이관은 다른 작업이다. 신규 설치의 기본 추천 변경을 기존 프로젝트의 Smith 설정에 소급 적용하지 않는다. 기존 정의·사용자 수정·핵심 정책을 보존하고, 다음 전환 경로가 실제로 동작한 뒤 기본 추천 변경이나 폐기를 출시한다.

1. **전환 대상 확인:** 프로젝트에서 명시적으로 연결한 설치 scope·pack·Smith 활성 설정·생성 manifest를 읽어 변경할 파일과 현재 조합을 확인한다. 무관한 저장소를 탐색하거나 사용자 agent 내용을 서버로 수집하지 않는다. 소유권·원본·기준 digest가 불명확하면 사용자 파일로 취급한다.
2. **안내와 지원 기간:** 전환 릴리스의 CHANGELOG·업데이트 화면/로컬 알림에 새 기본 동작, 기존 모드 유지 여부, 이관 가능/보류 상태, 필요한 행동과 복구 방법을 제공한다. 기존 alias·명령은 앞의 최소 두 릴리스 호환 원칙을 지키고, 지원 종료 전 대체 경로·버전/일정을 명시한다. 코드/계정 정보를 밖으로 보내야 안내할 수 있는 구조로 만들지 않는다.
3. **자동 이관 범위:** 사용자가 이미 허용한 프로젝트 갱신 범위 안에서, 생성 소유권과 원본이 확인되고 수정·권한 변화가 없는 호환 변환만 백업 → 새 위치에 준비 → 검증 → 전환한다. 매번 재승인하지 않는다. `.agents/agents/` 원본으로 새 출력을 만들며 `.claude/agents/`를 직접 패치하지 않는다. 패키지 캐시 갱신만으로 사용자 원본을 변환하지 않는다.
4. **수정 파일과 의미 변경:** 생성 당시 기준·현재 파일·새 템플릿의 차이를 비교하고 사용자 수정은 보존한다. 수동 파일·충돌·모호한 규칙은 해당 경로만 보류해 구체적 diff와 선택지를 제공한다. 기존 선택의 일괄 해제, agent 삭제·이름 변경, 다른 모델/계정·권한으로 전환, 개인 선호·Must/Never의 의미 변경은 별도 승인 없이 자동 이관하지 않는다. 지식을 profile/skill로 옮길 때도 빠진 정책이 없는지 검사한다.
5. **상태와 복구:** `기존 모드 유지 / 자동 이관 완료 / 검토 필요 / 실패 후 복구`를 구분한다. source·설치물·세션·생성물의 조합과 백업/복구 receipt를 로컬에 남기며 기존 파일 전체를 공개 로그에 넣지 않는다. 실패하면 검증된 이전 조합을 유지·복구하고, 진행 중인 session/Work는 시작 버전을 사용한다. 오프라인·비활성 설치에는 즉시 전달됐다고 표시하지 않는다.

사용자 안내의 예시는 ‘새 프로젝트는 필요한 지침과 검증 설정을 우선 구성합니다. 기존 Smith 사용 설정과 수정한 파일은 유지됩니다. 이 프로젝트의 전환 상태: {기존 모드 유지/자동 이관 완료/검토 필요}. 필요한 행동·변경 내역·되돌리기: {실제 제공 경로}’다. 이관되지 않았는데 자동 완료라고 표시하거나, 모든 사용자에게 `/setup` 전체 재실행을 반복 요구하지 않는다.

G1b/G3의 이관 fixture는 기존 Smith on/off, 생성 후 무수정/사용자 수정/수동 정의/manifest 부재, 중단·재시도·재실행·이전 버전 복구를 포함한다. 정책·개인 profile·alias 보존과 질문 중복을 확인한다. 이관 도구와 복구가 미완료면 파괴적 기본 전환을 미루고 기존 모드를 제공한다. 효용 비교에서 역할을 제거하기로 했어도 사용자 프로젝트에서 즉시 삭제하는 근거로 삼지 않는다.

## 9. 이번 검수에서 결정할 사항

아래는 10월의 미결정·후속 검증 목록을 보존한 것이다. 2026-11-05의 정본 연결과 2026-11-07의 결과 작업대 중심·TUI/원격 우선 선택으로 지위가 달라진 항목은 수정했으며, 권고·선택지를 구현 완료로 승격하지 않는다. 확정된 정보 구조 방향, 기각 시안의 중단·재사용 금지와 남은 시각 검토·다음 작은 단계는 §5 및 CURRENT를 따른다.

| 항목 | 권고안 | 결정이 필요한 시점 |
|---|---|---|
| 제품 중심 | 공통 기억·개인 기준·경험·모델별 지시·Reflexion이 이어지는 개인화 코어. 어시스턴트와 실행 에이전트/서브에이전트 구분 | 제품 방향 반영, G2/GH 기본 개인화·G3 모델 간 전달·GL 고도화 검증 |
| 저장소 경계 | CodeForge 무료 OSS 유지 + 이를 소비하는 별도 제품 권고. 신규 core repo 필수 아님 | G0b packaging·consumer 실증 후 |
| CodeForge의 중심 역할 | 정책·지침 구성 compiler와 결정적 도구로 발전, native는 최소 plugin/pack·managed는 직접 소비. 작은 plugin만으로 같은 효과면 큰 전환 생략 | G0b 최소 비교 설계, G1b/G2/GH 품질·총비용·전환 비용 증거 뒤 확정 |
| Smith·프로젝트 특화 agent | 신규 일괄 역할 생성은 기본 추천에서 제외하는 방향. 지식 전달·기본 subagent·custom agent를 비교해 이득 있는 특화만 고도화. 기존 활성 설정은 보존 | G0b 비교 설계, G1b/G2/G3 모델별 효용·비용과 호환 검증 |
| 작업별 임시 agent | 위임이 유익할 때 skill/기존 compiler가 최소 지침을 조립해 기본 subagent 우선 실행. 필요한 임시 정의는 결과·근거 회수 후 종료·정리, 반복 이득만 재사용 후보로 승격 | G0b host 능력·비교 설계, G1b/G2 생명주기·총비용·정리/복구 검사 |
| 기존 사용자 전환 | 안내·소유권 확인·백업·허용 범위의 자동 이관·수정 파일 보류·복구. 기존 alias 최소 두 릴리스 유지, 폐기 일정 사전 안내 | 기본 추천 변경·전환 릴리스 전 G1b/G3 이관/복구 통과 |
| 호스트·모델별 원본 | 같은 저장소의 공통 정책 + host별 자동 적재 파일 + 평가로 채택한 모델별 특화 본문. 저장소 분리도 실증 후 ADR로 허용 | G0b 비교 계획, G1b/G3 채택 근거·유지 비용 확인 |
| 제품 배포 형태·업데이트 | 버전 있는 도구 묶음 + host-native plugin/대체 pack. 공통 release 계약, 설치물별 갱신 주체 하나, 선택한 자동 갱신과 새 세션 활성화·생성물 정합 확인 | G0b 배포/갱신 능력표, G1b/G3 실제 업데이트·복구 검증 |
| 제품·메타포 | CodeForge OSS, Atelier 가칭 제품. Library/Workbench/Inspector는 설명용 책임 이름. 대장간 메타포와 제품 고유성 보존 | G0 ADR·상표 검토 전 이름 확정 금지 |
| 작업 진행 중 정보 구조 | 데스크톱은 결과 작업대 중심, 열고 닫는 보조 대화·얇은 작업 탐색·결과에 연결한 질문/변경/검증/승인. 첫 요청의 쉬운 채팅·모바일 채팅 기본·동일 Work의 키보드 TUI 유지 | 정보 구조 방향 선택 완료. 웹의 필수 정보·작업 흐름과 실제 레퍼런스·작은 와이어프레임 검토는 후속. 색·폰트·세부 레이아웃·구현·실제 prototype은 미승인 |
| 개발 접점 순서 | 개발자 TUI·사용자 관리 머신/서버의 SSH 원격 사용 우선. 웹·모바일 결과 작업대·텔레그램 등은 후속, 네이티브 앱은 실제 필요 확인 후 선택 | 순서 선택 완료. 다음은 OMP 재사용 범위·첫 실행 환경의 읽기 전용 조사와 G0b 한 작업의 실행 계약 좁히기. 기술 스택·fork 실제 변경 범위·파일 경로는 미확정 |
| 에이전트 자율 선택과 일관성 | agent는 환경·목표에 맞춰 스킬·도구·위임·다음 행동을 선택, host/core는 권한·예산·상태·독립 검증 집행. 미지원 표시와 근거 있는 fallback | G0b 효과 계약, G1b/G2/GH 실제 흐름·실패/재개 검사 |
| coding-practice 분리 | 이미 별도 Git root/origin. 사람 연습은 서비스·필수 pack·출시 조건에서 제외, 개인화는 연습 repo 없이 사용. 기존 profile 외부 참조는 선택 | 이번 계획에 범위 반영, 연결 해제/기존 사용자 호환은 후속 구현 |
| 첫 고객 경험 | 최신 상세 정본 §6·8의 사용자 소유 모델 시작 경로, 관리형 제공은 조건부 선택. 웹/모바일 채팅과 개발자 TUI가 같은 Work를 사용. 실행·preview·상시 hosting 비용 분리 | G0b 능력·원가, G2 로컬 흐름, G4 원격·관리형 제공 gate |
| 수익 구조 | 기본 구독 + 제한된 사용량 + 명시적 추가 구매. 가격은 가설, 무제한 약속 금지 | 유료 파일럿 전 실제 원가·약관 검증 |
| 기존 계획과의 관계 | 최신 상세 정본을 상세 설계·실행 gate 기준으로 채택. 이 문서와 서비스 계획은 유효 요구·과거 초안을 보존 | 정본 포인터 반영, 구현 전 충돌 범위 재확인 |
| 직접/관리 실행 | 작은 작업은 native, 장기 목표는 명시적 managed. 설치만으로 자동 전환 금지 | G0 계약 |
| 정책·판정 권위 | advisory/preference와 집행 항목 구분, managed verdict는 core, host permission 별도 | schema fixture 전 |
| 상태·계약 정본 | 기존 status v1·progress·승인 원본 보존, core가 Work와 공통 개인화 기억의 논리적 권위·수명 소유 | schema fixture 전 |
| flow-toolkit | 필수 엔진으로 부활시키지 않음. 검증 요구만 계승 | G0 시작 전 |
| Hearth | 휴면 백업. 다중 source Markdown 수요와 안전성·schema·parser gate 뒤 유지/흡수/archive | G0 동결, P4 재평가 |
| Glow·Herdr | Glow는 projection, Herdr는 권한 있는 제어 adapter. 실제 설치·능력 별도 검증 | G0 능력표 |
| Voice·음성 서비스 | 기존 로컬 입력 보존, 새 녹음/전사·승인 연결은 후속 선택 기능. 음성은 권한을 확대하지 않고 실제 반영 승인은 대상·버전에 묶음 | 기존 경로 회귀 유지, 새 기능은 가치·접근성·비용 및 별도 입력/승인 gate |
| context·언어 | 권한 선검사·최소 선택·출처는 G2/GH부터. 고급 검색 UI·자동 언어 최적화는 후속 | G0 최소 fixture, GH 누출 검사 |
| 멀티모델 범위 | Claude/Codex 두 runtime·두 native pack의 실제 conformance 뒤 G3 지원 선언. 단일 runtime G2 내부 alpha와 구별 | G0b 능력표, G1b pack 검증, G3 지원 조합 검증 |
| 첫 실증 범위 | 공개 코드 저장소 한 곳과 구조화 runtime 하나, 이후 두 번째로 범용성 확인 | G0에서 repo·runtime 확정 |
| 기술 재결정 | 10월 Go+TS 결정과 TS 단일 후보를 설치·복구·SDK 실험으로 비교, SQLite WAL 검증 | G0 실험 뒤 ADR |
| 배포·호환·복구 | 단일 catalog·불변 artifact·stable/dev·호환 기간·종류별 rollback drill | G0 정의, G1/G3 검증 |
| 비용과 계정 | 허용 계정·realm·외부 action·예산·실행 시간 명시 | 유료·인증 실행 전 |
| 데이터 보존 | realm별 DB·artifact·원문 수집 범위·retention·export/delete·백업 정책 | 첫 managed 실행 전 |
| 공개와 라이선스 | 새 저장소 공개 범위·라이선스는 별도 확정. 비공개 참고 코드 복사 안 함 | 저장소 공개·배포 전 |

10월 개정과 2026-11-05 후보 준비에서는 새 교차 모델 검수를 수행하지 않았다. 승인된 최신 상세 정본에 기록된 이전 독립 검토의 범위는 §1에서 구별했다. Goal·새 저장소·runtime 계정 연결·인접 저장소 변경·배포는 별도 구현 단계다. 구현 착수 권한이 생기면 G0a의 복원 가능한 baseline과 G0b의 최소 계약·packaging·격리·원가를 각각 확인한다. 현재 다음 작은 단계는 §5의 TUI·원격 우선 결정에 따라 실제 OMP 재사용 범위·첫 실행 환경을 읽기 전용으로 조사하고 G0b 작업 하나의 실행 계약을 좁히는 것이다. 기술 스택·fork 실제 변경 범위·파일 경로는 코드 조사 전이므로 미확정이다. 웹의 시각 레퍼런스·와이어프레임 검토는 후속으로 남기며 새 디자인·프로토타입과 기각 시안의 자동 재개·재사용은 금지다. 이번 Python 문서 smoke는 두 후보의 존재·상대 링크의 후보 또는 게시 기준 Git 파일 해결·선택과 미확정 구별만 확인하며 외부 링크·앵커 도달은 검증하지 않았다.
