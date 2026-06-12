# Changelog

code-forge 패치노트. 버전 범프 커밋에 본 파일 갱신이 **반드시 포함**된다 (절차: AGENTS.md §릴리스 절차).
형식: [Keep a Changelog](https://keepachangelog.com/ko/) 변형 — 추가/변경/수정/제거, 사용자 관점으로 서술.

---

## [4.6.0] — 2026-06-12

### 추가 (마스터플랜 2단계 — "작업 시작할 때 길안내 (Foreman)")
- **Foreman 관문** — 자연어 작업성 발화("만들어줘/구현해줘/추가해줘" 등) 감지 시 "① /start로 정식 진행 ② 그냥 진행(복잡도 LOW/MED/HIGH + 권장 effort 명시)" 선택지를 모델이 1회 제시하도록 컨텍스트 주입. **세션당 1회**(스로틀 마커), 슬래시 명령·10자 미만 발화엔 침묵. 강제 아님 — 영구 휴면이던 auto-flow-trigger.sh(UserPromptSubmit) 재활용
- **완료 시점 마무리 제안** — 턴 종료 시 변경 파일이 있는데 progress.md가 1시간 내 미갱신이면 다음 프롬프트에서 "progress 정리 또는 /handoff" 1회 안내. Stop 훅 출력은 모델에 미도달(공식 문서 판정)이라 route.json `wrapup_hint` + 다음-프롬프트 백스톱 구조. quality.jsonl에는 미기록(게이트 통계 오염 방지)
- **스킬 4종(/start /test /e2e /debate) 발화 트리거 문구** — description에 자연어 트리거 예시 보강 (모델이 스킬을 떠올리는 빈도 개선, /handoff 패턴 복제)

### 변경
- auto-flow-trigger.sh의 전역 flow CLI 가드를 티켓 분기(C2) 직전으로 강등 — flow 미설치 환경에서도 Foreman(C0/C1)은 동작. 티켓→flow tc select 회로는 동작 무변경
- 분류용 grep 전체에 `|| true` 가드 — set -e 하 훅 침묵 사망 방지 (적대 검증 must_fix 7)

### 측정 (Foreman 철회 기준의 전제 — 적대 검증 must_fix 4)
- usage.jsonl `type:skill` 채널 충실도 실측: 기록 2/2 모두 스킬명 정상(`code-forge:start`) — 4주 후 제안→전환 측정에 사용 가능

## [4.5.0] — 2026-06-12

### 수정 (마스터플랜 1단계 — "검증이 돌았는지 보이게 + 만년 빨간불 수리")
- **품질 게이트 always-fail 수리** — 실측: 실사용 프로젝트에서 384회 중 통과 0회의 원인이 코드가 아니라 게이트 설정이었음
  - tsc: 루트 실행(루트 tsconfig 없는 모노레포는 무조건 exit 1) → **변경 파일에서 가장 가까운 tsconfig 워크스페이스만 검사** (최대 3개, 못 찾으면 fail 대신 warn+스킵)
  - eslint: "출력 있으면 실패" 판정(설정 오류 메시지에도 실패) → **exit code 판정** (1=린트 오류, 2+=설정 오류 → warn, 차단 안 함)
  - 같은 파일 반복 경고(최대 27회 기록) 중복 억제
- **emit-event가 deep-merge로** — producer마다 자기 필드만 보내면 됨. quality-gate의 last_gate와 /start의 complexity가 서로 안 지움

### 추가
- **게이트 결과가 route.json에 기록** — 매 턴 종료 시 pass/fail/skipped + 실패 블록. "이 작업이 검증을 탔는가"에 항상 답함 (침묵 스킵이던 변경-없음 경로 포함)
- (forge-glow `e8f5c8d`) HUD `FORGE_GLOW_GATE_LAST=1` — 누적 카운트 대신 "이번 턴 검증" 표시, 경고가 3줄째를 교체해도 보존. ctx 80% 알림에 "→ /handoff" 안내

## [4.4.0] — 2026-06-12

### 추가
- **`bin/forge emit-event`** — 실시간 라우팅 스냅샷(`.claude/state/route.json`) 원자 갱신. latest-only 덮어쓰기 — 히스토리는 usage.jsonl/quality.jsonl 담당 (HYBRID transport, event-schema.md §1)
- **`bin/forge status --json`에 `route` 키** — v1-additive (스키마 범프 없음). route.json 없으면 `null`
- **`references/routing-policy.md`** — 라우팅 정책 단일 진실: 라우팅 가능한 축(티어/벤더 — 버전은 표시 전용), 핀 정책, effort 정직성(Claude 서브에이전트 상한은 advisory)
- state-schema.md §6 route.json 등재 + 버전표 1.1/1.2

### 변경
- `instructions/agent-patterns/model-routing.md` → 포인터 스텁 (구 티어 매트릭스 113줄은 `archive/instructions/` 보존, 참조 3곳 갱신 — codex 에이전트는 이제 더 가벼운 routing-policy를 주입받음)

### 기록
- **모델 핀 정책 확정 (사용자 결정 ⓐ)**: opus 핀 2개(architect/analyst) 유지 — opus-4-8 고정. haiku 2 + sonnet 10도 비용 격리로 유지. 근거: 티어 별칭은 main 모델이 아니라 티어 최신으로 해석된다는 실측 (2026-06-11)

## [4.3.0] — 2026-06-12

### 추가
- **`/handoff` 스킬** — 사용자 통제 세션 핸드오프. 대화에만 존재하는 맥락(결정·이유·미결질문)을 progress.md에 기록하고 새 세션 킥오프 프롬프트를 클립보드에 복사. auto-compact 대신 문서 기반으로 세션을 넘기는 루틴의 스킬화. `/handoff <문서경로>`로 지정 진행 문서의 ★CURRENT 교체 갱신도 지원
- **`docs/REFERENCE.md`** — 에이전트/스킬/훅/상태/규칙 카탈로그의 단일 소스 (온디맨드 문서)

### 변경
- **CLAUDE.md 211→51줄, AGENTS.md 170→76줄** — 카탈로그 표를 REFERENCE.md로 이동(정보보존), 매 세션 자동 주입 -306줄. AGENTS.md는 멀티모델 진입점 델타(수정 규칙+금지 작업)만 유지
- 스킬 카탈로그를 디스크 기준으로 재생성 — 누락 4개(e2e, setup-e2e, smith-build, smith-create-agent) 최초 등재, 개수는 산출 명령 표기로 대체

### 수정
- 팬텀 스킬 4개 제거 — AGENTS.md가 나열하던 `/done` `/bug-fix` `/refactor` `/quality`는 v4.0에서 폐지(규칙·훅으로 흡수)된 것 (대체 매핑: docs/CATALOG.md)
- AGENTS.md 자기모순 해결 — "agents/ 직접 편집"(수정 규칙) vs "agents/ 직접 수정 금지"(금지 표) 공존 → 금지 대상을 컴파일 출력물 `.claude/agents/`로 정정

## [4.2.2] — 2026-06-11

### 수정
- **write-guard.sh / skill-dedup.sh stdin 수리** — 두 훅이 환경변수만 읽어 .env/인증서/자격증명 Write 차단이 **한 번도 작동한 적 없던** 버그. stdin JSON 파싱(guard.sh 패턴) 이식, 환경변수 폴백 유지
- candidate-profile 경로 버그 — 룰이 레거시 `.claude/coding-profile.md`만 읽어 `.candidate/profile.md`(canonical)가 미소비되던 문제 (4.2.2 배포로 런타임 활성화 — 소스 픽스는 b1e163a)

### 변경
- **candidate-profile §3 복구** — "구현 전 이유 설명" 규칙을 모델 불문 소통 최소 보장선으로 재서술 (하한선이지 증폭기 아님)
- event-schema 계약: tier enum += `fable`, effort += `ultracode`(하니스 전용), transport HYBRID 확정(실시간 route.json + 기록은 기존 누적 로그)

### 비고
- 직전 배포(3.4.0, 2026-05-02) 이후 누적분 일괄 포함: Forge Voice(G9), flow CLI 통합(G5), progress.md 메커니즘(G3), implementation-notes 패턴(G3.5), scout 강화(G4), Gemini 아카이브, PR-trace 제거 등

## [4.2.1] — 2026-04-20
- smith 스킬 루트 `skills/`로 이동 — 마켓플레이스 로드 보장 (fix)

## [4.2.0] — 2026-04-19
- setup orchestrator + 슬래시 명령 네임스페이스 통일

## [4.1.0] — 2026-04-14
- 원격 접근 + 관찰 가능성 레이어 (`/setup-channels`, `/forge-status`, bin/forge CLI)

## [4.0.0] — 2026-04-14
- 번들 통합 + 구조조정 + state layer 계약 고정. `/done` `/quality` `/bug-fix` `/refactor` 폐지 — 규칙·훅으로 흡수 (docs/CATALOG.md)

## [3.4.0] — 2026-04-05
- 전수 감사 + 하네스 강화 + 스킬 정리

## [3.3.0] — 2026-03-29
- 하네스 3층 실구현 + AGENTS.md AAIF + hooks 강화

## [3.2.0] — 2026-03-21
- Bellows 로깅 + `/stats` + smith-build 보안 스캔

## [3.1.0] — 2026-03-21
- 설치 가이드 정비 + README/CLAUDE.md 개선

## [3.0.0] — 2026-03-21
- Smith 빌드 시스템 + hooks 구현 + 사고모델 주입 (Phase 1)

## [2.2.0] — 2026-03-19
- Anvil 에이전트 시스템 + `/start` 원큐 워크플로우

## [1.1.1] — 2026-03-16
- VAS(Vibe-Agent-System) 통합 + 플러그인 구조 리팩토링. `ggombee-agents` → `code-forge` rename

## [1.0.0] — 2026-03-15
- 최초 릴리스 — `.claude/` 기반 → Claude Code 플러그인 구조 마이그레이션
