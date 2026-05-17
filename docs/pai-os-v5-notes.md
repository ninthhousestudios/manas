# PAI-OS v5.0.0 — Notes for Manas

Source: `~/soft/pai-os/Releases/v5.0.0/`
Date: 2026-05-13
Status: Parked. Nothing immediately actionable — revisit if relevant.

PAI-OS is a "Life Operating System" built on Claude Code. v5.0.0 ships 37 hooks,
45 skills, 171 workflows, a named Digital Assistant persona, and a 7-phase execution
engine. Philosophically grounded in David Deutsch's epistemology (knowledge as
hard-to-vary explanation). Very different from manas — PAI is maximalist scaffolding
around a single user's life; manas is composable infrastructure for code-aware agents.

A chitta-specific steal list lives at `chitta/docs/pai-os-v5-steal-list.md`.

---

## Ideas Worth Remembering

### Mode/Effort Classification

PAI uses a Sonnet classifier hook at prompt-submit to decide how much machinery to
spin up. Three modes (MINIMAL/NATIVE/ALGORITHM) and five effort tiers (E1–E5). The
effect: simple questions don't load the full context stack, saving tokens and cache.

Manas doesn't gate effort — every session gets the full context load regardless of
task complexity. A lightweight triage step could reduce token spend on simple tasks.

### Scaffolding > Model

PAI's founding principle #5. The bet: deterministic infrastructure (hooks, typed
schemas, closed enumerations) beats relying on model judgment for anything the model
has shown willingness to get wrong.

Their experience: open vocabularies get "wallpapered" — models invent
plausible-sounding categories that aren't in the actual enum. Fix: closed
enumerations with explicit failure modes. Quote: "closed enumerations beat open
vocabularies for any rule the model has shown willingness to wallpaper."

This resonates with manas's direction on hooks and typed schemas. Worth keeping in
mind when designing any agent-facing taxonomy.

### Self-Healing Infrastructure Routing

When a rule is missed, PAI patches the system rather than writing a memo. They have
an explicit routing table for where fixes land:

| Fix type | Surface |
|----------|---------|
| Deterministic enforcement | Hook |
| Operational preferences | CLAUDE.md |
| Permissions | settings.json |
| Domain behavior | Skill |
| Execution doctrine | Algorithm version file |

Manas does this informally. The routing table idea is worth formalizing if rule
drift becomes a problem.

### ISA Done-Criteria Pattern

PAI's Ideal State Artifact uses verifiable criteria (ISCs) that evolve during
execution. Each criterion is binary-testable. Decisions are logged as
`conjectured / refuted_by / learned / criterion_now` — Deutsch-style
error-correction.

Yojana's context shapes could adopt verifiable done-criteria if task specs need
to get richer. The changelog format for decisions is also interesting.

### Unified Daemon

PAI runs a single bun process (Pulse, port 31337) handling observability, hook
execution, voice, dashboard, cron, and messaging. One process, many concerns.

Manas currently runs separate daemons (yojana, chitta, sutra, sangha, smriti).
The tradeoff is explicit — composability vs operational simplicity. Not obviously
wrong either way, but worth revisiting if the daemon count becomes a pain point.

---

## Things Reviewed but Not Relevant

- **TELOS (mission/goals/current-state/ideal-state)** — life planning system.
  Not what manas does.
- **The Algorithm (7-phase execution engine)** — heavyweight workflow orchestration.
  Manas uses lighter skill/hook composition.
- **Knowledge graph (People/Companies/Ideas)** — file-based entity graph with BM25
  search. Planned for vidya, but PAI's approach (flat markdown, no database) is the
  opposite of what vidya would likely do.
- **Relationship memory / satisfaction capture** — detailed in the chitta steal list.
- **40+ skills** — domain-specific (art, sales, web scraping, etc.). Not relevant
  to infrastructure.
