# code-forge

Install it. Claude Code gets better.

14 specialized agents, 17 skills, 17 stack modules.
A proven thinking model keeps quality consistent across every task.

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
# 1. Clone
git clone https://github.com/ggombee/code-forge.git

# 2. Run with plugin directory
claude --plugin-dir /path/to/code-forge

# 3. Set up your project
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

### `/bug-fix` — options first, then fix

Paste an error message and get 2–3 solution options with a comparison. Pick one and it applies the fix.

```
/bug-fix "TypeError: Cannot read property of undefined"
```

### Other skills

| Skill | What it does |
|-------|-------------|
| `/done` | Validate already-written code → commit → PR |
| `/refactor` | Refactoring analysis + policy-preserving tests |
| `/generate-test` | BDD scenario-based test generation |
| `/debate` | Run a structured debate between models to decide direction |
| `/research` | Fact-based structured research |
| `/codex` | Pair programming with OpenAI Codex |
| `/setup --profile` | Analyze project coding style → generate a profile |

---

## 14 Agents

Agents with write access and agents without are strictly separated.

| Permission | Agents | Capabilities |
|-----------|--------|-------------|
| **Read-only** | analyst, architect, refactor-advisor, vision | Analysis, architecture, review — no code changes |
| **Bash-only** | scout, code-reviewer, git-operator, researcher | Exploration, review, git, research — no file edits |
| **Edit-only** | lint-fixer, build-fixer | Modify existing files — cannot create new files |
| **Full access** | implementor, deep-executor, assayer, codex | Anything |

Simple exploration goes to haiku (fast), complex implementation to sonnet, architecture analysis to opus.

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

## The Forge metaphor

code-forge uses a blacksmith metaphor — a cognitive apprenticeship model where each component has a clear role:

| Name | Role |
|------|------|
| **Forge** | The platform itself |
| **Smith** | Builds and compiles agents (STATE + ACT) |
| **Anvil** | User-facing interface (CLI, skills, commands) |
| **Whetstone** | Sharpens coding skills (separate repo) |
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
