# manas — system principles

Status: current
Date: 2026-05-03

This doc owns the **cross-cutting** principles that apply to every owned subsystem. Subsystem-specific principles (e.g. chitta's verbatim-is-sacred) live in their own repos and govern their own behavior; they extend, not contradict, what's here.

When a principle here conflicts with a subsystem-local one, this doc wins for cross-cutting concerns; the subsystem doc wins for its own internals.

---

## 1. Single responsibility per subsystem

One contract per subsystem. Don't make chitta a file indexer. Don't make smriti store decisions. Don't make sutra a memory system. The contract is one sentence; the implementation is whatever fits inside it.

**Rules out:** subsystems that "also do" a second thing for convenience. Cross-domain features in a single binary.

## 2. Content-addressed over path-addressed

Where a subsystem has identity, it derives from the content (BLAKE3 in smriti; symbol qualified-name in sutra; content_hash in kosha). Paths are metadata. Identity must survive moves and renames.

**Rules out:** path-as-primary-key. Filename heuristics for "is this the same file." Renames breaking cross-tier joins.

## 3. Agent-native interface

Every MCP response is shaped for token-efficient consumption: structured envelopes, snippets with truncation honest, full content fetched on demand. Not human CLI output reformatted for agents.

**Rules out:** ad-hoc response shapes per tool. Pretty-printed text where structured JSON would do. Multi-page responses without explicit budget.

## 4. No implicit server-side state

Every query carries its scope: profile (chitta), root (smriti), workspace (sutra), session (sangha), project (yojana). No "current directory," no "active session" maintained server-side. The agent manages all state.

**Rules out:** sticky session bindings beyond connection-identity. Implicit defaults that change behavior between calls. Any tool that returns different results for the same input depending on prior state.

## 5. Self-hosted and inspectable

All data local. Every derived structure (embeddings, graphs, summaries) is re-derivable from a deterministic pipeline over the source. The human can inspect, query, and understand their own data without going through an agent. Direct DB access, export tools, and human-readable views are part of the contract.

**Rules out:** cloud-only storage. Opaque derived state. Features that only work through the agent surface.

## 6. Hard vs soft contracts named

When you write a contract, say which it is.
- **Hard** contracts are enforced by code, schema, ACL, or lock lifecycle. Examples: mcpjungle Tool Group binding, sangha lock TTL, chitta unique constraints, smriti privacy gate.
- **Soft** contracts depend on LLM cooperation. Examples: CLAUDE.md instructions, skill markdown bodies, observation discipline.

If a contract is hard, point at its enforcement. If soft, point at the fallback for non-cooperation.

**Rules out:** treating CLAUDE.md as if it were a kernel. Designing concurrency control around prose instructions to the LLM.

## 7. Default-deny on read paths

Filesystem and document access are allowlisted, not denylisted. Smriti reads only from configured roots. Kosha ingests only from configured knowledge roots within smriti's allowlist. Built-in filesystem reads are out-of-policy for indexed content.

**Rules out:** "read anywhere by default." Skipping the privacy gate for convenience. Tools that bypass smriti to read raw bytes.

## 8. Freshness on every read

Every read tool returns `as_of` (when the data was observed/indexed) and `is_stale` (server's judgment that the data is older than the threshold). Each operation declares its response tier:
- **Tier 1 — announce.** Return data + flag.
- **Tier 2 — refuse.** Return error + withhold content (so the LLM can't anchor).
- **Tier 3 — self-heal.** Refresh in-band.

Stale `read`-shaped operations should default to tier 2. Stale overview operations (`map`, `grep`, `outline`) default to tier 1.

**Rules out:** silently returning stale content. Combining tier 1 announce + content for tools where the LLM is likely to anchor.

## 9. Subsystems don't call each other directly; manas-cli owns all cross-tier composition

Cross-tier coordination flows through one of two named seams:
- **(a) the agent.** Default. The LLM reads from one tier, decides, calls another. Visible in transcript, costs tokens.
- **(b) the manas-cli sideband.** When the operation is deterministic, frequent, or must not depend on LLM cooperation.

Direct subsystem-to-subsystem calls (smriti calling chitta, sutra calling smriti) are out-of-policy. **Any compound behavior that touches more than one subsystem lives in manas-cli — never inside a subsystem server's binary.** This includes: yojana context-shape resolution (cross-joins to chitta/sutra/disk), darshana joined views, kosha event subscription against smriti, smriti→chitta path-move sync, future report generators, and any "convenience" tool that bundles results from multiple tiers. Subsystem servers stay pure: their tools answer questions about their own tier only.

mcpjungle may surface a compound tool *as* a single MCP tool, but the implementation routes through manas-cli, not through a subsystem.

**Rules out:** silent IPC between subsystems. "Just this once" coupling. Calling another subsystem's DB directly. A subsystem server reaching into another subsystem to "enrich" a response.

## 10. Each subsystem owns its own history

Chitta owns the history of understanding. Smriti owns the history of documents. Sutra is stateless (git owns code history). Kosha versions segments by content_hash. Yojana owns task state transitions. Sangha is real-time only.

No subsystem stores another subsystem's history. Don't put document paths in chitta as if chitta tracked them; put them as `external_refs` (typed, with `as_of`) and let smriti remain authoritative.

**Rules out:** caching another subsystem's state with no freshness signal. Duplicating history across subsystems.

## 11. Harness-agnostic by construction

Owned subsystems must run under any reasonable LLM harness (Claude Code, Gemini CLI, opencode, eventually local). Skills are two-layer: a Rust shell (lock + IO + env, via manas-cli) and an LLM body (the reasoning). Harness-specific assumptions (file paths under `~/.claude/`, CC-specific env vars) belong in adapters, not skill bodies.

**Rules out:** hardcoded harness paths in skills. Boot sequences that only Claude Code can execute. CC-specific affordances treated as ground truth in any subsystem's contract.

## 12. Every dependency has a written reason

Each `Cargo.toml` (or `go.mod`) entry carries a one-line comment stating what it's for and what was considered instead. If no reason can be written, the dependency isn't taken.

**Rules out:** silent dependency growth. Convenience crates that pull large transitive trees. "Standard" dependencies adopted on faith.

---

## How this doc is used

- Every PR that adds, renames, or removes a subsystem references the principles it touches.
- Subsystem-specific principle docs (chitta/docs/principles.md, etc.) extend these. They never override.
- Revising a principle requires its own PR that updates this doc first, then lands behavior in a follow-up.
- Principles are numbered for stable reference; do not renumber. If one is retired, mark it `withdrawn` in place.

## What lives in subsystem-specific principles

These principles say *what* manas commits to. Subsystem docs say *how* a particular subsystem honors them. Examples:

- `chitta/docs/principles.md` — verbatim-is-sacred, write-fast-enrich-lazily, idempotent writes, profiles as isolation, errors as instructions, no write-time extraction without benchmark wins.
- `smriti/docs/architecture.md` — privacy gate, two-tier (indexed + cataloged), `.smritiignore` semantics.
- `sutra/docs/sutra-sketch.md` — workspace identity, freshness via reparse-on-add-root.
- `sangha/docs/daemon-sketch.md` — connection-bound identity, lock vocabulary.

If a subsystem's principle contradicts something here, that's a bug in one of the two docs and needs to be reconciled.

---

## Withdrawn principles

(none yet)
