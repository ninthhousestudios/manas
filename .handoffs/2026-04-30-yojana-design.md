# manas — handoff

Date: 2026-04-30
Session intent: design conversation comparing `~/soft/mymir` and `~/soft/mp-skills/skills/engineering/` against the manas ecosystem, deciding what to steal and how to sequence the next stretch of work.

This is an umbrella-level handoff, not specific to any one repo. Per-repo handoffs (`<repo>/docs/handoff.md`) remain authoritative for in-flight work inside each repo.

---

## the headline

Three things were decided this session, none of them implemented yet:

1. **Yojana** — a new manas repo, a typed task-graph MCP service. Fills the gap between chitta (memory), sutra (code), smriti (files), and sangha (sessions). Closes the "where were we?" loop. Full design in `manas/yojana/docs/yojana-design.md`.

2. **mp-skills as the process layer.** We adopt `~/soft/mp-skills/skills/engineering/` (Matt Pocock's engineering skills) as the opinions about *how* work gets done. Yojana provides storage and grammar; mp-skills provides brainstorm/decompose/triage/tdd/diagnose. Yojana becomes a fourth "issue tracker backend" alongside mp-skills's existing GitHub / GitLab / local-markdown options.

3. **ADRs adopted across all manas repos.** Per-repo `docs/adr/` with the strict mp-skills filter (hard to reverse, surprising without context, real trade-off). Backfill candidates identified for chitta, fewer for sutra and smriti.

## what we are not doing

- **Not building our own brainstorm/decompose/onboarding/manage agents.** Use mp-skills's `to-prd`, `to-issues`, `improve-codebase-architecture`, `triage` instead. Mymir's agents are early-stage; mp-skills's are battle-tested.
- **Not collapsing manas into a Postgres monolith.** Mymir does this; we don't. The split (chitta/sutra/smriti/sangha) is a feature.
- **Not syncing yojana with GitHub Issues.** Local-first. Public visibility for chitta/sutra (public repos) is handled by future yojana web UI, not Issues sync.
- **Not starting any of the three refactors yet.** Plans exist (`chitta/docs/plans/chitta-refactor.md`, `sutra/docs/plans/sutra-refactor-plan.md`, `smriti/docs/plans/smriti-improvement-plan.md`); execution has not begun. Recent commits in those repos are bug fixes and review-driven cleanups, not the planned waves.

## sequencing (the real plan)

```
[parallel track 1: refactors]                [parallel track 2: yojana]

  smriti Wave 2 bug fix (standalone PR)        yojana v0 schema + 6 tools
  sutra PRs 1–2 (trivial cleanup)              yojana_context summary + working shapes
  smriti Wave 1 (quick wins)                   seed yojana with the 3 refactor plans
  chitta Phase 0 cleanup                       (dogfood against real data)
  sutra PRs 3–6                                iterate shapes based on what felt useful
  smriti Waves 3–4                             planning + agent shapes
                              ↓
                        REUNION POINT
                              ↓
   chitta Phase 1 (engine + server crate split) — first work PLANNED THROUGH YOJANA
   chitta Phase 2 (embedder sidecar)
   next features (TBD) — yojana drives planning natively
```

### Why this shape

- The three refactor plans are well-decomposed and self-managing. Adding yojana on top of them would be ceremony, not value.
- Yojana built in greenfield is the cleanest possible test of whether the design is right. Not retrofitted.
- **Dogfood early**: as soon as yojana v0 runs, seed it with the existing refactor plans as tasks-with-edges. The refactors continue to be *executed* normally — yojana just *observes*. This gives real data to develop the context shapes against, before we commit to using yojana for next-feature planning.
- The reunion point is chitta Phase 1 (engine/server crate split). That phase is genuinely *aion-driven feature work*, not internal cleanup — perfect first real test of yojana as a planning surface, since it requires multi-repo coordination (chitta + future aion plugin work).

### Smriti Wave 2 — pull out and ship now

`smriti/docs/plans/smriti-improvement-plan.md` Wave 2 contains a real bug fix: MCP scans ignore the user's `~/.smritiignore`. That should not be bundled with cleanup PRs. Lift it out, ship it as its own PR before any other refactor work.

## key insight from the session — grammar vs opinions

The design pivot that made everything click:

- **Yojana has no opinion about how work is done.** It provides the grammar (project, task, edge, status, identifier, context shape templates) and the continuity (storage, retrieval, ready-detection).
- **The opinions live in skills.** Editable markdown. They evolve without schema migrations. Different teams could use yojana with different process opinions (TDD-first vs spike-first vs whatever).
- **Josh brings the opinion. Yojana gives Josh continuity.** Skills package the opinions so they're reusable.

This is also how mymir is built — their MCP server is pure CRUD; their `agents/*.md` files carry the opinions. We borrow the structure and replace the opinions with mp-skills.

## what changed about yojana's schema during the session

Initial sketch was close to mymir's schema. Reading mp-skills surfaced these additions, all decided to **pre-add to v1** (cheap nullable fields beat a migration in two weeks):

| field | source | purpose |
|---|---|---|
| `category` (`bug` \| `enhancement`) | mp-skills/triage | distinguishes bug workflow from feature workflow |
| `slice_type` (`AFK` \| `HITL`) | mp-skills/to-issues | routes "what's next" — agent vs human pickup |
| `reproduction` (text, bug-only) | mp-skills/diagnose | locked-down repro becomes part of the agent context shape |
| `root_cause` (text, bug-only) | mp-skills/diagnose | confirmed cause; propagates upstream when other tasks reference this one |
| `context_refs` (jsonb of strings) | our own design | cross-service pointers: `docs/adr/N`, `CONTEXT.md#term`, `chitta:id`, `sutra:symbol`, `smriti:path` |

State machine adopted verbatim from mp-skills/triage:
```
needs-triage → needs-info → ready-for-agent | ready-for-human → in_progress → done
                                                              ↘ wontfix
```

Edge types include `motivated_by` for the diagnose → improve-codebase-architecture handoff (refactor task linked back to the bug that motivated it — captures genealogy).

## ADR backfill — what to write when convenient

Not urgent. When someone next opens chitta-refactor.md and re-litigates one of these decisions, that's the moment to make it an ADR.

**chitta:**
- 0001 — postgres stays as a real install dep (rejected: trait abstraction, embedded postgres)
- 0002 — memory_type as deployment-configured allowlist (rejected: open text, hardcoded)
- 0003 — engine + server crate split (rejected: monolith)
- 0004 — embedder extracted as sidecar (rejected: per-process model loading)

**sutra:** review sutra-overall-refactor.md for load-bearing decisions.

**smriti:** the SIGBUS-related WAL/mmap decisions look ADR-shape. Verify against current commit history before writing.

## open threads

- **Yojana DB location.** `~/.yojana/<slug>.db` (per-user) vs `<repo>/.yojana/index.db` (per-repo). Lean per-user with project slug, since cross-repo work is the common case in manas. Decide before v0.
- **Per-project CONTEXT.md adoption.** Adopt eagerly or lazily (only when a grilling session naturally produces a term)? mp-skills's `grill-with-docs` discipline says lazy. Lean lazy.
- **Manas umbrella `CONTEXT-MAP.md`.** Defer until at least one repo has a CONTEXT.md.
- **`setup-yojana-project` skill.** Modeled on mp-skills's `setup-matt-pocock-skills`. Bootstrap step before yojana usage in a repo. Builds: `docs/agents/issue-tracker.md` (yojana-flavored), `docs/agents/triage-labels.md`, `docs/agents/domain.md`, `## Agent skills` block in CLAUDE.md or AGENTS.md. To write after yojana v0 ships.

## what to pick up next session

In order of probable value:

1. **smriti Wave 2 bug fix** — half a day, ships a real fix, builds momentum.
2. **Sutra PRs 1–2** — half a day, trivial cleanup.
3. **Yojana v0 skeleton** — Cargo workspace, migration `0001_init.sql` from the schema in `manas/yojana/docs/yojana-design.md`, six v0 tools as stubs. Probably 1–2 sessions.
4. **chitta Phase 0** — start when sutra/smriti are settling.

If picking up #3, read `manas/yojana/docs/yojana-design.md` first — it has the full schema, the tool surface, the context shapes, and the decisions made during this session.

## pointers

- **Yojana design**: `manas/yojana/docs/yojana-design.md`
- **Refactor plans**: `manas/{chitta,sutra,smriti}/docs/plans/`
- **mp-skills**: `~/soft/mp-skills/skills/engineering/` — read `README.md` for the index
- **Mymir reference**: `~/soft/mymir/` — what we compared against; useful as a reference for context-shape patterns and agent prompts
