# code-forge

[한국어](README.md)

> Install it. Claude Code gets better.

A Claude Code plugin that ships specialized agents, slash skills, and stack modules.
A proven thinking model (GROUND→APPLY→VERIFY→ADAPT) keeps quality consistent across every task.
(Agent/skill counts: the disk is the source of truth — `ls agents/*.md | wc -l`, `ls skills/*/SKILL.md | wc -l`)

**Current status**: actively maintained on personal GitHub (marketplace release 4.10.0). Patch notes: [CHANGELOG.md](CHANGELOG.md)

---

## Installation

### Option 1: Marketplace (recommended)

```bash
# 1. Register the marketplace (once)
claude plugin marketplace add https://github.com/ggombee/forge-market.git

# 2. Install the plugin
claude plugin install code-forge

# 3. Set up your project
claude
> /setup
```

### Option 2: Local clone

```bash
git clone https://github.com/ggombee/code-forge.git
claude --plugin-dir /path/to/code-forge
> /setup
```

Add an alias to avoid retyping every time:

```bash
alias claude-forge='claude --plugin-dir /path/to/code-forge'
```

### What `/setup` does

Reads `package.json`, auto-detects your stack, and generates a project-specific `CLAUDE.md` + `AGENTS.md`.
Stack selection and feature toggles (Smith / Whetstone / Bellows on/off) are handled interactively.

- `CLAUDE.md` — stack rules + module references (Claude Code)
- `AGENTS.md` — core thinking model propagation (compatible with Codex CLI and other tools)

---

## What it does

### `/start feature.md` — from spec to PR in one command

Write requirements in a Markdown file. It runs analysis → design review → implementation → tests → lint → commit → PR, all in one flow.
It asks you twice: "Implement this?" and "Commit?"

```
/start feature.md              # full flow
/start feature.md --plan-only  # analysis and plan only
/start "change button color"   # free text works too
```

It judges complexity itself — skips exploration for LOW, runs a Plan agent first for HIGH.
Follow-ups like completion-validation and bug-fixing aren't separate skills; they're absorbed into rules and hooks (replacement mapping: [docs/CATALOG.md](docs/CATALOG.md)).

### `/handoff` — cut a session, continue later

Instead of trusting auto-compact, it documents the context that lives only in the conversation (decisions, rationale, open questions) into `progress.md`, then copies a kickoff prompt for the next session to your clipboard. The next session picks it back up via session-init injection.

### Other key skills

| Skill | What it does |
|-------|-------------|
| `/test` | Unified test entry point — routes to unit / E2E / setup automatically |
| `/e2e` | Screen-level E2E automation (Playwright + autonomous run loop) |
| `/debate` | Run a structured debate between models to decide direction |
| `/research` | Fact-based structured research |
| `/codex` | Pair programming with OpenAI Codex |
| `/voice` | Voice input setup (local Whisper, hands-free) |
| `/setup --profile` | Analyze project coding style → generate a profile |

Full catalog: [docs/REFERENCE.md](docs/REFERENCE.md)

### `bin/forge` — state surface (for external tools)

```bash
bin/forge status --json   # quality gate / routing / REFLECT state (the only sanctioned read surface)
bin/forge whet --draft    # recurring quality issues (3+ times) → personal-convention draft candidates (human adopts)
bin/forge doctor          # self-diagnosis of injection circuit / version match / stuck-red (report-only)
```

[forge-glow](https://github.com/ggombee/forge-glow) (the HUD) consumes this surface to show the quality gate and effort recommendation on the status line.

---

## Agents

Agents with write access and agents without are strictly separated.

| Permission | Agents | Capabilities |
|-----------|--------|-------------|
| **Read-only** | analyst, architect, refactor-advisor, vision | Analysis, architecture, review — no code changes |
| **Bash-only** | scout, code-reviewer, git-operator, researcher | Exploration, review, git, research — no file edits |
| **Edit-only** | lint-fixer, build-fixer | Modify existing files — cannot create new files |
| **Full access** | implementor, deep-executor, assayer, codex | Anything |

Simple exploration goes to haiku (fast), complex implementation to sonnet, architecture analysis to opus.
Routing policy (tier pin = cost control): [references/routing-policy.md](references/routing-policy.md)

---

## Smith — the agent that builds agents

Agents are defined by splitting STATE (what the agent knows) and ACT (what the agent does), then compiled at build time.

Project agents embed the thinking model (Blueprint) inline, so core rules work even without the plugin.

```
/code-forge:smith-create-agent    # analyze project → auto-generate a custom agent (auto-triggered by setup)
/code-forge:smith-build           # manual build
```

---

## Stack modules

`/setup` reads `package.json` and configures automatically. Or pick manually:

| Category | Options |
|---------|---------|
| Framework | Next.js Pages Router, App Router, React SPA |
| Design System | MUI, Ant Design |
| State | Jotai+TanStack, Zustand+TanStack, Redux RTK |
| Styling | Emotion, Tailwind, Styled Components |
| Testing | Jest, Vitest |

Presets for quick setup: `standard` (Pages+Jotai+Emotion+Jest) or `modern-stack` (MUI+App+Zustand+Tailwind+Vitest)

---

## Sister tools (the 5-family)

code-forge is complete on its own, but composes with sister tools over shared contracts.
The contract + wiring status (🟢 wired / 📐 designed) is canonically tracked in [docs/contracts/INTEGRATION.md](docs/contracts/INTEGRATION.md).

| Tool | Role | Status |
|---|---|---|
| [forge-glow](https://github.com/ggombee/forge-glow) | Real-time HUD (status line) | 🟢 wired — consumes `bin/forge status --json` |
| flow-toolkit | Model-agnostic workflow CLI | 📐 dormant — every call is a graceful skip when absent |
| forge-hearth | Multi-project dashboard | 📐 dormant |
| coding-practice | Personal-convention source (`.candidate/profile.md`) | 🟢 consumed by the candidate-profile rule |

---

## The Forge metaphor

code-forge uses a blacksmith metaphor — a cognitive apprenticeship model where each component has a clear role:

| Name | Role |
|------|------|
| **Forge** | The platform itself |
| **Smith** | Builds and compiles agents (STATE + ACT) |
| **Anvil** | User-facing interface (CLI, skills, commands) |
| **Whetstone** | Sharpens coding skills (separate repo: coding-practice) |
| **Assayer** | Test generation and validation |
| **Bellows** | Usage logging and statistics |
| **Blueprint** | Thinking model and rules |

---

## MCP integrations

The plugin works standalone. These add more:

| MCP | Effect |
|-----|--------|
| Figma | Auto-analyze design specs in `/start` |
| Codex | Pair programming with another model |

Not installed? It just doesn't activate. No errors.

---

## License

MIT
