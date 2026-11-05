# Tern에서 배운 터미널 UX를 반영한 CodeForge 통합 최종안

## 1. 결론과 선택

**[권고] CONDITIONAL GO. CodeForge가 작업 UX와 Core를 소유하고, controlled OMP fork의 실행·렌더링 능력, TSP native 표현, ANSI TUI와 기존 terminal 기반을 재사용한다.** Tern host는 선택이지만 개발자 기본 UX의 품질은 필수다. 키보드 탐색·작업 전환·입력 보존·검토·승인·복구를 G2의 실제 완료 조건에 넣는다.

| 대안 | 비용 | 호환성 | 권리 | 자립성·판정 |
|---|---|---|---|---|
| 텍스트 출력 위주의 최소 TUI | 초기 비용은 작지만 입력·탐색·검토 부담이 남음 | 넓지만 rich 표현이 제한됨 | 재사용 자산별 확인 필요 | 사용자 요구를 충족하지 못하므로 기각 |
| Tern 앱 전체를 초반부터 재구현하거나 비공개 fork | terminal·PTY·GPU·창·동기화·업데이트까지 큰 유지비 | OS·기존 terminal 호환을 다시 책임짐 | 앱 전체의 source·fork·배포 권리 미확인 | 자립성 확보 전에 제품 개발을 지연하므로 기각 |
| 자체 작업 UX + OMP/TSP/ANSI·기존 terminal | 제품 흐름과 작은 adapter에 집중 가능 | 일반 terminal의 핵심 행동과 Tern 향상 경로 병행 | 공개 MIT 범위와 고지 조건을 지키며 재사용 | **권고안. Core·작업 계약을 소유하고 host 교체성을 검증** |

직접 만들 것은 Work 중심 정보 구조, command palette, 상태·증거·변경·질문·승인 화면, 초안 수명, 재접속과 권한 검사다. 재사용할 것은 OMP의 모델 연결·agent loop·기존 TUI/native renderer와 terminal emulator다. 새 범용 UI framework나 GPU 엔진은 만들지 않는다.

독립 CodeForge desktop 앱은 초기 필수가 아니다. dogfood와 제품 시험에서 기존 host로 해결하기 어려운 IME·접근성·첨부·알림·다중 창 문제가 반복되고, 사용자 부담 감소가 packaging·업데이트·보안·지원비를 정당화할 때 선택한다. 먼저 작은 독립 client로 검증하며 terminal emulator 재구축은 별도 근거가 있어야 한다. 기본 TUI 개선을 이 결정까지 미루지 않는다.

이번 문서는 제공된 이전 검수 결과에 새 terminal 요구와 연구 증거를 통합한 최종 의사결정안이다. 기존 16개 원문을 다시 조회하거나 검사를 재실행하지 않았다. 기존 Claude Opus 5.5 high 검토는 승인 bundle, 개인 Codex 대조는 당시 지정 자료에 한정된 기록이다. 전체 저장소·시장·실행 보안의 실증으로 확대하지 않는다.

## 2. Tern에서 확인한 것과 배울 범위

**[공식 문서]** Tern SDK는 host/window 확장과 native surface를 공개하며, 별도 CLI/TUI도 plugin 설치 없이 PTY에서 TSP를 사용할 수 있다고 설명한다. 프로그램이 semantic tree와 input/state를 소유하고 host가 배치·theme·일부 view 상태를 맡는 분리는 참고할 가치가 있다. ([SDK](https://docs.stencil.so/tern/index.md), [TSP](https://docs.stencil.so/tern/protocol/index.md))

공개 OMP의 pin `88a69582c755bd000e8dc0290981fc787a4f400c`에는 wire 타입과 renderer 계약이 있다. 제공된 조사에서는 handshake, semantic 표현과 rows fallback, credit pacing, startup typeahead, draft recall, stale node 거부를 확인했다. `packages/tui/src/native/backend.ts`와 `packages/tui/src/terminal.ts`도 공개 구현 앞부분을 읽었지만 해당 조회 URL은 mutable `main`이었다. **재사용 경로가 있다는 증거이며 CodeForge adapter 구현 증거는 아니다.** ([wire 타입](https://github.com/can1357/oh-my-pi/blob/88a69582c755bd000e8dc0290981fc787a4f400c/packages/wire/src/tsp.ts), [renderer 계약](https://github.com/can1357/oh-my-pi/blob/88a69582c755bd000e8dc0290981fc787a4f400c/docs/tui-core-renderer.md))

**[실제 관찰]** 제공된 독립 headless 연구는 설치 앱 메타데이터 `0.9.12`, 공개 dev 명령 노출, 별도 기본 환경의 창 분할·focus, command palette 표시, 공개 TSP 카드와 정적 한글 표시를 확인했다. 실행은 exit 0이었고 PNG 3개와 layout JSON을 남겼다. 기존 사용자 창·session·credential을 조회하거나 plugin을 설치하지 않았다. 팔레트 선택 실행, 한글 IME, 원격·모바일·restart·긴 세션 성능, CodeForge 제품 흐름은 검증하지 않았다.

**[권고]** 배우는 대상은 빠른 작업 접근, 의미 있는 상태 표현, keyboard hint, 한 화면의 주 행동 하나, 점진적 상세 공개다. 모든 내용을 카드로 감싸거나 LLM 로그를 그대로 쌓지 않는다. CodeForge 고유 정보 구조·용어·스타일로 재구성한다. ([공식 view 설계](https://docs.stencil.so/tern/guides/design.md))

공개 OMP와 Tern SDK의 MIT 원문에는 copyright·permission notice 보존 조건이 있다. 제품 branding 정리와 법적 고지 보존을 구분한다. **SDK MIT는 Tern 앱 전체의 fork·재배포, 비공개 source, 상표·visual asset 이용 권리를 뜻하지 않는다.** 앱 EULA와 실제 app fork 권리는 미확인이다. ([OMP MIT](https://github.com/can1357/oh-my-pi/blob/88a69582c755bd000e8dc0290981fc787a4f400c/LICENSE), [SDK MIT](https://github.com/stencil-hq/tern-sdk/blob/a3ba62fd180625a70de80b595f6accc383f27d58/LICENSE))

현재 목표에는 공개 경로가 있으므로 비공개 binary 분석은 선행 조건이 아니다. 향후 공개 자료로 해결되지 않는 구체적 호환 문제가 생기면 필요성, 이용 권리·약관·적용 법률, 접근 권한, 최소 분석 범위와 산출물 취급을 확인해 별도 범위를 정한다. 관찰·공개 코드 학습을 막연히 금지하지도, 앱 권리를 확보했다고 가정하지도 않는다.

## 3. 개발자 terminal 품질 계약

아래는 **[권고]이며 아직 제품에서 검증하지 않은 수용 기준**이다.

- **단일 진입:** 하나의 실행 진입에서 현재 Work 복귀, 새 작업, 검색·전환, 연결 상태에 접근한다. 반복 설정이나 host별 별도 작업 원장을 요구하지 않는다.
- **실제 실행 조건:** user·realm, provider, 인증 주체·연결 상태, 요청한 model/effort와 관측값, 예산의 예약·사용·잔여·불명을 보여 준다. 프로필명 ‘개인’은 계정 증거가 아니다. filesystem·network·tool·승인 권한을 관측하고 read-only session에서는 실행 불가 이유와 가능한 행동을 표시한다. 관측 불가 값은 unknown이다.
- **키보드 동선:** palette에서 Work 검색→전환→질문 답변·편집→diff·증거 확인→정확한 승인→결과 확인이 가능해야 한다. focus와 뒤로 가기를 일관되게 하고, 전환 후 이전 위치·검색·초안을 복원한다. 제출·승인은 단순 탐색과 구분하며 IME 조합 확정을 제출로 오인하지 않는다.
- **정보 구조:** 작업 요약과 attention 상태, 단계·비용, 변경/증거/대화/preview 상세, 하단 입력과 key hint를 연결한다. loading·empty·error·success와 blocked·unknown을 구분한다. 답변 대기·승인 필요·예산 부족·검증 실패·결과 불명을 우선 드러내고 로그는 필요할 때 펼친다.
- **검토와 조작:** diff, 검사 결과와 근거, artifact revision, preview, 반영 대상을 같은 Work에서 연다. mouse·semantic control·palette·keyboard는 같은 action을 호출한다. native 표현이 없어도 ANSI에서 조회·답변·승인·취소·결과 확인이 가능해야 한다.
- **입력 품질:** Work별 초안·답변·첨부 참조를 보존하고 다른 Work로 몰래 이동시키지 않는다. 붙여넣기·여러 줄·복사·한글 IME·조합 취소·파일 첨부를 실제 시험한다. 큰 paste와 민감 자료는 전송 범위를 확인할 수 있게 한다. host clipboard 미지원 시 명시적 파일·외부 편집 경로를 제공한다.
- **긴 작업:** 긴 이력의 점진 적재·가상화, scroll 위치, resize와 focus 유지, bounded buffer, 느린 렌더러의 backpressure를 설계한다. 입력 지연·메모리·재접속 시간의 기준은 시험 전에 정한다. 아직 성능 수치는 없다.
- **중단과 복귀:** 화면 연결 상태와 실행 상태를 따로 표시한다. 취소 요청·실제 중단·늦은 결과·외부 반영 여부를 구분하고, 재접속 시 마지막 Core 상태와 초안을 조정한다.

layout·검색·filter·progress 표시는 결정적 client 로직과 Core 상태로 처리한다. 화면을 열거나 전환할 때마다 모델을 호출하지 않는다. 미지원 native preview는 접근 통제된 browser나 외부 viewer로 연결하되 링크 열기를 게시 승인이나 권한 우회로 취급하지 않는다.

## 4. Core 권위와 작은 화면 연결 구조

**[권고]** Core가 Work·상태·정책·user/tenant/realm·credential·budget·검증·결정·승인·apply/readback·Receipt·memory 정본을 소유한다. OMP는 허용된 모델·도구·agent loop를 실행하는 runtime이다. runtime의 done·자체 memory·approval이 Core 권위를 대신하지 않는다.

Core의 domain 상태에서 작은 `WorkSummary`, `Review`, `Question`, `Action` 등의 view/action projection을 만들고 ANSI TUI, Tern native TSP, web/mobile chat이 소비한다. 공통화 대상은 의미와 행동 계약이다. terminal widget·GPU·모든 화면 component를 Core 추상화로 끌어올리지 않는다. 비개발자 채팅은 목적·결과·필요한 질문을 보여 주며 raw terminal mirror가 되지 않는다.

모든 action은 인증·realm membership·허용 capability를 서버에서 확인한다. 승인에는 artifact/base digest·policy revision·실제 연결 account·target·action·금액 한도·expiry를 묶고, 실행 직전에 재검증한다. idempotency로 중복 요청을 처리한다. stale node, 오래된 화면, 복제된 palette action은 권한이 아니다. worker가 출력한 가짜 버튼·성공 문구도 trusted action이나 Receipt로 승격하지 않는다.

**[공식 문서]** Tern plugin은 실행 OS 사용자 권한으로 파일·프로그램·네트워크·shell input에 접근할 수 있고 이를 좁히는 permission system이 없다고 명시한다. Luau sandbox는 악성 plugin으로부터 사용자나 tenant를 격리하는 장치가 아니다. ([plugin 보안](https://docs.stencil.so/tern/concepts/security.md))

따라서 초기 native 연동은 기존 PTY/TSP 경로를 우선한다. plugin이 필요해도 최소 범위로 검토하며, UI confirm·profile·host/window 분리를 보안 경계로 삼지 않는다. 같은 OS 사용자 권한의 악성 plugin으로부터 로컬 비밀을 보호한다고 주장할 수 없다. tenant 격리는 별도 실행 경계와 Core 인증으로 검증하고 production secret은 별도 apply executor에 둔다.

## 5. 호환성과 복구 계약

**[공식 문서]** window reattach의 surface snapshot 전달과 daemon restart 이후의 복원은 다르다. 문서는 daemon crash/restart 뒤 새 shell을 시작하고 inline/flow surface·command block을 read-only scrollback으로 복원하며 screen surface는 복원하지 않는다고 설명한다. frame ack는 window가 그렸다는 뜻이다. Work 완료·검증 통과·프로세스 생존·안전한 재실행 증거가 아니다. ([운영 계약](https://docs.stencil.so/tern/protocol/operations.md))

**[권고]** 복구는 다음 순서로 처리한다.

1. 창 닫기·연결 단절 뒤 client가 Core에서 Work revision, 실행 lease, 취소 상태, 미해결 질문·승인·반영 결과를 다시 읽는다.
2. worker/session 생존은 실제 실행기와 lease로 확인한다. 화면 복원만으로 실행 중이라고 표시하지 않는다. 재시작한 shell은 이전 worker와 구분한다.
3. lease 세대·fencing으로 오래된 worker의 새 action을 막는다. 취소 뒤 이미 시작된 effect는 readback으로 조정한다.
4. apply 응답 유실은 결과 불명이다. idempotency 또는 대상 readback으로 확인하기 전 반복하지 않는다. 부분 반영은 보상·rollback·수동 복구 조건을 남긴다.
5. UI는 확인된 상태를 표시하고 초안을 복원한다. 만료·변경된 승인을 자동 갱신하거나 재승인하지 않는다.

TSP 연결은 handshake와 실제 확인 가능한 version/capability에 따라 지원 subset을 선택한다. `TSP_VERSION=1`만으로 최신 element 전체를 보장하지 않는다. optional kind·미지원 표현은 대체 view로 처리하고, 필요한 지원을 확인할 수 없으면 ANSI 경로를 쓴다. 현재 앱 `0.9.12`와 최신 문서의 지원 범위를 동일시하지 않는다. SDK API에도 version number가 없고 capability 확인을 권한다는 문서 경계를 유지한다. ([배포·호환성](https://docs.stencil.so/tern/guides/distribution.md))

일반 terminal은 handshake 무응답 시 ANSI를 유지하는 문서상 경로가 있다. **실제 ordinary-terminal 검증은 남아 있다.** ANSI fallback은 핵심 행동을 유지하고 rich 표현만 달라야 한다. SSH·tmux의 APC 전달·재연결·터미널 크기·key 충돌은 지원 조합별 시험 뒤 표기한다.

delta·append·coalescing·credit pacing·가상화는 표현 비용을 줄이는 데 재사용한다. 승인·검증 event를 화면 최적화 때문에 생략하지 않는다. `gone`·retention 만료 뒤에는 Core의 권한 있는 최신 projection으로 재구성하고 stale control을 거부한다. blob·첨부·snapshot·cache에는 realm별 접근·보존·삭제 정책을 적용한다. 화면·scrollback·로그에 credential을 넣지 않고 악성 output의 링크·escape·가짜 승인 표현을 검사한다.

vendor가 소개하는 daemon·desktop/iPhone/browser·세션 복원은 **[공식 문서의 주장]**이다. ‘never lose work’를 reboot 후 모든 실행과 부작용이 안전하게 이어진다는 보장으로 확대하지 않는다. ([공식 소개](https://stencil.so/tern))

## 6. 유지하는 전체 제품·사업·운영 방향

**[권고]** 최종 제품은 자율적으로 일을 끝내 주는 플랫폼이다. 비개발자 web/mobile chat, 개발자 TUI·CLI·API가 같은 Core를 쓴다. 첫 유료 고객은 여러 AI 코딩 작업의 상태 확인·재설명·검토·반영에 시간을 쓰는 개인 개발자와 소규모 팀이라는 **가설**로 둔다. 판매할 가치는 예쁜 terminal이나 Receipt 자체보다 검증된 완료와 사용자 부담 감소다.

반증 실험은 새 SaaS 선행 개발 없이 허용된 실제 작업을 기존 도구로 수행하는 유료 파일럿이다. 기존 방식 대비 실제 대금·반복 사용·완료·개입 시간·재작업·모델 및 worker 비용·검증·지원 시간을 비교한다. 기준은 실행 전에 정한다. 반복 사용·부담 감소가 없으면 고객군·흐름을 수정하고, 경제성이 없으면 hosted 투자를 보류한다. 가격·quota·출시일은 확정하지 않는다.

초기 dogfood는 사용자 소유 BYOK/API·허용 OAuth·등록된 local endpoint 중 검증된 연결로 시작한다. 무료/GLM 경로도 작업 평가와 정책을 통과하면 선택할 수 있다. managed 포함 사용량은 비개발자 진입의 선택지이며 확정 기본값이 아니다. 소비자 구독의 개인 사용 허용을 서버 토큰 보관·대리 호출·재판매 허용으로 확대하지 않는다.

사용자는 허용 범위에서 model/effort를 선택하고 Core policy가 realm·데이터·capability·budget·action을 최종 허용한다. 무허가 provider·회사/개인 계정 fallback은 없다. 변경은 새 Attempt와 문맥·권한·비용 재검사로 남긴다. cheap-first는 저위험·가역·저렴한 실패 검증이 가능한 작업의 비교 후보이며 어려운 작업은 충분한 모델로 바로 보낸다.

예산은 호출 전 작업·사용자·realm에서 예약하고 정산한다. 모델 외 worker·preview·저장·재시도·검증·지원비도 계측한다. 비용 불명은 0원이 아니며 시간·동시성 제한만으로 금액 상한을 보장하지 않는다. managed 공개 전에는 약관·남용 제한·중지·환불·지원 책임을 검증한다.

기억은 Work 문맥을 자동 유지하되 모든 대화의 영구 저장을 기본으로 삼지 않는다. 사전 허용된 범위의 저위험 선호·확인 사실은 출처와 함께 자동 기억하고 알림·되돌리기·수정·삭제를 제공한다. 상충·추정은 후보로 두고 권한·예산·정책·공유 정본 변경은 별도 승인한다. owner·realm·source·revision·유효기간·supersedes를 관리하며 삭제를 파생 기억·index/cache·eval·prompt 의존성에 전파한다. 외부 provider·backup 삭제 범위는 미검증이다.

controlled OMP distribution fork는 초기에 시작하되 얕은 배포 fork에서 필요한 변경을 허용하고 upstream을 선택 반입한다. pin·patch queue·변경 이유·재현 build·불변 release·보안 intake·rollback을 유지한다. pin만으로 보안이나 교체성이 생기지 않으며 stub 뒤 실제 두 runtime conformance를 통과해야 한다.

Paperthin의 mental-model/recipe, Hermes의 기억 검색·점진적 도구 공개·전송 원리는 비용·위험·평가 이득에 따라 선택 흡수한다. 새 자산은 출처·license·version/digest·권한·capability·task eval·제한 rollout·rollback을 거친다. 거대 기본 skill 묶음·상시 다중 모델·자동 active rule 수정은 도입하지 않는다.

Forge는 전체 환경, Blueprint는 판단·정책, Smith는 역할 구성, Anvil은 접점, Assayer는 검사 제안, Bellows는 관찰, Whetstone은 사람 학습·개선 후보를 뜻한다. 차별성은 이름이나 자기평가가 아니라 권리와 접근 범위 안에서 축적한 검증 절차·지식·정책·평가·호환성 자산이다.

첫 인프라는 단일 control-plane, SQLite WAL·migration·outbox, queue/lease, 격리 worker, artifact 저장소, credential broker와 별도 apply executor다. realm별 writable authority는 하나이며 live DB를 파일 동기화하지 않는다. worker는 worktree만으로 격리됐다고 보지 않고 파일·프로세스·자원·network·host socket을 제한한다. tenant는 인증된 membership에서 결정하고 memory·cache·artifact·backup을 분리한다. local endpoint는 명시 등록과 SSRF/egress 검사를 거친다. Kubernetes·분산 scheduler는 선행 조건이 아니다.

## 7. 예약 홈페이지가 끝까지 이어지는 경험

다음은 **[권고·미구현 목표 흐름]**이며 첫 공개 repo 개선 proof를 대신하지 않는다.

1. 사용자가 채팅에서 ‘내 가게 예약 홈페이지 만들어줘’라고 말하면 제공 항목·수용량·영업시간/시간대·취소 규칙·공개 대상처럼 결과를 바꾸는 최소 질문만 한다. Work ID와 개발 용어는 기본 화면에서 숨긴다.
2. 허용된 자료·모델·예산으로 격리 실행한다. 개발자는 같은 Work를 TUI에서 보고 다른 Work로 전환했다 돌아와도 초안·검토 위치·질문이 이어진다. 비개발자에게는 필요한 판단과 진행 결과만 전달한다.
3. 접근 통제된 mobile/desktop preview에서 실제 저장 경로를 사용해 동시 중복 예약·경계 시간·휴무일·시간대·취소/재예약·오류와 재시도를 검증한다. screenshot·mock·단위 테스트만으로 완료 처리하지 않는다.
4. 지정 후보의 artifact/base, 실제 연결 계정·게시 대상·공개 범위·비용 항목과 승인 금액 상한·운영 의무·복구 방법을 보여 준다. 실비·추정·불명을 구분하고 필수 금액 한도를 지킬 수 없으면 차단한다. 해당 후보의 정확한 publish action만 승인하며 후보·대상·권한이 바뀌면 재승인한다.
5. 별도 executor가 publish하고 실제 주소·버전·공개 범위·서비스 상태를 readback한다. 통제된 시험 데이터로 예약 동작도 확인한다. 실제 고객 개인정보·알림·결제는 별도 허용 없이 시험하지 않는다.
6. 응답 유실은 완료가 아니다. 중복 publish를 막고 readback·이전 버전 복귀·보상·수동 조정으로 이어 간다. 다음 대화에는 허용된 상호·운영시간·디자인 선호를 활용하되 예약자 개인정보는 비서 기억으로 승격하지 않는다. 운영시간 변경은 기억을 대체하고 새 Work·검증·게시 권한으로 반영한다.

이번 Tern screenshot은 이 흐름의 구현·검증 증거가 아니다.

## 8. 실행 단계와 완료 gate

아래는 향후 실행 권고다. 기존 plugin **CURRENT 수리와 장기 플랫폼은 별도 track**으로 유지한다. 제공 기록의 로컬 회귀 통과를 Linux·CI·host 검증이나 G1 전체 완료로 바꾸지 않는다.

| 단계 | 의존성과 완료 조건 |
|---|---|
| G0a | 기존 WIP·source·설치본·cache 기준선과 실제 복원 리허설. 현재 Git 상태는 새 실행에서 확인해야 하며 이번에는 조회하지 않았다. |
| G0b | G0a와 독립 가능한 계약 검토 진행. Work/action·권한·예산·기억 수명·view projection·ANSI/TSP 지원표·실제 identity/capability fixture를 정한다. OMP fork 범위·보안 intake와 Go+TS/TS ADR은 설치·취소·복구 실험으로 결정한다. |
| G1 | G1a는 G0a 뒤 기존 안전성·기록·적재·handoff 수리. G1b는 host 능력 확인 뒤 두 native pack 발견·설치·제거 검증. Core는 G0b 뒤 구축하며 TUI·채팅 사용자 시험을 시작한다. |
| G2 | 필요한 수리·Core 계약 뒤 runtime 하나·공개 repo 하나에서 개선→독립 검증→질문→정확한 승인→별도 로컬 apply/readback→복구를 완결한다. ANSI TUI의 palette·Work 전환·초안·diff/증거·입력·승인·취소·재접속과 Tern의 대응 native 향상을 같은 흐름으로 검증한다. 로컬 web chat·반응형 질문/승인·최소 Inbox·scoped memory의 다음 대화 재사용/수정/삭제도 같은 Work에 연결한다. 단일 장비 wake/restart를 포함한 내부 alpha다. |
| G3 | G2와 G1b 뒤 실제 두 runtime·두 pack·성격 다른 repo profile·설치본·native/managed 회귀를 통과한다. ANSI와 지원 Tern 조합, SSH/tmux, 입력·접근성·긴 이력, web/TUI 동시 결정과 stale 승인 거부를 검증한다. 예약 profile은 실제 앱과 통제된 publish/readback의 별도 gate이며 Core 전체 출시의 일괄 필수 조건으로 묶지 않는다. |
| G4 | G3 기반에서 원격 모바일 인증·상시 authority/worker·전원/연결 장애를 검증한다. managed 공개·실고객 예약 운영·팀 기능은 약관·격리·데이터·비용·운영 gate를 각각 통과한 범위만 출시한다. |

G2는 전체 G1b나 모든 host·viewer를 기다리지 않지만 자신이 의존하는 수리는 통과해야 한다. 반응형 채팅은 초반부터 설계·시험하고 원격 상시 모바일 운영은 G4에서 검증한다. 독립 desktop·native mobile 앱, 다수 document viewer·voice는 별도 가치·접근성·비용 증거로 선택한다.

bootstrap은 현재 사용하는 Tern·OMP·기존 CodeForge로 실제 작업을 하며 사람이 최소 WorkSpec·검증·질문·승인·readback을 연결하는 방식이다. 재설명·작업 탐색·초안 손실·모델 선택·잘못된 완료를 기록해 우선 개선하고 새 계약으로 옮긴다. 새 Core 완성을 dogfood의 선행 조건으로 요구하지 않는다. 이번에는 새 loop나 agent를 실행하지 않았다.

## 9. 검증 한계와 이전 안에서 달라진 결정

**[실제 관찰]** 이번 입력에 있는 실행 증거는 독립 headless의 분할·palette 표시·공개 TSP 카드·정적 한글 smoke뿐이다. 공식 headless 도구의 기본 환경 설명과 관찰 결과도 구분한다. ([공식 자동화](https://docs.stencil.so/tern/scripts/index.md))

**[미검증·향후 gate]** 실제 IME 조합·제출·취소, keyboard-only 전체 동선, clipboard·첨부, screen reader·focus·색 대비, ANSI 행동 동등성, SSH/tmux, window/daemon/worker restart, 긴 이력·resize·지연·메모리, 모바일·원격은 제품 시험이 필요하다. 멀티 surface stale approval, worker crash·취소·늦은 결과, lease 경합·중복 apply·응답 유실·readback unavailable, budget 경합·비용 불명, 타 tenant의 memory/artifact/approval/secret 주입·검색 누출, 악성 output·plugin도 시험한다. 성공으로 오인되거나 권한이 확대되거나 effect가 중복되면 실패다.

provider별 로컬/서버 약관·OAuth·포함 사용량, OMP/SDK와 전이 의존성 고지, worker·tenant·secret 격리 실증, 개인정보 삭제·backup, 실제 지불·반복 사용·지원비는 관련 구현·출시 gate로 남는다. 기준 없는 성능 수치나 현재 가격·quota는 만들지 않는다.

**이전 안에서 바뀐 결정:** Tern 연동을 포괄적 미검증으로만 두던 판단을 공개 SDK·TSP·OMP 경로와 제한된 실제 관찰로 구체화했다. 기본 terminal 품질과 Tern 향상을 G2 단일 flow에 넣었고, 작은 view/action projection·행동 동등한 ANSI fallback·복구 계층·독립 desktop 선택 기준을 추가했다.

**그대로인 결정:** 공유 Core와 다중 접점, 초기 controlled OMP fork, 사용자 소유 모델 시작 경로와 managed 선택지, 자연스러운 scoped memory, 개발자 우선 유료 가설, 첫 repo proof와 예약 profile 분리, CURRENT 별도 track, 권한·검증·정확한 승인·readback 중심 완료 계약을 유지한다.

**종합 설계안 전달은 이 보고서로 완료한다.** 제품 구현·배포·시장 검증, Tern 앱 fork 권리 검증은 완료되지 않았다. 이번에는 도구·shell·web·다른 대화·파일을 조회하거나 모델을 추가 호출하지 않았고, 코드·저장소·정본·설정·plugin·기존 Tern 창과 session을 변경하지 않았다.

---

### 검토 산출물과 범위
- 위 내용은 이전 전체 원문 검토를 이어받아 Tern 공개 근거·실제 격리 headless 관찰을 반영한 새 통합 의사결정안입니다. CodeForge 구현이나 정본 승격은 아닙니다.
- 새 개인 Codex 세션에서 통합안을 작성하고, 별도의 새 개인 Codex 세션이 R1~R16과 source를 대조했습니다. 추가 회사 모델 호출은 없습니다.
- 이전 검토: `/tmp/codeforge-review.BetIWmZd/codeforge-final-review.md`
- 공개 근거와 관찰 기록: `/tmp/codeforge-review.BetIWmZd/tern-study/research-evidence.md`
- 실제 headless PNG·layout: `/tmp/codeforge-review.BetIWmZd/tern-study/shots/observe/`
- 별도 검수: `/tmp/codeforge-review.BetIWmZd/tern-study/integrated-plan-audit.json`
- 저장소·코드·계획 정본·설정·기존 Tern 세션은 수정하지 않았고, commit·배포·plugin 설치를 하지 않았습니다.
