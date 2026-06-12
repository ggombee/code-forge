# forge-event v1 — normalized cross-agent event contract

> **Status:** Phase 0 SHADOW spec (written, not yet consumed). Introduced by the Option C overhaul (`workspace/OVERHAUL_PLAN.md` §2). Sibling to [`state-schema.md`](./state-schema.md) and [`INTEGRATION.md`](./INTEGRATION.md).
> **Purpose:** ONE normalized event that every model/agent (Claude, Codex, future) maps INTO and every consumer (forge-glow HUD, forge-hearth, routing) reads OUT — killing the shell↔Python dual-parser drift at the root.

---

## 1. Transport — HYBRID ruling (2026-06-11, owner-confirmed)

실시간과 기록은 서로 다른 형태가 맞다는 소유자 결정에 따라 transport는 두 축으로 분리한다:

- **실시간(latest-only) — `.claude/state/route.json`:** 현재 상태(모델/effort/role/last_gate) 딱 하나를 원자적 갱신(`mv` rename). **emit은 DEEP-MERGE** — producer는 자기 필드만 보내면 되고(`bin/forge emit-event`가 기존 파일과 `$old * $new` 병합), `ts`/`producer`는 매 emit 갱신. 서로 다른 producer(quality-gate의 `last_gate`, /start의 `complexity`)가 서로를 지우지 않는다. 소비자는 `bin/forge status --json`의 **v1-additive `route` 객체**로 읽는다 (별도 `route` 서브커맨드/리듀서 불필요). 외부 도구는 파일 직독 금지 — surface 경유 (honors `state-schema.md` §외부 도구 연동 규약).
- **기록(누적 지표 — 이행률/사용량/품질):** 신규 일기장을 만들지 않는다. **기존 누적 로그를 수리해 사용**한다 — `~/.code-forge/usage.jsonl`(bellows, name 어트리뷰션 수리 필요)과 `.claude/state/quality.jsonl`. 히스토리 대시보드(stats TUI/hearth)는 이쪽을 소비.
- **Mapper:** one canonical shell mapper `forge-glow/hud/lib/map-event.sh` translates each vendor's raw JSONL into the forge-event shape (§2) before writing `route.json`. Producers stay dumb; one place owns vendor quirks.

> **DEFERRED (정보보존 — 삭제 아님):** 원안의 `.claude/state/events.jsonl` append-only NDJSON + reducer + `bin/forge route --json` 서브커맨드는 **2nd consumer(이벤트 히스토리를 실소비하는 주체)가 실존할 때 재개**한다. 소비자 0인 채 무한 append하는 shadow는 켜지 않는다 (GC 미설계 상태). 원안 스펙 본문은 본 문서 git 히스토리(2026-06-08판)에 보존.

---

## 2. The event shape

```jsonc
// the forge-event shape — current snapshot lives in .claude/state/route.json (§1)
{
  "schema_version": "1",              // string; forward-compat guard. NEVER bumped for additive fields (see §4)
  "ts": "2026-06-08T12:34:56Z",       // ISO8601 emit time
  "agent": "claude",                  // "claude" | "codex" | <subagent type>
  "model": "fable",                   // TIER (coarse): haiku|sonnet|opus|fable|<codex tier>|unknown — for pricing/grouping/routing
  "model_version": "claude-fable-5[1m]", // EXACT id, VERBATIM from source, or null. DISPLAY/PROVENANCE ONLY — never a routing knob (see §5)
  "effort_level": "high",             // low|medium|high|xhigh|max|ultracode | null  (FR2)
                                      //   ※ API effort enum은 low~max 5종. ultracode는 Claude Code 하니스 전용 레벨
                                      //     (xhigh + 워크플로우 오케스트레이션) — verbatim 기록, API param으로 전달 금지
  "role": "coder",                    // planner|coder|reviewer|critic | null  (FR3)
  "turn": 12,                         // int turn/iteration counter
  "session_id": "abc123",             // session id
  "thread": "main",                   // thread/subagent thread key
  "usage": {                          // CUMULATIVE-per-session (one semantic, see §3)
    "input": 25290354,
    "cached": 23973504,
    "output": 40222,
    "reasoning": 6114,                // Codex reasoning_output_tokens; Claude 0
    "total": 25330576
  },
  "ctx_pct": 12.7,                    // float | null
  "ctx_window": 200000,               // int | null
  "cost_usd": 1.23,                   // float | null (derived from the tier price table)
  "items": [                          // optional: agents/skills/gates active
    { "type": "agent", "name": "scout", "count": 3 }
  ],
  "source": "transcript",             // transcript|rollout|sidecar — provenance
  "producer": "map-event.sh"          // which mapper/emitter wrote this line
}
```

---

## 3. Vendor → event mapping (verified on-disk source paths)

### Claude (`~/.claude/projects/**/*.jsonl`, incl. subagents)
- `model_version` ← `.message.model` (exact id, e.g. `claude-fable-5[1m]` / `claude-opus-4-8` / `claude-sonnet-4-6` — 리터럴 핀 금지, verbatim). `model` (tier) ← data-driven lookup keyed off that id (fable/opus/sonnet/haiku 키워드 매칭, 신규 티어 우선).
- `usage` ← `.message.usage.{input_tokens, cache_read_input_tokens, cache_creation_input_tokens, output_tokens}`, summed per session; `reasoning` = 0.
- `effort_level` / `role`: **absent from the transcript** (only `thinking` blocks exist). Sourced from the **harness sidecar** (§3 sidecar), never scraped. `null` when no sidecar.

### Codex (`~/.codex/sessions/**/*.jsonl`, select active by `mtime` within ~5 min)
- `model_version` ← `turn_context.payload.model` (**verbatim** — do not normalize; the live id has drifted across `gpt-5.x` releases, so never pin a literal).
- `effort_level` ← `turn_context.payload.effort`.
- `role` ← `turn_context.payload.collaboration_mode.mode` → `Plan`→`planner`, `default`→`coder`.
- `usage` ← **LAST** `event_msg` where `.payload.type == "token_count"` → `.payload.info.total_token_usage.{input_tokens, cached_input_tokens, output_tokens, reasoning_output_tokens, total_tokens}` (cumulative — take last; **do NOT sum across files** → triggers issue-#950 91× overcount). De-dupe unchanged cumulative totals (rate-limit re-emit, issue #14489).
- `ctx_window` ← `.payload.info.model_context_window`.
- **There are ZERO `turn.completed` rows** (verified) — the legacy parser's phantom schema. Read `token_count`, not `turn.completed`.

### Claude sidecar (harness-emitted — the only honest source for Claude `effort`/`role`)
- Written by `bin/forge emit-event` at SessionStart / routing-decision / SubagentStop. Carries `{model_version, effort_level, role}` the harness *chose*.

---

## 4. Forward-compat — the spine landmine

`forge-glow/hud/lib/parse-forge.sh` does **not** "ignore unknown fields" — on `schema_version != "1"` it **returns early and reads nothing**. So a version bump dark-screens the already-shipped forge-glow L3 panel for every user.

**Rule:** all FR1-FR4 fields (`model_version`, `effort_level`, `role`, `model`, …) are added as **v1-ADDITIVE fields with NO version bump.** The existing guard tolerates *new fields* under v1; it only breaks on a *new version*. Never bump the version for additive fields. (If a future change ever needs a major bump, the guard must first be made presence-tolerant and that fix shipped *before* any producer bumps.)

---

## 5. `model_version` is display-only (FR1 honest finding)

Per-task / per-subagent Opus-version pinning (4.8 vs 4.7 vs 4.6) is **NOT supported** by the harness — the Agent `model` param is a tier-alias slot (`haiku`/`sonnet`/`opus`/`fable`), not a full-id slot. The only real version knob is the session-global `settings.json` `"model"` (changed via `/model`).

**실측 (2026-06-11, main=claude-fable-5[1m] 환경):** `model: opus` 핀 서브에이전트의 transcript `.message.model` = `claude-opus-4-8` — 티어 별칭은 **main 세션 모델이 아니라 해당 티어의 최신 모델**로 해석된다. 따라서 핀 제거 시 서브에이전트는 main(Fable, 2x 단가)을 상속하고, 핀 유지 시 티어 최신에 머문다 — 핀은 비용 통제 수단으로 유효.

Therefore `model_version` is captured **verbatim** purely so the HUD can display the truth (`🧠 Opus 4.8 @ high`). Routing decisions are made on `model` (tier) + `agent` (vendor) only. See `OVERHAUL_PLAN.md` §6 FR1.

---

## 6. Usage semantic (once)

`usage` is **cumulative-per-session**. Codex is already cumulative (take last `token_count`). The Claude mapper sums per-session to match. `reasoning` is Codex-only (Claude 0).

---

_Last verified: 2026-06-11 (transport HYBRID ruling + fable/ultracode enum + opus-alias 실측). Owner: code-forge contracts. Consumed by: forge-glow (Phase 5+), forge-hearth (new feature, deferred)._
