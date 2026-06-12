# INTEGRATION — code-forge × forge-glow × flow-toolkit × forge-hearth

> 4개 컴포넌트가 하나의 워크플로우로 유기적으로 동작하는 방식 + 공유 데이터 계약.
> Claude Code (개인 PC) 진입점에서 자동 로드되는 단일 진실 소스.
>
> **상태 범례 (2026-06-12 정직화 — 마스터플랜 8단계)**: 🟢 **wired** = 실제 회로가 돌고 실사용 증거 있음 / 📐 **designed** = 코드·문서는 있으나 미가동(휴면/보류). 이 구분 없이 적힌 약속이 신뢰를 깎았다 — 이제 designed를 wired처럼 서술하지 않는다.

---

## 1. 컴포넌트 역할 분담

| 컴포넌트 | 상태 | layer | 책임 | 입력 | 출력 (다른 컴포넌트가 소비) |
|---|---|---|---|---|---|
| **code-forge** | 🟢 wired | UX (Claude Code 플러그인) | 자연어/슬래시 → 단계별 워크플로우. 에이전트/스킬 수는 디스크가 진실. | 사용자 발화, `/start`, `/test`, `/setup` | `.claude/state/quality.jsonl`, `route.json`(emit-event), `bin/forge status --json` |
| **forge-glow** | 🟢 wired | observability (HUD) | 실시간 statusLine + Python rich TUI + tmux. 5-layer 데이터 (L1~L5). | stdin / transcript / `bin/forge` / OTel | statusLine 출력, `forge-glow-stats` TUI |
| **flow-toolkit** | 📐 designed (휴면 — 사용자 보류, 마스터플랜 §3) | execution (멀티 모델 CLI) | policy / TC / spec / retro / doctor. | `flow workflow start <ticket>` | `.policy/*.json`, `~/.flow/projects/{repo}/` — **현재 생산 0** (CLI 미설치). 관문은 Foreman, 회고는 Whetstone(`forge whet`)이 대행 |
| **forge-hearth** | 📐 designed (미가동) | reporting (markdown dashboard) | 다중 프로젝트 progress 집계. tracker-agnostic. | `sources.json` v2 / `~/.forge-glow/workflow.json` | `dashboard.md` — 입력 데이터 미존재로 미가동. 마스터플랜 10단계에서 재상정 |

---

## 2. 데이터 흐름 (전체 아키텍처)

```
                  [사용자 자연어 / 슬래시]
                            │
                            ▼
        ┌─────────────────────────────────────────────────┐
        │  code-forge (Claude Code 플러그인) 🟢           │
        │   /start /test /e2e /handoff (+ Foreman 관문)   │
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

- **schema**: sources.json v2 (`forge-hearth/README.md` 참조)
- **소비처**:
  - `forge-hearth/builder.mjs` → `dashboard.md` / `projects/*.md`
  - `forge-glow-stats --workflow` → Python TUI 워크플로우 패널 (Phase 7)
- **위치 우선순위**:
  1. `$WORKFLOW_CONFIG_PATH`
  2. `~/.forge-glow/workflow.json` ← 권장 (양쪽 공유)
  3. `./sources.json`
  4. `./sources.example.json`
- **불변 필드**: `version: 2`, `trackers`, `projects[].id`, `projects[].path`

### 3.2 `bin/forge status --json` — code-forge → forge-glow (L3 surface)

- **공급자**: `code-forge/bin/forge`
- **소비자**: `forge-glow/hud/lib/parse-forge.sh`
- **계약 파일**: `code-forge/docs/contracts/state-schema.md` (JSON Schema v1)
- **불변 규칙**: forge-glow는 `.claude/state/*` 파일을 **직접 읽지 않는다**. 반드시 `bin/forge status --json` surface 경유.
- **이유**: state 파일 형식 변경 시 외부 소비자 깨짐 방지.

### 3.3 `.policy/*.json` — flow-toolkit이 정의, code-forge skill이 호출 📐 designed (휴면)

- **schema**: `flow-toolkit/packages/flow-rules/docs/policy-detection.md`
- **필수 필드**: `id`, `screen`, `category`, `bdd`, `affects.components[]`
- **생성**: `flow policy new <domain>` / **검증**: `flow policy lint` / **영향 분석**: `flow policy diff <ticket>`
- **현실 (2026-06-12)**: flow CLI 미설치로 위 호출 전부 graceful skip — `.policy/` 생산 0. 회고 축은 `forge whet`(Whetstone)이 quality.jsonl 기반으로 대행. flow 거취는 마스터플랜 10단계에서 데이터 갖고 재결정

### 3.4 `.claude/state/quality.jsonl` — code-forge hooks 출력 🟢 wired

- **공급자**: `code-forge/hooks/quality-gate.sh` (Stop 훅)
- **소비자**: forge-glow 및 외부 도구
- **형식**: jsonl append-only (1줄 1 이벤트)
- **이벤트**: ESLint 결과, tsc 결과, policy-sync 결과, scope 위반 등
- **계약 파일**: `code-forge/docs/contracts/state-schema.md`

### 3.5 자연어 관문 — auto-flow-trigger.sh (UserPromptSubmit) 🟢 wired (Foreman) / 📐 flow 분기는 휴면

- **위치**: `code-forge/hooks/auto-flow-trigger.sh` (구 auto-trigger.md 문서 발화 방식은 hook 강제 호출로 대체 — redesign G5)
- 🟢 **Foreman 관문** (4.6.0+): 작업성 발화 감지 → "/start로? 그냥? (복잡도/effort)" 선택지, 세션당 1회
- 🟢 **티켓 ID 분기**: `PROJ-123` 패턴 감지 (음성 친화 정규식 — G9c)
- 📐 **flow CLI 강제 호출**: 티켓 감지 후 `flow tc select` 호출하나 미설치라 graceful skip — Foreman 선택지만 실발화

---

## 4. 자연어 → 명령 매핑 (Claude Code 안에서)

> flow CLI 칸은 전부 📐 휴면 (미설치 graceful skip) — 실발화 칸은 "현재 실제로"가 진실.

| 사용자 발화 | 현재 실제로 (🟢) | flow CLI 설계분 (📐 휴면) |
|---|---|---|
| "PROJ-123 작업 시작" | Foreman 선택지 → `/start` 권유 (4.6.0+) | `flow workflow start`, `flow tc select` |
| "기능 만들어줘/구현해줘" | Foreman 선택지 (복잡도/effort 권고 — §3-3b 기록) | — |
| "통합테스트 돌려줘" | `/test` (유닛/E2E 자동 라우팅) | `flow run report` |
| "화면 테스트 만들어줘" | `/e2e` (Forge Loop) | — |
| "회고 / 반복 패턴 보여줘" | `forge whet` (Whetstone) + `/forge-status` | `flow retro` |
| "세션 정리하고 넘기자" | `/handoff` | — |
| "버그: TypeError ..." | thinking-model GROUND (2-3 옵션) | — |

(구 표의 `/done` `/bug-fix` `/research`는 v4.0 폐지 — 대체 매핑 `docs/CATALOG.md`)

---

## 5. 작업 시퀀스 예시

### 신규 Epic (E)

```
사용자: "PROJ-100 신규 회원가입 화면 작업 시작"
  ↓
[code-forge /start]
  ↓ Step 0-1: analyst — 요구사항 분석
  ↓ Step 0-3: flow spec capture <BE-URL>
  ↓ Step 0-4: flow policy new auth-signup
  ↓ Step 1-3: flow tc select PROJ-100
  ↓ Step 2-5: implementor — 구현 (PostToolUse hook → flow tc verify)
  ↓ Step 5:   quality-gate.sh → .claude/state/quality.jsonl append
              flow run report → .policy/runs/0001/result.json
              flow policy lint
  ↓ Step 6:   git-operator — commit + PR
  ↓ Step 7:   flow retro (3회+ 반복 패턴이면 rule 후보)
  ↓
[forge-glow HUD] 모든 단계 실시간 표시
  L1: 모델/브랜치/비용
  L2: 컨텍스트/캐시
  L3: bin/forge status (REFLECT flag, scope 위반)
  L5: OTel 정확 비용
  workflow panel: 현재 sub-task, 빌드 히스토리, 미결정
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

| 컴포넌트 | 본 PC 위치 | 설치 방법 | 자동 갱신 |
|---|---|---|---|
| code-forge | `~/Desktop/workspace/code-forge/` | `claude plugin install` 또는 `--plugin-dir` | 마켓플레이스 / session-init |
| forge-glow | `~/Desktop/workspace/forge-glow/` | `claude plugin install` 또는 `curl-install.sh` | tools/self-update.sh (1h) |
| flow-toolkit | `~/Desktop/workspace/flow-toolkit/` | `curl-install.sh` → `~/.local/share/flow-toolkit/` | (수동 `git pull`) |
| forge-hearth | `~/Desktop/workspace/forge-hearth/` | `node builder.mjs` 직접 또는 alias | cron `*/10 * * * *` 선택 |

---

## 7. 회사 데이터 분리 원칙

- `~/Desktop/workspace/_internal-workflow/` — 회사 프로젝트 working copy (cargopass/debit/invoice/naverworks/an). **GitHub push 금지**.
- `~/Desktop/workspace/forge-hearth/sources.json` — 회사 실데이터 (`.gitignore` 등록). **공개 X**.
- `~/Desktop/workspace/forge-hearth/sources.example.json` — sanitized sample (EXAMPLE-* 만). **공개 OK**.
- `~/.forge-glow/workflow.json` — 회사 데이터 들어가는 위치. **이전/sync 금지**.
- code-forge — 회사 GitLab 자산. **개인 GitHub push 금지**.

---

## 8. Harness 발전 방향 (다음 마일스톤)

현 구조는 이미 4-layer 분리가 잘 되어 있다. 발전 가능 축:

1. **bin/forge surface 확장** — `forge status`만 있는 surface에 `forge workflow`, `forge retro`, `forge tc` 등 추가하여 flow CLI와 통합. 외부 도구가 단일 binary로 접근.
2. **OTel L5 + flow run report 연결** — `flow run report`가 OTel 데이터를 함께 첨부하면 cycle별 정확 비용을 retrospect에서 활용 가능.
3. **retro → rule 자동 승격** — `flow retro` 가 3회+ 반복 incident 감지 시 `code-forge/rules/` 후보 PR draft 생성.
4. **forge-hearth → forge-glow alert 채널 통합** — forge-hearth의 미결정 Q / blocked item을 forge-glow 알림(Slack webhook)으로 전파.
5. **memory 통합** — `flow-toolkit/memory/` + `code-forge/.claude/state/notepad.md` + Claude Code 자동 memory(`~/.claude/.../memory/`) 셋의 단방향 sync 합의.

---

## 11. Forge Voice — 음성 진입점 (2026-06-08 redesign G9)

손목 부상/RSI 사용자가 family를 그대로 음성으로 쓸 수 있게. **code-forge의 확장** (별도 도구 X — 동일 family).

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
  ↓
flow tc select <ticket> 강제 호출 (모델 자율 의존 0)
  ↓
/start 진입 → 5-family 작동 → forge-glow HUD 표시
```

### 구성 (code-forge 내부 — 별도 repo 아님)

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

---

## 9. 참고 문서

- code-forge: [`README.md`](../../README.md), [`CLAUDE.md`](../../CLAUDE.md), [`docs/contracts/state-schema.md`](state-schema.md)
- forge-glow: `~/Desktop/workspace/forge-glow/README.md`, `docs/otel-setup.md`, `docs/workflow-setup.md` (Phase 7)
- flow-toolkit: `~/Desktop/workspace/flow-toolkit/README.md`, `CLAUDE.md`, `AGENTS.md`, `packages/flow-rules/docs/auto-trigger.md`
- forge-hearth: `~/Desktop/workspace/forge-hearth/README.md`, `NEXT_STEPS.md`

---

| date | description |
|---|---|
| 2026-05-17 | 초안 — 4 컴포넌트 통합 후 작성 |
