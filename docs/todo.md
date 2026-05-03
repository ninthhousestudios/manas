# manas — todo

Status: active
Date: 2026-05-03

Lightweight tracker until yojana v0 ships and we migrate. Source is the arch review at `docs/arch-review-2026-05-03.md` plus the roadmap.

Format: `[ ]` open, `[~]` in progress, `[x]` done, `[-]` dropped. Each item: priority (P0/P1/P2) → one-line rationale → file/area.

---

## P0 — architectural prereqs (do first)

- [ ] **Resolve principle 10.** Drop "CC-first" + the disagreement annotation. Adopt two-layer harness-agnostic skills as the path forward. → `docs/principles.md` (done in this rewrite); `docs/roadmap.md` (done).
- [ ] **chitta `external_refs` migration.** Typed JSONB column `[{type, value, as_of}]` with allowlist. Without this, cross-tier joins are JSONB grep. → `chitta/migrations/0007_external_refs.sql`.
- [ ] **chitta soft-delete + retirement.** `invalidated_at` column + `metadata.retired_at` + `metadata.retirement_reason`. `delete_memory` becomes soft. `search_memories` excludes retired by default. → `chitta/migrations/0008_*`.
- [ ] **Per-operation freshness response tier table.** Tier 1/2/3 specified per tool. Stale `read` ops withhold content. → `manas-cli/docs/freshness-envelopes.md` rewrite.
- [ ] **Failure-semantics table.** Codify the cross-subsystem failure-handling table from the arch doc; subsystem owners review. → `docs/manas-architecture.md` (started; expand).
- [ ] **Cost-model labels.** Cheap/medium/expensive per MCP tool, in each subsystem's docs. Documentation only for now. → per-subsystem README + manifest.

## P0 — experiments (do before darshana)

- [ ] **E1: chitta path-resolution audit.** Of memories with path-bearing metadata: % resolves to a real file? % to a smriti-indexed file? % survived recent moves? → `scripts/audit-chitta-path-refs.sh`.
- [ ] **E2: cross-tier-query frequency.** Scan `.sessions/*.jsonl` last 30 days. How many sessions hit ≥2 tiers about the same subject? → `scripts/audit-cross-tier-sessions.sh`.

## P1 — manas-cli phase 1

- [ ] **manas-cli crate scaffold.** `manas/manas-cli/` with `health`, `warm`, `done`, `reflect`, `status` subcommands. → new crate.
- [ ] **Harness adapter trait.** Concrete impls for Claude Code, Gemini CLI, opencode. Knows: how to invoke harness with a Tool Group, where the transcript is, what env to inject. → `manas-cli/src/adapters/`.
- [ ] **Skill-shell library.** Rust lock-claim → env-inject → invoke body → write output → release. Used by /done and /reflect. → `manas-cli/src/skill_shell.rs`.
- [ ] **Sideband daemon (minimal).** Unix socket. First endpoint: `path-move-notify` (smriti emits, chitta consumes). → `manas-cli/src/sideband/`.

## P1 — two-layer skills

- [ ] **Port /done to two-layer.** Shell handles transcript path injection (kills the hardcoded `~/.claude/projects/...`), sangha `handoff` lock, file IO. Body stays markdown for now. → `manas-cli/src/skills/done.rs` + existing skill md.
- [ ] **Port /reflect to two-layer.** Shell handles `reflect:user` lock, batch-loads observations + mental models (kills N+1), writes models with provenance. → `manas-cli/src/skills/reflect.rs`.

## P1 — chitta v0.0.4

- [ ] **Migration 0009: derivations table.** `(model_id, [observation_ids], session_id, skill_name, prompt_hash)`. Wired by /reflect shell. → `chitta/migrations/0009_*`.
- [ ] **`search_memories` exclude_retired / exclude_invalidated.** Default-on for retired. → `chitta/src/tools/search.rs`.
- [ ] **`chitta show` CLI.** Human-direct inspection per principle 5. → `chitta/src/bin/chitta-show.rs` or similar.

## P2 — yojana v0

- [ ] **Cargo workspace + schema migration.** Per `yojana/docs/yojana-design.md`. → `yojana/`.
- [ ] **Six v0 tools.** `yojana_project`, `yojana_task`, `yojana_edge`, `yojana_query`, `yojana_context`, `yojana_ready`.
- [ ] **Adopt mp-skills as opinion layer.** Add yojana as fourth issue-tracker backend in `setup-matt-pocock-skills`. → `docs/agents/issue-tracker-yojana.md`.
- [ ] **Migrate this todo into yojana.** Once v0 runs, dogfood. → here → yojana DB.

## P2 — darshana decision (gated on E1, E2)

- [ ] **Decide phase-5 path** based on E1/E2 outcomes. Roadmap encodes the decision rule. → `docs/roadmap.md` phase 5.
- [ ] **(if go) `darshana-report` first.** Precomputed nightly. Read by agent at rich boot. → `manas-cli/src/darshana/report.rs`.
- [ ] **(if go) `darshana-view` after.** Interactive `manas concept "X"`. → `manas-cli/src/darshana/view.rs`.

## P2 — kosha v0

- [ ] **Smriti event-stream tool.** `smriti_events_since(cursor_id)` over the existing events table. → `smriti/src/tools/events.rs` (new).
- [ ] **Kosha scaffold + Postgres schema.** Per `kosha/docs/architecture.md`. → `kosha/`.
- [ ] **Qwen3-VL pipeline.** Local model. Track candle BF16 dependency. → `kosha/src/embedding.rs`.
- [ ] **Six MCP tools.** `kosha_search`, `kosha_read`, `kosha_book`, `kosha_books`, `kosha_health`, `kosha_ingest`.

## P2 — smriti v0.3 (content storage + time travel)

- [ ] **`blobs` table** with zstd-compressed content. → `smriti/migrations/0003_*`.
- [ ] **`smriti_revert` tool.** → `smriti/src/tools/revert.rs`.
- [ ] **inotify watching** with crash recovery.
- [ ] **Catalog growth tracking.**

## P3 — observability + cost

- [ ] **mcpjungle OTEL token instrumentation.** Read-only first; enforcement deferred. → mcpjungle config + telemetry.
- [ ] **Per-tool cost manifest.** Auto-generated from per-subsystem `cost.toml`. → tooling.

## P3 — bookkeeping

- [ ] **Retire stale per-subsystem-roadmap docs.** `manas-cli/docs/roadmap.md` → archive (this rewrite supersedes). `manas-cli/docs/manas-architecture.md` → archive.
- [ ] **Touch up `manas-binding-sketch.md`.** Replace qartez references with sutra. Note the report-vs-view split. → `manas-cli/docs/manas-binding-sketch.md`.

---

## dropped / non-goals

- [-] **Build prajna now.** Deferred until darshana surfaces a list of cross-tier questions naive joins can't answer.
- [-] **CC-first principle 10.** Replaced by two-layer harness-agnostic skills (this iteration).
- [-] **Multi-machine smriti / sangha.** Out of scope until real divergent-machine workflow emerges.

---

## last-updated source

This list reflects the arch review at `docs/arch-review-2026-05-03.md` and the roadmap at `docs/roadmap.md`. When yojana v0 runs, this file is migrated and then deleted.
