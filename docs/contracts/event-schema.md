# forge-event v1 — normalized cross-agent event contract

> **Status:** Phase 0 SHADOW spec (written, not yet consumed). Introduced by the Option C overhaul (`workspace/OVERHAUL_PLAN.md` §2). Sibling to [`state-schema.md`](./state-schema.md) and [`INTEGRATION.md`](./INTEGRATION.md).
> **Purpose:** ONE normalized event that every model/agent (Claude, Codex, future) maps INTO and every consumer (forge-glow HUD, forge-hearth, routing) reads OUT — killing the shell↔Python dual-parser drift at the root.

---

## 1. Transport (single, canonical)

- **Sink:** `.claude/state/events.jsonl` — per-project, append-only NDJSON (one forge-event per line). Matches the existing `.claude/state/` convention in `state-schema.md`. **Not** `~/.forge-glow/` (global, mixes projects).
- **Read API:** `bin/forge route --json` returns the latest reduced snapshot (latest-per-`(agent, thread, role)`). External tools **never** read the file directly — they call the API (honors `state-schema.md` §외부 도구 연동 규약).
- **Mapper:** one canonical shell mapper `forge-glow/hud/lib/map-event.sh` translates each vendor's raw JSONL into forge-event. Producers stay dumb; one place owns vendor quirks.

---

## 2. The event shape

```jsonc
// one forge-event per line in .claude/state/events.jsonl
{
  "schema_version": "1",              // string; forward-compat guard. NEVER bumped for additive fields (see §4)
  "ts": "2026-06-08T12:34:56Z",       // ISO8601 emit time
  "agent": "claude",                  // "claude" | "codex" | <subagent type>
  "model": "opus",                    // TIER (coarse): haiku|sonnet|opus|<codex tier>|unknown — for pricing/grouping/routing
  "model_version": "claude-opus-4-8", // EXACT id, VERBATIM from source, or null. DISPLAY/PROVENANCE ONLY — never a routing knob (see §5)
  "effort_level": "high",             // low|medium|high|xhigh|max | null  (FR2)
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
- `model_version` ← `.message.model` (exact id, e.g. `claude-opus-4-8` / `claude-opus-4-7` / `claude-sonnet-4-6`). `model` (tier) ← data-driven lookup keyed off that id.
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

Per-task / per-subagent Opus-version pinning (4.8 vs 4.7 vs 4.6) is **NOT supported** by the harness — the Agent `model` param is a tier-alias slot (`haiku`/`sonnet`/`opus`), not a full-id slot. The only real version knob is the session-global `settings.json` `"model"` (changed via `/model`).

Therefore `model_version` is captured **verbatim** purely so the HUD can display the truth (`🧠 Opus 4.8 @ high`). Routing decisions are made on `model` (tier) + `agent` (vendor) only. See `OVERHAUL_PLAN.md` §6 FR1.

---

## 6. Usage semantic (once)

`usage` is **cumulative-per-session**. Codex is already cumulative (take last `token_count`). The Claude mapper sums per-session to match. `reasoning` is Codex-only (Claude 0).

---

_Last verified: 2026-06-08. Owner: code-forge contracts. Consumed by: forge-glow (Phase 5+), forge-hearth (new feature, deferred)._
