# CURRENT — CodeForge 개선 계획

2026-11-07 · G0b 첫 좁은 구현·실제 검증 기록 보완 · 이전 기획 문서 브랜치 `docs/agentops-platform-plan` · 기획 문서 4개 게시·원격 SHA 일치 확인 기준 `a2ecb128d9928e7645a345f5fccd14a35b1028ee` · 이전 문서 준비 기준 `388107defbca80cef612e14716ea2dc0c7242cb0`.

전체 목표는 웹/모바일의 쉬운 채팅 진입점과 개발자 TUI·편리한 workspace가 같은 Core의 Work·정책·증거·승인·복구·scoped memory를 사용하는 플랫폼이다. 초기 controlled OMP fork와 기존 terminal 기반을 재사용하고 upstream은 검증 후 선택 반입한다. Tern은 선택 host이며 필수 tenant sandbox가 아니다. 비개발자만을 대상으로 좁히지 않는다.

## 먼저 읽을 문서

1. [최신 상세 정본](imported/codeforge-final-plan-with-terminal-ux.md): 전체 설계·제품/사업 방향·실행 gate·검증 한계의 유일한 상세 정본.
2. [기존 실행 계획](../plan/code-forge-final-improvement-plan-2026-10-18.md): 기존 유효 계획·호환 요구와 최신 결정 보완. 특히 §1의 검토 범위, §5의 디자인 상태, §6~7의 과거 단계 매핑을 확인한다.
3. [문서 지도](agentops/README.md): 서비스 요약과 보조 설계 연결.

## 상태와 이번 승인 범위

기획 통합안과 그 원문에 기록된 실제 Claude 독립 검토·개인 Codex 대조/감사는 지정 자료 범위의 계획 검수다. 제품 구현·보안/격리 실증·시장 검증·출시 완료가 아니다. 그 뒤 사용자의 별도 구현 승인으로 실제 개인 Codex 세션들이 첫 실험을 구현했고 부모가 실제 실행·검증했다. 이번 마무리는 실행 가이드·이 CURRENT·기존 실행 계획·CHANGELOG 네 문서에 한정하며, 앱·테스트·추가 모델 실행을 반복하지 않는다.

단계적으로 구현 계획을 확정하는 첫 실제 결정에서 사용자는 **데스크톱의 ‘작업 진행 중’ 기본 구조로 결과 작업대 중심을 선택했다.** 홈페이지·문서·기타 산출물이 중앙의 주인공이고, 대화는 결과를 지시하는 열고 닫는 보조 영역이다. 작업 탐색은 얇게 두고 질문·변경·검증·승인은 해당 결과와 연결해 접근한다.

첫 요청 순간에는 비개발자의 쉬운 채팅 진입점을 유지한다. 모바일은 채팅을 기본으로 결과·검토로 이동한다. 개발자 TUI는 같은 Work의 의미·상태·행동을 키보드로 제공하며 웹 레이아웃을 복제하지 않는다.

두 번째 실제 선택에서 사용자는 **개발자 TUI와 원격 사용 우선**을 명시적으로 선택했다. 웹·모바일과 결과 작업대 방향은 후속 단계로 유지하며, 화면 디자인·시각 방향 확정을 첫 Core 구현의 선행 조건으로 두지 않는다. 최초 수직 흐름 목표는 **TUI 요청 → 실제 실행 → 검증 → 필요한 승인 → 반영 후 확인(readback) → 원격 접속을 끊었다 다시 연결해 같은 Work 확인**이다. TUI는 authoritative 작업 상태의 소유자가 아니며 화면 단절과 작업 수명을 분리한다. 접속 단절·재접속·취소·복구를 계약에 포함하고, 중단 후 외부 작업을 무조건 재시도·재반영하지 않는다.

초기 원격은 사용자 자신이 관리하는 머신·서버에 SSH로 접속하는 경로를 우선 검토한다. 공개 인터넷용 다중 tenant SaaS·격리 완성을 뜻하지 않는다. 모델 credential은 보호된 실행 환경에 남기고 메신저로 받지 않으며, 모델·계정 silent fallback 금지와 사용자별 격리 원칙을 보존한다.

텔레그램 등은 후속 접점으로 알림·상태조회·간단 요청부터 검토한다. 게시·삭제·비용 발생 승인은 사용자·권한·대상 버전·유효성·중복 방지 경계를 갖춘 뒤 검토하며, 처음부터 원격 shell·포괄 승인 권한을 주지 않는다. 텔레그램 구현·새 bot 생성은 현재 승인 범위가 아니다. 네이티브 데스크톱·모바일 앱은 OS 통합·알림·기기 기능의 실제 필요를 확인한 뒤 선택하며 첫 구현 범위에서 제외한다.

비개발자 시장·쉬운 채팅 방향은 유지한다. 개발자 dogfooding 성공만으로 비개발자 사용성·사업성을 입증했다고 보지 않는다.

이 정보 구조 선택 자체는 **웹 화면 방향만 승인**한 것이다. 웹의 색·폰트·세부 레이아웃·구현·실제 prototype은 승인되지 않았다. 이후 별도 승인된 TUI 첫 실험과 구분한다. 첫 시안은 사용자가 ‘완전 클로드 디자인 그 자체’라고 거절하고 ‘그냥 멈춰’라고 중단했다. 여전히 기각·중단 상태이며 재사용하지 않는다. **기각 시안의 자동 재개 금지.** 결과 작업대 선택을 ‘다크 3단 패널이 곧 차별성’이라는 결론으로 바꾸지 않는다. CodeForge의 대장간 메타포와 제품 고유성을 보존한다. HTML/CSS/JS·디자인 명세·스크린샷·runner/browser tooling·로컬 로그는 반입하지 않는다.

기존 plugin 수리 track과 새 플랫폼 G0a/G0b/G2/G3/G4 gate는 별도로 유지한다. G0a는 복구 가능한 기준선, G0b는 최소 계약·실증, G2는 단일 runtime·공개 repo의 로컬 흐름과 기본 기억, G3는 실제 두 runtime·두 pack·지원 조합, G4는 원격 모바일·상시 authority/worker의 검증이다. 세부 의존성과 출시 조건은 상세 정본 §8을 따른다.

**G0b first narrow slice는 구현·실제 검증 완료**다. [실행 가이드와 증거 요약](../experiments/g0b-tui-remote/README.md)에 CLI 명령·개인 guard 환경·TUI 키·SSH·unknown 복구를 기록했다. 구현 위치는 `experiments/g0b-tui-remote/`이며 Python stdlib·private SQLite·단일 OS 사용자·합성 파일 범위다. 첫 runtime은 사용자가 별도 선택한 개인 `codex-cli 0.167.0`, 명시 요청 모델은 `gpt-6.1-sol`이다. 실제 모델 호출은 1회이고 backend effective model은 미관측이며 계정·모델 자동 fallback은 없다. 이 실행은 OMP RPC가 아니다. OMP 18.16.0 공개 source 조사에서 독립 OAuth profile 필요를 확인했지만 공식 Codex auth importer를 확인하지 못해 위 runtime을 선택했다.

부모가 실행한 unittest는 47개·16.084초 OK다. loopback OpenSSH의 실제 새 연결에서 CLI로 NEW 생성/조회 → detached run → 접속 종료 → 재접속 후 같은 Work REVIEW_READY·호출 예약 1/1을 관측했다. TUI q detach·후보 승인·별도 반영은 로컬 PTY에서 실제 조작했고, 독립 oracle subprocess 16/16과 새 SSH CLI의 APPLIED/readback을 확인했다. 원격 SSH의 TUI 렌더링은 검증하지 않았다. 승인 전과 승인 직후 target 원본 유지, 같은 approval/key 재요청의 target device/inode/mtime_ns 불변·receipt 동일, 완료 TUI 재접속도 확인했다. 독립 개인 코드 검토의 nested workspace alias 우회는 부모 throwaway 재현으로 수정 전 실패·최소 수정 후 차단/target 불변을 확인하고 영구 회귀에 포함했다. 구현 중 runtime_failure 누락과 placeholder gate도 해결했으며 RUNTIME_FAILED·RUNTIME_UNKNOWN·CANCELLED를 구분한다. raw terminal 모양의 디자인·사용성 평가를 통과했다는 뜻은 아니다.

**G0a/G0b 전체 gate는 미완료**다. provider identity의 충분한 증명·backend model 관측, 공급자 상업 OAuth 약관·원가/금액 cap, OMP isolated personal OAuth/RPC 접속·취소·복구, 실제 다른 호스트·원격 OS 차이, packaging·격리·기억·복구 등 남은 계약을 생략하지 않는다. 현재 budget은 호출 예약 횟수 cap이며 USD/token hard cap이 아니다. 공개 multi-tenant, Tern SDK, 네이티브 앱·웹·Telegram, provider 과금 취소/외부 effect rollback, OS 전체 sandbox는 미구현/미검증이다. CLI read-only·clean env·도구 이벤트 감시는 OS 전체 read/network 격리가 아니다.

기존 기획 문서 네 개는 `a2ecb128d9928e7645a345f5fccd14a35b1028ee`로 게시됐고 실제 원격 readback의 SHA 일치까지 확인됐다. 이전의 ‘commit/push하지 않았다’는 문서 후보 당시 상태이며 현재 게시 상태가 아니다. main·릴리스·제품 배포는 승인 범위에 포함되지 않는다.

첫 실험 코드·회귀 테스트·실행 가이드와 기존 계획 상태 갱신을 `docs/agentops-platform-plan`에 게시하는 승인은 이미 받았다. **첫 실험의 제품코드와 이번 문서 보완은 아직 commit/push하지 않았다.** 이번 문서 마무리는 게시·버전 범프·배포를 수행하지 않는다. 향후 게시도 정확한 승인 범위와 공식 guard·기존 Git hooks를 지키며, 최종 커밋 자신의 SHA를 본문에 미리 쓰지 않는다.

root main의 dirty 상태·사용자 변경·인덱스와 오래된 미존재 worktree 등록은 보존됐다. 첫 구현은 현재 별도 detached checkout에 있다. root의 미추적 동명 CURRENT는 읽거나 복제하지 않고 이전 게시 기준 문서 구조를 유지한다. 이번 마무리는 네 문서만 다루며 코드·테스트·설정·`.git`·상세 원문·다른 worktree를 변경하지 않는다. 자기 커밋 SHA를 쓰는 amend loop는 만들지 않는다.

## 무결성과 이식 범위

- 원문 반입 SHA256: `4285f40f2ac842dbd3f5246456e61d58dfe80ba6e8463592c23515233184f7c7`.
- 최신 상세 정본 SHA256: `4285f40f2ac842dbd3f5246456e61d58dfe80ba6e8463592c23515233184f7c7`. 원문 바이트를 그대로 보존하므로 위와 동일하며 내용 보완은 기존 실행 계획에만 둔다.
- 이전 기획 문서 게시 기준의 기존 실행 계획 검증 SHA256: `02f887b56da1f69354f485766b81be6517de48dae60c6ae3bb775f187084053d`. 이번 보완 전 검증값을 보존한 것이며 현재 문서의 SHA가 아니다.

집에서 필요한 설계 본문 전체는 최신 상세 정본과 위 레포 상대 링크에 있다. 상세 정본 말미의 과거 임시 증거 경로는 당시 검토의 출처 포인터이며, 그 파일 없이도 설계 본문과 기록된 검증 한계는 읽을 수 있다. 리뷰 원문·회사 bundle·headless 이미지/layout·감사 JSON·실행 로그는 이식하지 않았다. 따라서 과거 검토/관찰을 원자료로 재현하거나 독립 감사할 자료까지 함께 보존됐다는 뜻은 아니다. 원문 속 ‘이번’과 ‘정본 승격 아님’ 등은 원문 작성 당시의 상태이며 현재 문서 지위는 이 진입점과 기존 실행 계획이 정한다. 공식 반입 receipt·사용 근거 기록은 후속 guard admit에서 다루며 공개 문서에 복사하지 않는다.

## 미결정과 다음 한 단계

데스크톱 작업 진행 중의 결과 작업대 중심 정보 구조와 개발자 TUI·원격 사용 우선 순서는 확정됐다. 웹의 필수 정보·작업 흐름, 시각 방향·실제 레퍼런스·작은 와이어프레임 검토는 후속 단계에 남기며 바로 할 일로 두지 않는다. 첫 요청의 채팅 진입점·모바일·TUI의 경계는 위 선택 범위를 따른다. 첫 실험의 경계는 이 저장소의 `experiments/g0b-tui-remote/`, Python stdlib·SQLite, 개인 Codex CLI와 macOS loopback SSH로 정해 실제 검증했다. 제품 이름·최종 언어/배포 구조·controlled OMP fork 실제 변경 범위·최소 실행 계약의 정식 채택·후속 runtime/host 조합은 아직 확정하지 않았다. provider별 BYOK/허용 OAuth·local/managed 약관과 원가, 사용자 간 인증·기억·비용 격리 실증, 삭제/backup·유료 반복 사용은 결정 또는 검증 대기다. Paperthin/Hermes는 근거 확인과 선택 평가가 남은 참고 후보이며 필수 의존성·도입 완료가 아니다. 가격·quota·라이선스 조건을 새로 확정하지 않는다.

**다음 한 단계:** 이 첫 실험을 근거로 최소 실행 계약(상태·action·독립 검증·승인·readback·단절/재접속/취소/unknown 복구)을 검토·확정하고, OMP isolated personal OAuth/RPC 접속 실증 또는 실제 다른 호스트 원격 실증 중 우선할 한 단계를 좁힌다. 이미 선택한 개발자 TUI·원격 타깃, 첫 개인 Codex runtime과 웹 후속 순서를 다시 묻지 않는다. 기존 plugin 수리와 새 Core/controlled fork G0b는 분리하며, 새 디자인·프로토타입이나 기각 시안을 자동으로 재개하지 않는다.

이번 문서 확인은 네 문서의 내용 대조와 내부 상대 링크의 현재 checkout 파일 존재 확인에 한정한다. 앱·테스트를 재실행하지 않았고 외부 링크·앵커 도달은 검증하지 않았다. 실제 검증 근거의 파일명·통과범위와 한계는 실행 가이드에 기록했으며 로그·상태 DB·SSH key·생성 candidate·개인 메타데이터를 저장소에 반입하지 않는다.
