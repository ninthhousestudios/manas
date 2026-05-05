# manas architecture review

Date: 2026-05-04
Reviewer: Codex
Primary input: `docs/manas-architecture.md`
Other inputs sampled: `docs/roadmap.md`, `docs/principles.md`, `docs/todo.md`, `docs/darshana-design-notes.md`, `kosha/docs/architecture.md`, `yojana/docs/yojana-design.md`, plus source/migrations for chitta, smriti, sutra, sangha, and mcpjungle.

## executive take

The architecture has a good spine: the subsystem contracts are clear, the hard-vs-soft distinction is the right lens, content-addressed identity is the right default, and the roadmap is already aimed at the right prereqs. The main risk is not that the architecture is confused; it is that several load-bearing guarantees are still only described, not enforced.

Do not go all in on the implementation plan until the hard-contract layer is real enough to constrain the rest of the work. In practical terms: manas-cli boot/tool-group binding, normalized freshness/error envelopes, typed cross-tier references, and event/cursor semantics should land before yojana/kosha/darshana work starts accumulating code against unstable assumptions.

The weak parts below are ordered by how much they could force rework if left vague.

## what is strong

The one-sentence subsystem contracts are doing real architectural work. Chitta, smriti, sutra, sangha, kosha, and yojana have mostly clean boundaries, and the architecture has avoided the common failure mode of one "memory/search/planning" blob.

The hard-vs-soft distinction is the right correction. Treating CLAUDE.md and skill prose as cooperation surfaces rather than enforcement surfaces is the most important shift in the current docs.

Smriti's content-addressed model is the right foundation for long-lived identity. The architecture correctly avoids making paths the authoritative identity for files.

The darshana-before-prajna posture is disciplined. Building a read-only joined view after measuring real cross-tier demand is much safer than creating a concept graph because the system vocabulary makes it tempting.

## P0 weaknesses

### 1. Boot/ACL is still the real kernel, but manas-cli does not exist yet

The architecture says minimal/rich boot is hard-enforced by mcpjungle Tool Groups selected by manas-cli. That is the right target, but today manas-cli is docs only. Until it exists, the most important boundary in the system is still operational convention.

There is also a subtle distinction in mcpjungle: Tool Groups provide scoped group endpoints, while the existing client ACL machinery is server allow-list oriented and non-enterprise mode returns all tools. That may be fine operationally, but the architecture should not treat "Tool Groups exist" as equivalent to "each harness session is cryptographically or operationally bound to exactly one allowed tool surface."

Before implementation push:
- Define the exact boot contract: which endpoint/config does the harness receive, who creates it, who rotates/removes it, and what happens if binding fails.
- Make fallback to per-server MCP an explicit emergency mode, not a normal degraded path. It removes the ACL guarantee.
- Add an integration test that a minimal/code session cannot call chitta, smriti content-read, or sangha even when the agent asks for them by exact tool name.

### 2. Freshness envelopes are not yet a uniform interface contract

The doc says every read returns `as_of` and `is_stale`, and stale read-shaped operations should withhold content. The source does not yet match that across the board.

Examples:
- `sutra_read` reads current file contents and then `wrap_response` appends `is_stale`; stale content is still returned.
- `smriti_read` returns path/hash/content but no freshness envelope.
- Some smriti MCP errors are plain strings rather than structured errors.
- Several MCP methods return JSON encoded inside `String`, which weakens schema-level enforcement.

This matters because freshness is supposed to prevent the model from anchoring on bad context. If content and `is_stale: true` arrive together, the model can still anchor.

Before implementation push:
- Define a shared response envelope pattern for read tools: `ok`, `data`, `freshness`, `error`, `next_action`, and `truncated` where applicable.
- Implement tier-2 refusal first for `sutra_read` and `smriti_read`.
- Make "all read tools include freshness" a testable requirement, not prose.

### 3. Cross-tier identity is still brittle

The architecture correctly names chitta's path/hash/symbol joins as weak. That weakness is now blocking, because yojana context shapes, kosha citations, darshana, and future sideband sync all depend on reliable references.

The current plan says `external_refs` in chitta, while yojana design still describes `context_refs` as opaque strings. That creates two competing reference conventions. If yojana ships with opaque refs and chitta ships typed refs, the binding layer will inherit another translation problem.

Before implementation push:
- Define one typed external reference shape shared by chitta and yojana, even if stored differently.
- Include `type`, `value`, `as_of`, and ideally `authority`/`source_tier`.
- Decide whether chitta refs are JSONB only or whether high-use refs deserve a relational companion table for indexing.
- Make path refs second-class where a content hash or symbol id can be used.

### 4. The event stream is underspecified for the work it must carry

Kosha, smriti->chitta path-move sync, and sideband coordination all depend on durable event replay. Smriti has an `events` table and pruning, but the architecture still needs the subscriber contract.

The missing pieces are not glamorous, but they are load-bearing:
- `smriti_events_since(cursor_id)` shape, ordering, pagination, and retention behavior.
- Cursor ownership and recovery after pruning.
- Idempotency keys for consumers.
- Dead-letter or retry semantics for failed sideband actions.
- A clear answer for "event observed, source row later changed before consumer reads it."

Before implementation push:
- Treat `smriti_events_since` as a P0 API, not a kosha-side detail.
- Write the event contract once and use it for kosha and sideband path-move sync.
- Add a replay/reconciliation story for consumers that fall behind retention.

### 5. The sideband seam is named but not designed

The architecture now admits two cross-tier seams: agent orchestration and manas-cli sideband. That is honest. The sideband, however, is currently a bucket for several different responsibilities: path-move sync, kosha event subscription, compound tools, skill shells, and maybe boot/session lifecycle.

Those are different classes of work. Some are deterministic background jobs; some are harness orchestration; some are gateway/query planning.

Before implementation push:
- Split sideband responsibilities into named modules: boot/session host, skill shell runner, event consumers, and compound tool/query planner.
- Define whether sideband talks MCP-to-MCP, DB-to-DB, or through internal library APIs. Avoid deciding ad hoc per feature.
- Require every sideband operation to have idempotency, retry, and observability from day one.

## P1 weaknesses

### 6. Failure semantics currently conflict with security goals

The failure table is useful, but a few entries weaken the hard-contract story.

The biggest example: "smriti down -> sutra read of indexed file -> fall back to direct read." That may preserve availability, but it bypasses the smriti privacy gate and conflicts with "default-deny on perception subsystems." Similarly, "mcpjungle down -> fall back to per-server MCP config" removes the Tool Group ACL that minimal boot relies on.

Before relying on the table:
- Classify each fallback as secure-degraded, insecure-emergency, or prohibited.
- For privacy/ACL failures, prefer refusal over transparent fallback.
- Make the user-visible warning concrete enough that the operator knows a hard boundary is gone.

### 7. Chitta's epistemic lifecycle is still incomplete

Chitta is the long-term memory tier, but its lifecycle controls are not yet in schema/code: soft delete, retirement, typed supersession/contradiction, derivations, and observation consolidation are still planned.

That is acceptable at v0.1 scale. It becomes risky once /reflect, yojana, and darshana begin treating memories as durable planning context. Without provenance, a bad mental model can be retired but not explained. Without consolidation/eviction, /reflect will eventually become noisy and expensive.

Before broad rollout:
- Land soft delete and retired-model filtering before more code depends on `delete_memory`.
- Add derivations before two-layer `/reflect` starts generating durable mental models.
- Mark consolidated observations so `/reflect` has a bounded working set.

### 8. Yojana's context generator crosses a boundary the design says it will not cross

Yojana is described as the grammar of work and says `context_refs` are opaque strings. The same design then makes `yojana_context` resolve chitta observations, sutra outlines, ADRs, and other refs.

That can be a good feature, but it must live in the right place. If the yojana server calls chitta and sutra directly, it violates the subsystem seam. If manas-cli resolves context shapes, then yojana's MCP surface is not quite the six-tool server described. If the agent resolves them, the feature is soft and token-heavy.

Before implementing yojana:
- Decide where context-shape resolution lives.
- Keep yojana's core CRUD/query graph pure if possible.
- Put cross-tier context bundle assembly in manas-cli or mcpjungle, where compound behavior belongs.

### 9. Kosha's model bet needs a thin vertical proof before schema hardening

Kosha's design depends on Qwen3-VL embeddings being good enough for scanned documents without OCR. That is plausible, but it is still a product-quality assumption, not an architectural fact.

Before building full kosha:
- Run a small retrieval benchmark on the actual corpus: scanned pages, mixed scripts, tables, marginalia, and text-layer PDFs.
- Measure ingest latency, memory pressure, index size, and search quality.
- Prove citation usefulness for image-only pages. If `kosha_read` cannot return text for a scanned page, the user experience and chitta citation story need a concrete fallback.

### 10. Cost and observability are still documentation, but the architecture will need them early

The current cost model is labels, not instrumentation or enforcement. That is fine for single-user manual use, but manas-cli, sideband jobs, kosha ingestion, and darshana reports will create background and compound calls where token/runtime costs are less visible.

Before adding compound surfaces:
- Add per-tool cost labels in machine-readable manifests.
- Add trace/session ids across manas-cli -> mcpjungle -> subsystem calls.
- Record call counts, latency, result sizes, truncation, stale refusals, and sideband retries.

## P2 weaknesses

### 11. Human inspectability is a principle without a product surface

The principles say the human can inspect and understand all local data without going through an agent. Today the practical answer is mostly direct DB access or scattered CLI commands.

This does not block early implementation, but it should not be forgotten. A minimal `manas inspect` or per-subsystem `show/export` surface would make the principle real and help debug bad memory/context behavior.

### 12. Packaging/version boundaries are unclear

The root architecture treats the implemented subsystems as one federation, but the repo is a collection of separate Rust/Go projects with separate migrations and lifecycle commands. That can work, but the implementation plan should name compatibility expectations.

Before a larger release:
- Define a compatibility matrix: chitta schema version, smriti schema version, sutra version, sangha version, mcpjungle version, manas-cli version.
- Make `manas health` check those versions and report actionable drift.
- Decide whether root-level release tags mean anything across nested repos.

## attend to before going all in

I would gate the broader implementation plan on this short list:

1. Implement enough manas-cli to own boot mode, Tool Group binding, transcript/env injection, and lock-bracketed skill execution.
2. Normalize MCP response/error/freshness envelopes and enforce tier-2 stale refusal for `sutra_read` and `smriti_read`.
3. Land a shared typed external-ref contract, then chitta `external_refs`; align yojana `context_refs` with it before yojana code ships.
4. Specify and implement `smriti_events_since` with cursor, retention, pagination, and replay semantics.
5. Design the sideband as explicit modules with idempotent operations, not a general "coordination stuff" daemon.
6. Reclassify failure fallbacks so privacy/ACL degradation is never silent.
7. Land chitta soft-delete, retirement filtering, derivations, and observation consolidation before relying on /reflect as a durable model factory.
8. Run the two darshana experiments already in the roadmap before building any joined view.
9. Run a kosha retrieval spike before committing to the Qwen3-VL/no-OCR architecture.
10. Add machine-readable cost manifests and traces before compound tools or reports fan out across tiers.

## recommended order

The roadmap is close, but I would adjust the front of it:

1. **Interface contracts first:** response envelope, freshness tiers, error shape, typed refs, event stream contract.
2. **manas-cli thin kernel:** boot binding, harness adapter skeleton, lock-bracketed shell runner, health.
3. **Chitta lifecycle migration:** external refs, soft delete, retirement, derivations.
4. **Sideband/event consumer skeleton:** consume smriti events with idempotent cursor handling; implement one path-move sync.
5. **Two-layer `/done` and `/reflect`:** only after the shell and chitta lifecycle pieces exist.
6. **Yojana v0 core graph:** keep cross-tier context assembly outside the core server until the compound-tool location is settled.
7. **Kosha spike, then v0:** benchmark first, schema second.
8. **Darshana decision:** only after E1/E2 and typed refs.

## bottom line

Manas is architecturally promising, but the risky parts are exactly the parts that turn prose into guarantees. The next implementation phase should be less about adding new subsystems and more about hardening the federation substrate: boot authority, envelope consistency, typed references, event replay, sideband ownership, and memory lifecycle. Once those are real, yojana/kosha/darshana have a much better chance of landing cleanly instead of encoding today's gaps as tomorrow's APIs.
