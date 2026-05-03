# manas — roadmap

Status: current
Date: 2026-05-03
Supersedes: `manas-cli/docs/roadmap.md` (2026-04-26, stale)

## where we are (2026-05-03)

| Subsystem | State |
|---|---|
| chitta | v0.1.0 live. Postgres + pgvector + bge-m3 ONNX. 7 MCP tools. 6 migrations. |
| smriti | v0.2.3 live. SQLite + FTS5 + sqlite-vec. Daemon. Privacy gate. 2 migrations. |
| sutra | v0.1.0 live. SQLite + tree-sitter. 17 MCP tools. Replaces qartez. |
| sangha | v0.1.0 live. SQLite. 9 MCP tools. Connection-bound identity. 2 migrations. |
| kosha | Design (architecture.md, kosha-sketch.md, model-server-sketch.md). No code. |
| yojana | Design (yojana-design.md). No code. |
| mcpjungle | Integrated. Tool Groups + ACL + e2e tests in source. |
| manas-cli | Docs only. No code. |

The system works for single-session, single-user usage today. Active gaps:

- No harness-agnostic boot. CLAUDE.md is the only "kernel," and it's soft.
- Skills are markdown, currently CC-shaped. Hardcoded transcript paths.
- Skill lock lifecycles depend on LLM cooperation.
- Cross-tier joins (chitta ↔ smriti, chitta ↔ sutra) are JSONB string-matches.
- No cost model. No specified failure semantics.

The arch review at `docs/arch-review-2026-05-03.md` is the authoritative source for *what's wrong*. This roadmap is the *what we're doing about it*.

---

## guiding shifts since 2026-04-26

1. **Harness-agnostic, two-layer skills.** Replaces the deferred "CC-first" principle. Skills are Rust shells in manas-cli with LLM bodies that any reasonably-capable model can execute.
2. **Hard vs soft contracts.** Named explicitly. The arch enforces what it can in code (Tool Group ACL, lock lifecycles, schema constraints) and stops pretending CLAUDE.md is enforcement.
3. **External refs in chitta before binding.** A typed `external_refs` column lands before darshana, otherwise cross-tier joins are guesses.
4. **Sideband as first-class seam.** "Subsystems don't call each other" reworded to admit two named seams: agent (default) and manas-cli sideband (deterministic / frequent / non-LLM-dependent operations).
5. **Yojana enters the planning sequence.** Was not in prior roadmap. Now part of phase 4.
6. **Kosha enters the planning sequence.** Was not in prior roadmap. Now phase 5.

---

## phase 0 — architectural prereqs (do first)

These are decisions/changes that block or shape later phases. Cheap now, expensive after code lands.

### 0.1 resolve principle 10 (harness agnostic)
- Delete the "CC-first" principle and the disagreement annotation.
- Adopt the two-layer skill model as the path forward.
- Skill markdown stays where it is for now (CC continues to work). New skills are Rust-shelled from day one.

### 0.2 chitta `external_refs` column
- Migration `0007_external_refs.sql`. JSONB array of `{type, value, as_of}`.
- Update `store_memory` and `update_memory` schemas to accept typed refs.
- Validate `type` against an allowlist (`smriti:hash`, `smriti:path`, `sutra:symbol`, `kosha:citation`, `yojana:task`, `chitta:memory`).
- Backfill: optional. Existing JSONB metadata is unchanged; new code uses the typed column.

### 0.3 chitta soft-delete + retirement
- Migration: `invalidated_at TIMESTAMPTZ NULL`, `metadata.retired_at`, `metadata.retirement_reason`.
- `delete_memory` becomes soft-delete (sets `invalidated_at`). Hard delete is a separate purge tool or psql.
- `search_memories` accepts `exclude_retired: true` (default).

### 0.4 freshness response tiers per operation
- Update `manas-cli/docs/freshness-envelopes.md` with the per-tool tier table from the arch review.
- Implement tier 2 (refuse + withhold content) in sutra `read` and smriti `read` first.

### 0.5 failure-semantics table
- Codify the cross-subsystem failure-handling table from the arch doc. Each subsystem owner reviews their column.

### 0.6 cost-model documentation
- Label each MCP tool cheap/medium/expensive in the per-subsystem README or a manifest.
- mcpjungle wires OTEL token instrumentation. Enforcement deferred until we have data.

### 0.7 two cheap experiments
- **E1: chitta path-resolution audit.** Of all chitta memories whose metadata mentions a path, what fraction resolves to a real file today? What fraction resolves to a smriti-indexed file? What fraction survived the last three weeks of file moves?
- **E2: cross-tier-query frequency.** Scan `.sessions/*.jsonl` for the last month. How often did a session call into ≥2 tiers about the same subject?
- Outputs feed the darshana decision (phase 5).

---

## phase 1 — manas-cli scaffold + harness adapters

**Why first:** Everything below depends on a host that can claim locks, inject env, and enforce Tool Group binding. Building it now unblocks two-layer skills.

### deliverables

1. New crate `manas-cli` in the manas workspace.
2. Subcommands: `manas health`, `manas warm`, `manas done`, `manas reflect`, `manas status`.
3. Harness adapter trait. Concrete impls for Claude Code, Gemini CLI, opencode. Each adapter knows: how to invoke the harness with a given Tool Group, where to find the transcript, how to inject env.
4. Skill-shell library. A skill's shell is a Rust function: claim lock → set env → invoke LLM body → write outputs → release lock.
5. Sideband daemon (minimal). Listens on a Unix socket; one initial endpoint: `path-move-notify` (smriti emits, chitta consumes).

---

## phase 2 — two-layer /done and /reflect

Port the two existing skills into the two-layer model.

1. `/done` shell: claim `handoff`, inject transcript path, run body, write `docs/handoff.md`, release.
2. `/reflect` shell: claim `reflect:user` (long_op), batch-load observations + mental models (kill the N+1), run body, write models with provenance, release.
3. Skill bodies stay markdown — they are now prompts that the shell loads and submits to the harness via the adapter.

Output: same skills, harness-agnostic, deterministic concurrency.

---

## phase 3 — chitta v0.0.4

Land the chitta-side schema work from phase 0 and the things that need real implementation rather than docs.

1. Migration 0007: `external_refs` typed column.
2. Migration 0008: `invalidated_at`, `metadata.retired_at`, `metadata.retirement_reason`.
3. Migration 0009: `derivations` table — `(model_id, [observation_ids], session_id, skill_name, prompt_hash)`. Wired by `/reflect` shell.
4. `search_memories` updates: `exclude_retired`, `exclude_invalidated`, ref-typed filters.
5. Optional: a `chitta show` CLI for human-direct inspection (principle 5).

---

## phase 4 — yojana v0

Build yojana per `yojana/docs/yojana-design.md`.

1. Cargo workspace at `manas/yojana/`. SQLite migrations, schema as designed.
2. Six v0 tools.
3. `yojana_context` ships with `summary` and `working` shapes only. `planning` and `agent` follow once dogfooded.
4. Adopt mp-skills as the opinion layer (`/to-issues`, `/triage`, etc., pointed at yojana as the backend).
5. Migrate manas's own todo (`docs/todo.md`) into yojana once v0 runs. Dogfood.

---

## phase 5 — darshana decision (gated by phase 0.7)

Run E1 and E2 from phase 0.7. Then decide:

- If E1 shows >70% of chitta path refs resolve cleanly **and** E2 shows ≥1 cross-tier session/day → **build darshana**.
  - Split into `darshana-report` (precomputed nightly, read by agent at rich boot) and `darshana-view` (interactive). Build the report first.
  - Lives inside manas-cli.
- If E1 shows weak resolution → **build the typed external_refs migration backfill first**, then re-run E1.
- If E2 shows few cross-tier sessions → **defer darshana**; the audience doesn't exist.

---

## phase 6 — kosha v0

Per `kosha/docs/architecture.md`.

1. Postgres + pgvector schema (separate DB from chitta).
2. Subscribe to smriti event stream via a new smriti tool: `smriti_events_since(cursor_id)`.
3. Qwen3-VL embedding pipeline. Local model. (Fastembed Rust path blocked on candle BF16 — track as kosha dependency.)
4. Six MCP tools: `kosha_search`, `kosha_read`, `kosha_book`, `kosha_books`, `kosha_health`, `kosha_ingest`.
5. Citation contract: `(book_id, segment_index, segment_label)`. Stored in chitta memories via `external_refs.kosha:citation`.

---

## phase 7 — smriti v0.3 (content storage + time travel)

1. `blobs` table with zstd-compressed content. Configurable retention.
2. `smriti_revert` tool — restore a file to a previous version.
3. inotify-based watching with crash recovery.
4. Catalog growth tracking.

---

## deferred — revisit when pain arrives

| Item | Trigger |
|---|---|
| Prajna (concept binding tier) | Darshana surfaces a list of cross-tier questions naive joins can't answer. |
| Token cost enforcement | mcpjungle OTEL data shows real cost pressure. |
| Multi-agent / multi-user | Teammate or autonomous subagent needs scoped access. |
| Cross-machine smriti | Real divergent-index workflow. |
| Cross-machine sangha | Shared-repo presence. |
| Web UI for any subsystem | Agent surface is the surface for now. |
| CLAUDE.md regression testing | A CLAUDE.md bug causes real damage. |
| Local-AI harness adapter | An actual local model is the daily driver. |

---

## what changed from the prior roadmap

| Prior | Current | Why |
|---|---|---|
| Phase 1 = sangha | Sangha is shipped (v0.1.0); not in current roadmap as a phase | Done. |
| Phase 2 = smriti v0.1 | Smriti is shipped (v0.2.3); current roadmap = smriti v0.3 (blobs/revert) | Done. |
| Phase 3 = mcpjungle integration | mcpjungle integrated; no longer a phase | Done. |
| Phase 4 = chitta v0.0.4 + manas-cli | Split: phase 1 = manas-cli, phase 3 = chitta v0.0.4 | manas-cli is prerequisite to two-layer skills. |
| Principle 10 = "CC-first" | Replaced by two-layer skills | Annotation indicated active disagreement; resolved 2026-05-03. |
| No darshana decision criteria | Phase 5 gated by E1/E2 | Arch review demanded measurable graduation. |
| No yojana | Phase 4 = yojana v0 | Yojana design landed 2026-04-30. |
| No kosha | Phase 6 = kosha v0 | Kosha design stable; depends on smriti event stream. |
| No external_refs | Phase 0.2 + phase 3 | Arch review identified weak cross-tier joins. |
