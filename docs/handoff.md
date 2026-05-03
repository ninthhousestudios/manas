# manas — handoff

Date: 2026-05-03
Session intent: high-level architecture review; doc reorg to reflect current state.
Prior handoff archived to `.handoffs/2026-04-30-yojana-design.md`.

---

## the headline

The umbrella docs are now current. The prior `manas-architecture.md` and `roadmap.md` (2026-04-26) were stale enough to mislead; they're archived and replaced.

What changed:

- New `docs/manas-architecture.md` — current state of all 8 subsystems (chitta, smriti, sutra, sangha, kosha, yojana, mcpjungle, manas-cli), hard vs soft contracts named, sideband as first-class seam, cross-tier identity table, freshness response tiers, failure semantics, cost model, two-layer skills.
- New `docs/roadmap.md` — phase 0 (architectural prereqs + experiments) → phase 7 (smriti v0.3). Reflects what's shipped vs what's next.
- New `docs/principles.md` — 12 cross-cutting principles consolidated from three drift sources.
- New `docs/todo.md` — P0–P3 task list keyed off the arch review. Lightweight tracker until yojana v0 ships.
- New `docs/arch-review-2026-05-03.md` — the high-level critique that drove the rewrite.
- New `docs/darshana-design-notes.md` — 10 operational kernels to remember when darshana eventually gets built (deferred per phase 5).
- Updated `manas-cli/docs/freshness-envelopes.md` — added per-operation tier table (announce / refuse-and-withhold / self-heal).
- Updated `manas-cli/docs/manas-binding-sketch.md` — header note: qartez → sutra, report-vs-view split, gating on E1/E2.
- Archived `manas-cli/docs/{manas-architecture,roadmap}.md` (2026-04-26) to `manas-cli/docs/archive/`.

This is also the first commit of the umbrella docs repo. Each subsystem keeps its own git; this repo tracks the cross-cutting layer.

## key decisions made this session

1. **Principle 10 resolved.** "CC-first" replaced by harness-agnostic two-layer skills (Rust shell + LLM body in markdown). Drives manas-cli to phase 1.
2. **Sideband is a first-class seam.** "Subsystems don't call each other" reworded to admit two named seams: agent (default) and manas-cli sideband (deterministic / frequent / non-LLM-dependent).
3. **`external_refs` typed column on chitta** lands before darshana. Without it, every cross-tier join from chitta is JSONB grep.
4. **Freshness response per-operation, not per-subsystem.** Tier 2 (refuse + withhold content) is the default for `read`-shaped ops on sutra and smriti.
5. **Hard vs soft contracts named.** CLAUDE.md is no longer treated as a kernel; ACL + lock lifecycles + schema constraints are the hard column. New principle 6 in `docs/principles.md`.
6. **Darshana split.** Report (precomputed nightly) vs view (interactive). Build report first, gated on E1/E2.

## one correction worth flagging

Gemini's earlier critique (`docs/arch-review-2026-05-03-gemini.md`, item #5) claimed chitta has a `memory_contradictions` table and an `invalidated_at` column. **Both are hallucinated** — neither exists in current chitta migrations (0001–0006). `invalidated_at` is planned in chitta handoff notes but not implemented. The new `manas-architecture.md` ("chitta — known gaps") corrects this. The 2026-05-03 arch review I wrote inherited the error and still has the uncorrected wording; if you want the review amended too, that's a small edit.

## what to pick up next session — in order

The roadmap is the source of truth. Concrete next moves, ordered by leverage:

1. **Run experiment E1.** Chitta path-resolution audit — a one-evening shell script. For every chitta memory whose metadata mentions a path, what fraction resolves? What fraction smriti has indexed? What fraction survived recent moves? Output decides whether `external_refs` needs aggressive backfill or can ship lazily. Script lives at `scripts/audit-chitta-path-refs.sh` (doesn't exist yet — write it). See `docs/todo.md` P0.
2. **Run experiment E2.** Cross-tier-query frequency — scan `.sessions/*.jsonl` for the last month, count sessions that touched ≥2 tiers about the same subject. Output decides whether darshana has an audience. Cheap script.
3. **Write chitta migration 0007 (`external_refs`).** Typed JSONB column with `(type, value, as_of)` and an allowlist of types. Small, concrete, unblocks the binding-layer work whenever it kicks in.
4. **Write chitta migration 0008 (soft-delete).** `invalidated_at` + `metadata.retired_at` + `metadata.retirement_reason`. `delete_memory` becomes soft. The handoff notes have been wanting this for a while.
5. **Start manas-cli scaffold (phase 1).** New crate, harness adapter trait, skill-shell library, sideband daemon stub. This is the biggest single unlock — once it exists, two-layer /done and /reflect can land, and the hardcoded `~/.claude/projects/...` path goes away.

The truly-very-next concrete action: **E1**. Highest info-per-hour, doesn't block on writing any new code in any subsystem, and the result determines whether step 3 needs an aggressive backfill plan or can ship lazily.

## open threads

- **Failure-semantics table.** Started in `manas-architecture.md`; each subsystem owner needs to walk their column once. Probably ~30 min per subsystem.
- **Cost-model labels.** Documentation only for now. Each subsystem's tools need cheap/medium/expensive tagging. No enforcement until mcpjungle OTEL is wired.
- **manas-cli/docs/ vs docs/.** freshness-envelopes.md and manas-binding-sketch.md are cross-cutting and arguably belong in `/docs/` rather than `/manas-cli/docs/`. Left in place to avoid breaking links; move at will.
- **Yojana DB location.** Per-user (`~/.yojana/<slug>.db`) or per-repo (`<repo>/.yojana/index.db`). Per the prior handoff, leaning per-user. Decide before yojana v0.
- **Mental-model retirement protocol.** Designed in `roadmap.md` phase 0.3, lands with chitta v0.0.4. Not blocking but worth keeping warm.

## pointers

- `docs/manas-architecture.md` — current state, contracts, interaction rules.
- `docs/roadmap.md` — phases, what's done, what's next, decision criteria.
- `docs/principles.md` — 12 cross-cutting principles.
- `docs/todo.md` — P0–P3 tasks keyed off the arch review.
- `docs/arch-review-2026-05-03.md` — the critique that drove this rewrite.
- `docs/darshana-design-notes.md` — open this when darshana is no longer deferred.
- `chitta/docs/principles.md` — chitta-specific principles (still authoritative for chitta internals).
- `yojana/docs/yojana-design.md` — yojana v0 design (next subsystem to build).
- `kosha/docs/architecture.md` — kosha design (depends on smriti event-stream tool).
