# INTEGRATION — Forge family의 현재 연결과 전환 계약

> 기존 연결을 설명하는 참고 문서다. 이 파일의 존재만으로 host context 자동 적재를 보장하지 않는다.
> 새 core·멀티호스트 전환의 실행 순서는 [2026-10-18 최종 개선 계획](../../plan/code-forge-final-improvement-plan-2026-10-18.md)을 따른다.
>
> **상태 범례**: wired는 기존 사용 증거가 있는 연결, designed는 계획·휴면 상태다. 2026-10-18 source·설치 cache·버전이 일치하지 않는 사례를 확인했으므로 표를 현재 배포본 전체의 통과 증거로 사용하지 않는다. Foreman/Flow opt-in 등의 로컬 WIP도 설치본에서 별도 확인해야 한다.

---

## 1. 컴포넌트 역할 분담

| 컴포넌트 | 상태 | layer | 책임 | 입력 | 출력 (다른 컴포넌트가 소비) |
|---|---|---|---|---|---|
| **code-forge** | 🟢 wired | UX (Claude Code 플러그인) | 자연어/슬래시 → 단계별 워크플로우. 에이전트/스킬 수는 디스크가 진실. | 사용자 발화, `/start`, `/test`, `/setup` | `.claude/state/quality.jsonl`, `route.json`(emit-event), `bin/forge status --json` |
| **forge-glow** | 🟢 wired | observability (HUD) | 실시간 statusLine + Python rich TUI + tmux. 5-layer 데이터 (L1~L5). | stdin / transcript / `bin/forge` / OTel | statusLine 출력, `forge-glow-stats` TUI |
| **flow-toolkit** | 📐 designed, opt-in | legacy execution / domain capability | 비즈니스 policy / TC / spec / retro. core 실행 권한 정책과 구분 | 명시 실행 또는 지원하는 source의 opt-in | `.policy/*.json`, legacy Flow state. 새 Work 원장과 dual-write 금지 |
| **forge-hearth** | 📐 designed (미가동) | reporting (markdown dashboard) | 다중 프로젝트 progress 집계. tracker-agnostic. | `sources.json` v2 / `~/.forge-glow/workflow.json` | `dashboard.md` — 입력 데이터 미존재로 미가동. 통합 계획 P4에서 재평가 |
| **새 core** | 📐 구현 전 | trust / execution | managed Work 원장·독립 검증·Inbox·반영/readback | WorkSpec·versioned pack·RepositoryProfile | Evidence·Receipt·versioned read model |
| **Herdr** | 로컬 설치·능력 확인, core 연결 미구현 | terminal / process control | pane·workspace·agent 관찰과 제어 | 허용된 adapter 요청 | terminal 상태. Work 완료 판정은 아님 |
| **Voice / Anvil** | 기존 입력 경로 존재, provider 전환 설계 | accessibility / input | STT·단축키·입력, 선택형 wake·dispatch | 음성·명시한 대상 host | 텍스트 또는 승인 범위 안의 실행 요청 |
| **Whetstone** | 별도 개인 프로젝트 | human learning / profile | 연습·사람이 승인한 코딩 프로필 | 허용된 관찰·연습·사람 판단 | 개인 프로필 원본. 공개 pack 번들 금지 |
| **forge-market** | 기존 catalog, 정합 수리 필요 | distribution | host별 manifest·BOM·호환 조합 | version·source revision·digest | 설치용 catalog. runtime 권한 없음 |

---

## 2. 데이터 흐름 (전체 아키텍처)

아래 그림은 기존 Claude 회로와 선택 기능을 설명한다. Flow/Hearth는 필수 엔진이 아니며, 새 core 연결은 §8의 전환 계약을 따른다.

```
                  [사용자 자연어 / 슬래시]
                            │
                            ▼
        ┌─────────────────────────────────────────────────┐
        │  code-forge (Claude Code 플러그인) 🟢           │
        │ /start /test /e2e /handoff (+ Foreman opt-in) │
        │    └─ flow CLI 호출은 📐휴면 (graceful skip)    │
        └──────┬─────────────────────────┬────────────────┘
               │ produces                │ invokes
               ▼                         ▼
    ┌──────────────────┐         ┌──────────────────────┐
    │ .claude/state/   │         │ flow CLI             │
    │  quality.jsonl   │         │  policy/spec/tc      │
    │  reflect.flag    │         │  run/retro/doctor    │
    │  notepad.md      │         │   ↓ produces         │
    │  decisions.md    │         │ .policy/*.json       │
    └────────┬─────────┘         │ ~/.flow/projects/*   │
             │                   └──────────┬───────────┘
             │  surface                     │
             ▼                              │
   ┌──────────────────────┐                 │
   │ bin/forge status     │                 │
   │  --json (Schema v1)  │                 │
   └──────────┬───────────┘                 │
              │                             │
              │ (L3 소비)         retro 패턴 │
              ▼                             ▼
   ┌─────────────────────────────────────────────┐
   │  forge-glow                                 │
   │   L1 statusLine stdin                       │
   │   L2 transcript.jsonl 파싱                  │
   │   L3 bin/forge status (code-forge)          │
   │   L4 adapters/ (OMC 등)                     │
   │   L5 OTel cost_usd (정확값)                 │
   │   + ~/.forge-glow/workflow.json (forge-hearth와 │
   │     공유 schema → Python TUI 워크플로우 패널)│
   └────────────┬────────────────────────────────┘
                │
   ┌────────────┼─────────────────────────┐
   ▼            ▼                         ▼
statusLine   Python TUI                tmux 하단바
(2-3줄)      forge-glow-stats          (Codex 병렬)
             --workflow

                       ▲
                       │ 동일 sources v2
                       │
            ┌──────────┴────────────┐
            │ forge-hearth          │
            │  builder.mjs          │
            │  (Node, npm dep 0)    │
            │  → dashboard.md       │
            │  → projects/*.md      │
            └───────────────────────┘
```

---

## 3. 공유 계약 (Contracts)

### 3.1 `~/.forge-glow/workflow.json` — forge-hearth × forge-glow 공유 데이터

- **문서상 형식**: sources.json v2 (`forge-hearth/README.md` 참조). 실제 JSON Schema와 공통 parser fixture는 미완료이며 재활성화 전 검증한다.
- **소비처**:
  - `forge-hearth/builder.mjs` → `dashboard.md` / `projects/*.md`
  - `forge-glow-stats --workflow` → Python TUI 워크플로우 패널 (Phase 7)
- **위치 우선순위**:
  1. `$WORKFLOW_CONFIG_PATH`
  2. `~/.forge-glow/workflow.json` ← 기존 공유 위치. 새 중립 config로 바꿀 때 legacy read 보존
  3. `./sources.json`
  4. `./sources.example.json`
- **불변 필드**: `version: 2`, `trackers`, `projects[].id`, `projects[].path`
- 이 config의 수동 item 상태는 검증 evidence가 아니다. 재채택 시 상태 정본은 core 또는 원래 tracker/progress에서 읽고, config에는 source·표시 설정만 둔다. realm별 config/output을 분리한다.

### 3.2 `bin/forge status --json` — code-forge → forge-glow (L3 surface)

- **공급자**: `code-forge/bin/forge`
- **소비자**: `forge-glow/hud/lib/parse-forge.sh`
- **계약 문서**: `code-forge/docs/contracts/state-schema.md` (status v1 설명). 기계 검증 schema·fixture는 별도 완료 조건이다.
- **불변 규칙**: forge-glow는 `.claude/state/*` 파일을 **직접 읽지 않는다**. 반드시 `bin/forge status --json` surface 경유.
- **이유**: state 파일 형식 변경 시 외부 소비자 깨짐 방지.
- **현재 남은 결합**: Glow의 CLI 탐색은 Claude cache에 의존하고 usage 로그는 직접 파싱하는 경로가 남아 있다. 목표 계약 준수와 현 구현을 구분해 G1/G3에서 수리한다.

### 3.3 `.policy/*.json` — flow-toolkit이 정의, code-forge skill이 호출 📐 designed (휴면)

- **schema**: `flow-toolkit/packages/flow-rules/docs/policy-detection.md`
- **필수 필드**: `id`, `screen`, `category`, `bdd`, `affects.components[]`
- **생성**: `flow policy new <domain>` / **검증**: `flow policy lint` / **영향 분석**: `flow policy diff <ticket>`
- **로컬 source의 기본값**: `FORGE_FLOW_AUTO`가 꺼져 있으면 자동 호출하지 않는다. 설치본은 별도 확인한다. CLI가 없으면 graceful skip하고, 반복 패턴 후보는 `forge whet`가 제공한다. 이 명령은 사람 학습용 Whetstone과 구분한다.

### 3.4 `.claude/state/quality.jsonl` — code-forge hooks 출력 🟢 wired

- **공급자**: `code-forge/hooks/quality-gate.sh` (Stop 훅)
- **소비자**: forge-glow 및 외부 도구
- **형식**: jsonl append-only (1줄 1 이벤트)
- **이벤트**: ESLint 결과, tsc 결과, policy-sync 결과, scope 위반 등
- **계약 파일**: `code-forge/docs/contracts/state-schema.md`

### 3.5 자연어 관문 — auto-flow-trigger.sh (UserPromptSubmit) 🟡 Foreman opt-in / 📐 flow 분기는 휴면

- **위치**: `code-forge/hooks/auto-flow-trigger.sh` (Foreman과 flow 분기 모두 opt-in)
- 🟡 **Foreman 관문**: 기본은 침묵. `FORGE_FOREMAN_HINT=1`일 때만 작업성 발화에 "/start로? 그냥?" 선택지를 세션당 1회 주입
- 🟡 **티켓 ID 분기**: `FORGE_FLOW_AUTO=1`일 때만 `PROJ-123` 패턴을 감지해 flow를 호출
- 📐 **flow CLI 호출**: opt-in 후에도 미설치면 graceful skip

---

## 4. 자연어 → 명령 매핑 (Claude Code 안에서)

> flow CLI 칸은 전부 📐 opt-in 설계다. 기본은 호출하지 않으며 미설치 시에도 graceful skip한다.

| 사용자 발화 | 현재 실제로 (🟢) | flow CLI 설계분 (📐 휴면) |
|---|---|---|
| "PROJ-123 작업 시작" | 기본은 직접 처리; Foreman opt-in이면 `/start` 선택지 | `flow workflow start`, `flow tc select` |
| "기능 만들어줘/구현해줘" | 직접 처리; `FORGE_FOREMAN_HINT=1`일 때만 선택지 | — |
| "통합테스트 돌려줘" | `/test` (유닛/E2E 자동 라우팅) | `flow run report` |
| "화면 테스트 만들어줘" | `/e2e` (Forge Loop) | — |
| "회고 / 반복 패턴 보여줘" | `forge whet` (규칙 후보) + `/forge-status` | `flow retro` |
| "세션 정리하고 넘기자" | `/handoff` | — |
| "버그: TypeError ..." | thinking-model GROUND (2-3 옵션) | — |

(구 표의 `/done`, `/bug-fix`, `/refactor`, `/quality`는 v4.0에서 규칙·훅으로 흡수됐다. `/research`는 현재도 직접 호출 스킬이다.)

---

## 5. 작업 시퀀스 예시

### 신규 Epic (E)

```
사용자: "PROJ-100 신규 회원가입 화면 작업 시작"
  ↓
[code-forge /start]
  ↓ GROUND: 현재 에이전트가 대상 + 가까운 정상 패턴 확인
  ↓ PLAN: 위험 기반 route 권고; 별도 질문이 있을 때만 agent 추가
  ↓ 선택: FORGE_FLOW_AUTO=1이면 flow spec/tc/policy 호출
  ↓ APPLY: 직접 구현 또는 소유 범위가 분리될 때만 implementor
  ↓ Step 5:   quality-gate.sh → .claude/state/quality.jsonl append
              opt-in flow면 run report / policy lint
  ↓ checkpoint: 사용자 승인 뒤 commit / push / PR
  ↓ 회고: forge whet 초안은 사람이 채택
  ↓
[forge-glow HUD] 배선된 `bin/forge status --json` 필드만 표시
```

### 다중 프로젝트 진척 확인 (R)

```
사용자: "오늘 진척 보여줘"
  ↓
[forge-hearth builder.mjs] (또는 cron)
  ↓ ~/.forge-glow/workflow.json 읽기
  ↓ 각 프로젝트 git rev-parse + git log + progress 마크다운 파싱
  ↓ dashboard.md + projects/*.md 생성
  ↓
[forge-glow-stats --workflow] (선택)
  ↓ 같은 데이터를 Python rich TUI로
```

---

## 6. 설치 / 위치

| 컴포넌트 | 예시 clone 위치 | 설치 방법 | 자동 갱신 |
|---|---|---|---|
| code-forge | `<workspace>/code-forge/` | `claude plugin install` 또는 `--plugin-dir` | 마켓플레이스/수동. dev clone의 session-init 갱신은 `FORGE_AUTO_UPDATE=1`일 때만 |
| forge-glow | `<workspace>/forge-glow/` | `claude plugin install` 또는 `curl-install.sh` | tools/self-update.sh (1h) |
| flow-toolkit | `<workspace>/flow-toolkit/` | `curl-install.sh` → `~/.local/share/flow-toolkit/` | (수동 `git pull`) |
| forge-hearth | `<workspace>/forge-hearth/` | `node builder.mjs` 직접 또는 alias | cron `*/10 * * * *` 선택 |

---

## 7. 공개 자료와 realm 데이터

- working copy·이슈·source config·생성 dashboard·credential은 해당 realm의 허용 범위에서만 저장·동기화한다.
- 공개 문서와 `sources.example.json`에는 sanitized sample만 사용한다.
- `sources.json`과 기존 `~/.forge-glow/workflow.json`에 포함될 수 있는 원문은 별도 비공개 데이터다. 도구 코드 백업에 자동 포함하지 않는다.
- 새 core는 realm별 DB·artifact·보존/삭제·조회 권한을 정의한다. 여러 realm의 상태를 모을 때는 허용된 요약만 사용한다.
- 도구 코드의 공개 라이선스와 입력 자료의 공개 권한을 각각 확인한다.

---

## 8. 새 core와 연결하는 전환 계약

| 상태·자료 | 정본 | 소비 경로 |
|---|---|---|
| Blueprint·skills·Smith source | 기존 code-forge | pin된 host pack |
| native session의 route/quality | 기존 code-forge | `forge-status/v1` |
| managed Work·Attempt·Approval·Receipt | 새 core | versioned read/action API |
| 프로젝트 progress·ADR·tracker | 프로젝트가 선언한 원래 위치 | source pointer·revision·선택 adapter |
| 개인 연습·승인된 profile | Whetstone/사용자 | 허용된 부분의 compact profile |
| terminal·pane·workspace | Herdr | capability별 관찰/제어 adapter |
| Markdown·HUD cache | Hearth/Glow의 파생 산출물 | 원문/ledger 수정 권한 없음 |

새 core의 API 공개는 로컬 client용 규격을 뜻하며 데이터의 인터넷 공개를 뜻하지 않는다. raw host payload는 해당 adapter가 정규화하고, Glow/Hearth는 상태·완료·비용을 재판정하지 않는다. native hook의 gate는 managed Work의 Evidence로만 입력한다.

Glow가 기존 v1과 새 read model을 먼저 지원하고 실제 설치본 parity를 통과한 뒤 producer를 전환한다. cache 최고 version 대신 pin된 실행 경로를 사용하고, core DB 직접 조회를 금지한다. 계약 major·제품 version·source SHA·artifact digest는 구분해 BOM에 남긴다.

Hearth는 휴면 백업 후 재평가한다. 다중 source의 Markdown 보고서 수요가 있으면 schema·parser parity·경로 검증·shell 보간 제거·비파괴 installer·realm 분리를 갖춘다. core 데이터의 출력만 필요하면 report 모듈로 흡수하고, 수요가 없으면 복원 가능한 archive로 보존한다. 지금 병합·자동 설치하지 않는다.

Flow의 비즈니스 policy/spec/TC는 선택 capability로 평가하고 legacy workflow는 read-only import 또는 외부 참조로 연결한다. 하나의 managed Work를 Flow와 core가 각각 재시도·기록하지 않는다. 관찰 memory를 realm 사이에 무조건 동기화하지 않는다.

Herdr는 agent prompt·pane·worktree를 바꾸는 능력과 조회 능력을 나눈다. terminal 상태를 Work verdict로 쓰지 않고 생성·취소·제거 결과를 확인한다. core 부재·장애 시 native 사용은 보존하되 미확정 managed Work를 자동 재실행하지 않는다.

Whetstone은 사람 학습을 맡고, `forge whet`/Evidence의 반복 패턴은 승인 전 후보만 만든다. 개인 profile·프로젝트 정책·core 원장을 중복 정본으로 만들지 않는다. 시장 catalog와 설치물은 stable/dev를 구분하고 검증 후 원자 전환·이전 버전 복원을 지원한다.

---

## 9. Forge Voice — 음성 진입점

손목 부상/RSI 사용자가 family를 음성으로 사용할 수 있게 한다. 기존 code-forge 입력 도구와 별도 Anvil wake/dispatch는 연결 목표가 같지만 구현·설치 경로가 다르다.

### 진입 회로

```
[음성] → 단축키 ⌘⇧Space (Hammerspoon)
  ↓
forge-voice.sh — sox 녹음 → whisper.cpp (local) → 텍스트
  ↓
pbcopy + cliclick → Claude Code prompt 창 자동 paste
  ↓
UserPromptSubmit hook (auto-flow-trigger.sh) — 음성 친화 정규식
  티켓 ID 매칭 (case-insensitive, 공백/하이픈 모두 흡수)
  ↓ FORGE_FLOW_AUTO=1인 경우만
flow tc select <ticket>
  ↓
/start 진입 → 5-family 작동 → forge-glow HUD 표시
```

### 기존 code-forge 입력 구성

| 위치 | 역할 |
|---|---|
| `tools/forge-voice.sh` | 코어 STT 엔진 (sox + whisper.cpp 래퍼) |
| `tools/forge-voice.lua` | Hammerspoon 단축키 hook |
| `skills/voice/SKILL.md` | `/voice` 진입점 — 셋업/관리/진단 |
| `docs/voice-input.md` | 상세 가이드 + 트러블슈팅 |
| `hooks/auto-flow-trigger.sh` | 음성 친화 티켓 ID 매칭 (G9c 확장) |

### 의존성 (모두 무료 오픈소스)

- whisper.cpp (local Whisper, Metal 가속)
- sox (마이크 녹음)
- Hammerspoon (단축키 hook)
- cliclick (옵션, 자동 paste)

→ 셋업: `/voice setup` 1회.
→ 사용: `⌘⇧Space` 토글 또는 `⌘⇧.` silence detection.

### Hermes Agent와의 관계

Hermes는 Telegram/WhatsApp gateway로 voice memo transcription 제공. Forge Voice는 **로컬 macOS 통합** 우선 — 폰 음성 메모는 향후 G7 (Hermes H6 single gateway) 작업으로.

### 전환과 접근성 회귀 조건

기존 hotkey·symlink·Hammerspoon 절대경로를 새 설치·smoke test 전에 이동하지 않는다. Anvil의 STT/wake/dispatch와 code-forge `/voice`의 설치·호환 역할은 G0에서 정하고, Claude/Codex provider와 native/managed 입력을 검증한다. Inbox도 음성 질문 확인·응답·승인 scope 재확인 경로를 제공해야 한다. 음성 인식 결과만으로 권한이나 승인 범위를 넓히지 않는다.

---

## 10. 참고 문서

- code-forge: [`README.md`](../../README.md), [`CLAUDE.md`](../../CLAUDE.md), [`docs/contracts/state-schema.md`](state-schema.md)
- forge-glow clone: `README.md`, `docs/otel-setup.md`, `docs/workflow-setup.md` (지원 버전별 확인)
- flow-toolkit clone: `README.md`, `CLAUDE.md`, `AGENTS.md`, `packages/flow-rules/docs/auto-trigger.md`
- forge-hearth clone: `README.md`, `NEXT_STEPS.md`

---

| date | description |
|---|---|
| 2026-05-17 | 초안 — 4 컴포넌트 통합 후 작성 |
| 2026-10-18 | core·메타포·family 책임, Hearth 거취, Voice/profile·배포·복구 전환 계약 반영 |
