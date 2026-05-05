# manas — architecture

Status: current
Date: 2026-05-03
Supersedes: `manas-cli/docs/manas-architecture.md` (2026-04-26 draft, stale)

Manas (मनस् — "mind") is a federation of agent-native subsystems that together provide memory, perception, coordination, planning, and document comprehension to an LLM-driven workflow. Each subsystem has a one-sentence contract and an MCP surface. The LLM is the cognition; manas is its body.

This doc describes what's actually built and how it fits together. Subsystem-internal design lives in each repo's own docs.

---

## the subsystems

| Subsystem | Sanskrit | Role | Storage | Status |
|---|---|---|---|---|
| **chitta** | चित्त — consciousness/memory | Store and retrieve understanding (observations, decisions, mental models, session summaries) | Postgres + pgvector | **v0.1.0 implemented** |
| **smriti** | स्मृति — remembrance | Content-addressed filesystem indexer; "where are files, what are they about, where were they before" | SQLite + FTS5 + sqlite-vec | **v0.2.3 implemented** |
| **sutra** | सूत्र — thread | Code intelligence: symbols, calls, deps, blast radius, hotspots, dead code | SQLite (tree-sitter) | **v0.1.0 implemented** |
| **sangha** | संघ — assembly | Session coordination: registry, advisory locks, broadcast inbox | SQLite | **v0.1.0 implemented** |
| **kosha** | कोश — treasury | Document comprehension over smriti (PDFs, epubs, papers); semantic search and citation | Postgres + pgvector | Design |
| **yojana** | योजना — plan | Typed task graph: projects, tasks, edges, context shapes | SQLite | Design |
| **mcpjungle** | (Go, MIT-listed MPL-2.0) | Single MCP gateway, Tool Groups, ACL | — | Integrated |
| **manas-cli** | — | Ops surface, lifecycle commands, sideband daemon, harness adapters | — | Docs only |

Sutra replaces the previously-external `qartez`. All owned subsystems are Rust binaries.

---

## subsystem contracts

### chitta — memory
**Contract:** answer "what do we know about X?" Never "where is file Y now?"

Stores: observations, decisions, mental models, session summaries, general memories. Memory type is a typed column (mig 0005). Bi-temporal: `event_time` (when the subject happened) and `record_time` (when we wrote it down). Idempotent on `(profile, idempotency_key)`. Embeddings are 1024-dim (BGE-M3 ONNX), pgvector HNSW index. Hybrid retrieval (dense + FTS + sparse + RRF; mig 0004).

Tools (7): `store_memory`, `get_memory`, `search_memories`, `update_memory`, `delete_memory`, `list_recent_memories`, `health_check`.

Known gaps (planned, not built):
- Soft-delete with `invalidated_at` (handoff has this; not in migration yet).
- Mental-model retirement (`metadata.retired_at`, `metadata.retirement_reason`).
- `memory_contradictions` table for first-class supersession (referenced in some external reviews; **does not exist** in current schema).
- `external_refs` typed column for joins to smriti/sutra/kosha — substrate gating item; shape shared with yojana `context_refs` (see § cross-tier identity).
- Provenance/`derivations` table linking mental models to source observations (recommended; not yet planned).
- Observation eviction/consolidation policy (not yet planned).

### smriti — filesystem perception
**Contract:** answer "what files exist, what are they about, where are they now, where were they before?"

Content-addressed (BLAKE3). Allowlisted roots only. Two-tier: indexed (semantically understood, hashed, lifecycle-tracked) and cataloged (existence + size only — for build artifacts and caches). Tracks moves and renames; identity survives both. Daemon transport (Unix socket), not stdio-per-session. Privacy gate: `smriti_read` is the only content-access tool; built-in filesystem reads bypass policy and should not be used for indexed content.

Owns its temporal history. Emits an event stream other subsystems (kosha, sideband) consume via `smriti_events_since(cursor_id)`. **This event API is a substrate prereq, not a kosha-side detail** — kosha, sideband path-move sync, and any future replicated consumer all share it. Required guarantees: monotonic cursor, pagination, retention window, idempotency keys per event, replay/reconciliation story for consumers that fall behind retention.

### sutra — code intelligence
**Contract:** answer "what exists in this code, where, and how is it connected?"

tree-sitter parser, symbols and call edges and complexity in SQLite, FTS5 over symbol names. Stateless w.r.t. history (git already has that). Per-workspace registration. Daemon-resident; reparse triggered by `sutra_add_root`.

Tools (17): `sutra_health`, `sutra_map`, `sutra_outline`, `sutra_find`, `sutra_grep`, `sutra_read`, `sutra_impact`, `sutra_deps`, `sutra_parse`, `sutra_tools`, `sutra_refs`, `sutra_calls`, `sutra_diff_impact`, `sutra_cochange`, `sutra_dead`, `sutra_hotspots`, `sutra_file_health`. All responses include `as_of` and `is_stale`.

### sangha — session coordination
**Contract:** answer "who is here, what are they holding, what should I avoid?"

Session registry with heartbeat TTL. Advisory resource locks with per-claim TTL, user-scope (`__user__` sentinel) and project-scope. Connection-bound identity: first `session_register` binds identity to the MCP connection (prevents trivial impersonation). Broadcast inbox for human-readable presence messages.

Tools (9): `session_register`, `session_heartbeat`, `session_unregister`, `session_list`, `resource_claim`, `resource_release`, `resource_list`, `broadcast`, `read_inbox`.

Lock vocabulary (canonical, growing):
| Resource | Scope | Default TTL | Held by |
|---|---|---|---|
| `handoff` | project | 120 s | `/done` while writing `docs/handoff.md` |
| `reflect:user` | user | 600 s | `/reflect` for the entire run |
| `smriti-scan` | user | 300 s | smriti during scan |

### kosha — document comprehension (design)
**Contract:** answer "what does this document say about X, with citations?"

Sits on top of smriti's event stream. Decomposes documents into segments (PDF pages, epub chapters, markdown sections, HTML headings). Embeds with Qwen3-VL (text + image into one 2048-dim space) — no OCR for scanned content; the page image is embedded directly. Stable citation key is `(book_id, segment_index)`; chitta stores the full triple.

Reads files only via `smriti_read` (privacy gate). Tracks its own cursor over smriti's events table. New hash = new book; old book + segments retained for citation durability.

### yojana — task graph (design)
**Contract:** answer "where were we, and what should I work on next?"

Typed task graph: projects, tasks, edges (`depends_on`, `blocks`, `relates_to`, `supersedes`, `refines`, `motivated_by`), per-project sequence numbers (`YJN-N`). State machine borrowed from mp-skills' `triage`. **Grammar of work**, not opinions about work — opinions live in skill files. SQLite, single binary, MCP surface. Six v0 tools: `yojana_project`, `yojana_task`, `yojana_edge`, `yojana_query`, `yojana_context`, `yojana_ready`.

`context_refs` use the **same typed reference shape** as chitta `external_refs` (`{type, value, as_of, authority?}`) — not opaque strings. Yojana stores them; it does not resolve them.

**Where context-shape resolution lives:** `yojana_context` returns the *unresolved bundle* (task fields, edges, ref list) from yojana itself. Cross-joins to sutra outlines, chitta observations, ADRs on disk, etc. happen in **manas-cli** (per principle 9). The agent calls a single compound tool that manas-cli surfaces; manas-cli internally fans out to yojana → sutra → chitta → disk and assembles the U-shape result. Yojana's binary stays a pure task-graph server.

### mcpjungle — gateway
**Contract:** present a single MCP endpoint that fronts every other subsystem and enforces who can call what.

Go binary. Provides:
- A single MCP endpoint upstream of chitta, smriti, sutra, sangha (and later kosha, yojana).
- **Tool Groups** — named sets of tools. `memory` (chitta), `code` (sutra), `filesystem` (smriti), `presence` (sangha), `full` (everything). Existing in source: `internal/model/tool_group.go`, `internal/service/toolgroup/`, `internal/api/tool_groups.go`, e2e tests.
- **ACL** — which client/connection can invoke which Tool Group. This is the mechanism that makes blind-boot a *hard* contract: a code-review session is bound to `code` only and physically cannot reach chitta even if the LLM tries.
- OTEL hooks for token-cost instrumentation (deferred — wire when needed).

Known gaps to work around: no resource templates (smriti uses tool-based reads — already designed this way), no resource subscriptions (handled via manas-cli sideband), Tool Groups are tools-only (resources not group-scoped — accepted).

### manas-cli — ops surface (planned)
**Contract:** the human-and-harness-facing CLI that boots sessions, runs lifecycle skills, hosts the sideband daemon, **and owns every cross-tier compound operation** (per principle 9).

Responsibilities:
1. **Boot** — claim/inject the right Tool Group binding, seed the system prompt, hand off to the LLM harness (Claude Code, Gemini CLI, opencode, or eventually local).
2. **Skill shells** — claim sangha locks, inject transcript paths, execute LLM body, release locks, write outputs. The Rust shell of two-layer skills (see below).
3. **Sideband daemon** — narrow IPC for cross-subsystem coordination that must not depend on LLM cooperation (smriti→chitta path-move sync, kosha event subscription, etc.).
4. **Compound tool host** — implements every cross-tier read/write that bundles more than one subsystem: yojana context-shape resolution, darshana joined views, future report generators. Subsystem servers never call each other; manas-cli is the only place that fans out across tiers.
5. **Health + observability** — `manas health`, `manas warm`, `manas done`, `manas reflect`.

The boot contract (must be specified before anything else in manas-cli ships):
- Which endpoint/config the harness receives, who creates it, who rotates/removes it, and what happens if binding fails.
- Fallback to per-server MCP is an **emergency-only mode**, never a normal degraded path — it removes the ACL.
- An integration test that a minimal/code session cannot reach chitta, smriti content-read, or sangha even when the agent calls them by exact tool name.

These four points are the boot contract; they can be specified and tested independently of the rest of manas-cli landing.

---

## hard vs soft contracts

The architecture has two kinds of guarantees and they are not interchangeable.

| Kind | Where enforced | Examples |
|---|---|---|
| **Hard** — cannot be violated | Code, schema, ACL, lock lifecycle | mcpjungle Tool Group ACL, sangha advisory locks managed by manas-cli, chitta unique constraints, smriti privacy gate, freshness envelope fields, MCP schemas |
| **Soft** — LLM cooperation required | CLAUDE.md, skill markdown bodies | "Store observations proactively," "Read chitta first when starting work," skill prose instructions |

This distinction is load-bearing.

CLAUDE.md is **not a kernel.** It is configuration-as-prose interpreted by the LLM at runtime. The agent will sometimes skip a step, invent a step, or hallucinate compliance. Anything that *must* hold belongs in the hard column; anything that depends on the LLM following written instructions belongs in the soft column.

The current direction (per 2026-05-03 review) is to migrate as much as practical from soft to hard:

- **Boot mode** → Tool Group selected by manas-cli at connection time. CLAUDE.md describes what's available; ACL enforces it.
- **Lock lifecycles** → manas-cli claims and releases. The LLM can request advisory locks via sangha tools, but the load-bearing locks are bracketed by the host.
- **Transcript path** → injected as env var by manas-cli, not discovered by the LLM via shell globbing.
- **Skill workflow** → Rust shell (lock + IO + env), LLM body (the reasoning). Two-layer skills.

CLAUDE.md remains useful for behavior the LLM is well-suited to (proactive observation, choice of which tool to call) but stops being load-bearing for safety, concurrency, or routing.

---

## boot modes

Two modes. CLAUDE.md still loads (the harness does this regardless), but the ACL determines what tools are reachable.

**Minimal boot (default).**
- Tool Group: `code` only (sutra) — for blind code review, fresh-eyes work. Or `none` for pure file editing.
- ACL hard-blocks chitta, smriti's content-read, sangha presence, etc.
- No memory loading, no handoff reading.
- Health check is the only required step.

**Rich boot (opt-in).**
- Tool Group: `full`.
- Triggered explicitly (`manas warm`, "check the handoff", "what were we working on?").
- Read `docs/handoff.md`, query chitta for context, surface sangha inbox, load mental models.

The principle: the agent is always *capable* of continuity, but doesn't *impose* it. Today that's a CLAUDE.md instruction. Tomorrow (post manas-cli) it's a Tool Group binding.

---

## component interaction rules

1. **Subsystems don't call each other directly.** Cross-tier coordination flows through one of two named seams:
   - **(a) the agent**, by default. The LLM reads from one tier, decides what to do, calls into another. Visible in transcript, easy to inspect, tokens cost real money.
   - **(b) the manas-cli sideband**, when the operation is deterministic, frequent, or must not depend on LLM cooperation. Examples: smriti→chitta path-move sync, kosha subscribing to smriti's event stream, mcpjungle compound tools.

   This is a revision of the previous absolute "subsystems don't call each other" rule. The previous rule was already eroding by exception (darshana, sideband, compound tools). Naming the second seam makes the architecture honest.

2. **Each subsystem owns its domain's history.** Chitta owns the history of understanding. Smriti owns the history of documents. Sutra is stateless (git has code history). Kosha owns segment versioning by content_hash. Yojana owns task state transitions. Sangha is real-time only.

3. **MCP is the universal interface.** Every owned subsystem exposes MCP tools as its primary surface. CLI surfaces are conveniences. If a better tool protocol replaces MCP, all subsystems migrate together.

4. **Degrade gracefully** (with specifics — see *failure semantics* below).

5. **Default-deny on perception subsystems.** Smriti only reads from allowlisted roots. Kosha only ingests from configured knowledge roots within smriti's allowlist. Built-in filesystem tools should be considered out-of-policy for indexed content.

---

## cross-tier identity

Five identity systems coexist. The cross-tier joins manas needs are bridged primarily through:

| Tier | Identity |
|---|---|
| chitta | UUID + freeform `metadata` JSONB + tag strings |
| smriti | BLAKE3 content_hash + path |
| sutra | qualified symbol name (path + symbol) |
| kosha | `book_id` (UUID derived from content_hash) + `segment_index` |
| sangha | connection-bound session UUID |
| yojana | `YJN-N` per-project task ID |

The bridges that exist or are planned:

| Join | Bridge | Strength |
|---|---|---|
| chitta ↔ smriti | path or hash via JSONB strings | Weak — string-match, brittle to renames |
| smriti ↔ kosha | BLAKE3 content_hash | Strong — kosha derives book_id from hash |
| smriti ↔ sutra | path | Strong — both use canonical paths |
| chitta ↔ sutra | path/symbol via JSONB | Weak — string-match |
| chitta ↔ yojana | typed ref `{type:"chitta:memory", value:<uuid>, as_of}` in yojana `context_refs` | Strong (planned) |
| chitta ↔ kosha | `(book_id, segment_index, label)` triple stored as citation | Strong (planned) |

The weak bridges are a real architectural problem. The fix is one **shared typed-ref shape** used by both chitta `external_refs` and yojana `context_refs`:

```
{type: "smriti:hash" | "smriti:path" | "sutra:symbol" | "kosha:citation"
     | "yojana:task" | "chitta:memory" | "doc:path",
 value: "<id-or-path>",
 as_of: <unix_ms>,
 authority?: "<source-tier>"}
```

Both subsystems store the same shape (storage may differ — chitta as a typed JSONB column, yojana as a JSONB array on tasks). Path refs are second-class: prefer `smriti:hash` or `sutra:symbol` when available. This lands before any binding/view layer (darshana) and before yojana ships its `context_refs` schema. Without it, cross-tier queries are JSONB grep-with-extra-steps and yojana/chitta inherit a translation layer.

---

## freshness envelopes

Every read across manas subsystems returns:
- `as_of: i64` — Unix milliseconds. When the underlying data was last refreshed/observed. Not the call time.
- `is_stale: bool` — server's judgment that data is older than the subsystem's freshness threshold.

What `as_of` means per subsystem:
- **chitta** — `record_time` of the most recent write touching the returned data.
- **smriti** — last scan time for the path/root.
- **sutra** — index build time for the workspace.
- **sangha** — server time at response.
- **kosha** — embedding time for the segment.
- **yojana** — task `updated_at`.

**Response tier on `is_stale=true`** — pick per operation, not per subsystem.

| Tier | Behavior |
|---|---|
| 1. Announce | Return data + flag. Caller decides. |
| 2. Refuse | Return error; require caller to trigger refresh. Withhold content so the LLM can't anchor on it. |
| 3. Self-heal | Refresh in-band before returning. |

Suggested per-operation:
- chitta — never stale by definition (memory is the source of truth). All tier 1 (or N/A).
- sangha — real-time; N/A.
- sutra — `read` ops: tier 2 (returning a function whose file changed is dangerous). `map`/`grep`/`outline`: tier 1.
- smriti — `read`: tier 2. `find`/`map`: tier 1. `scan`: self-heals by definition.
- kosha — `read`: tier 1 with caveat (segment text is the working copy). `search`: tier 1.

When tier 2 is in effect, the response should send the staleness signal *instead of* the content, not alongside it. This makes in-context anchoring structurally impossible.

---

## failure semantics

What happens when X is down or contended. Each fallback is classified:

- **secure-degraded** — reduced functionality, hard contracts intact.
- **insecure-emergency** — operator-acknowledged temporary mode that drops a hard contract; loud warning required; never a silent fallback.
- **prohibited** — refuse the operation; do not bypass the gate.

| Failing component | Caller | Behavior | Class |
|---|---|---|---|
| chitta down | `/done` | Skip session_summary write. Still write handoff. Log the gap. | secure-degraded |
| chitta down | `/reflect` | Abort. Cannot read observations. Surface to user. | secure-degraded |
| chitta down | normal session | Continue without memory; warn at session start. | secure-degraded |
| smriti down | sutra `read` of indexed file | **Refuse.** Direct-read bypass would skip the privacy gate. Return tier-2 error pointing at `manas health`. | prohibited |
| smriti down | kosha ingestion | Pause cursor; resume on smriti recovery. | secure-degraded |
| smriti scan in-flight | sutra `read` of recently-moved file | Sutra returns its as-of-now answer with `is_stale: true`; sideband sync resolves on next tick. | secure-degraded |
| sangha down | `/done` | Best-effort: write handoff without lock. Warn user about possible concurrent-write race. | secure-degraded |
| sangha lock TTL expired mid-`/reflect` | `/reflect` | Re-claim with a fresh idempotency check; if state shows another writer, abort. | secure-degraded |
| manas-cli sideband down | smriti path-move | Event queues in smriti; chitta updates lag until sideband recovers. | secure-degraded |
| mcpjungle down | normal session | **Refuse.** Per-server MCP fallback removes Tool Group ACL — minimal/rich boot is no longer enforceable. | prohibited |
| mcpjungle down | operator running `manas dev --no-gateway` | Per-server MCP config, banner warns that ACL is off, every tool call logs the bypass. | insecure-emergency |

This table is incomplete. It should grow as new failure modes are observed. New entries must declare a class; "fall back transparently" is not an option for anything that holds a hard contract.

---

## cost model

Every read operation is labelled with a cost tier. (Labels not yet enforced; intent stated here for adoption.)

| Cost | Examples |
|---|---|
| Cheap | `*_health`, `sangha_session_list`, `chitta_get_memory(by_id)` |
| Medium | `chitta_search_memories`, `sutra_grep`, `smriti_find` |
| Expensive | `sutra_impact`, `sutra_diff_impact`, `kosha_search` (vector), darshana cross-tier joins |

Per-call budget extends the existing `chitta.search_memories.max_tokens` parameter to all read tools. mcpjungle wires OTEL token instrumentation when a budget concept lands. Until then, the cost model is documentation, not enforcement.

---

## skills — the two-layer model

Skills are operations the agent performs (triggered by user, by schedule, or by the agent itself). Today they are markdown files in `~/.claude/commands-archive/` that the LLM reads and follows.

Going forward (post manas-cli phase), skills are **two-layer**:

- **Rust shell** in manas-cli. Handles lock lifecycle, transcript path injection, file IO, environment variables, output writing. Harness-agnostic — same shell whether the body is run by Claude, Gemini CLI, opencode, or a local model.
- **LLM body** — a prompt that any reasonably capable model can execute. The body does the *reasoning* (synthesize observations, decide which models to retire, summarize a session). It does not do *workflow* (claim lock, find transcript, write file).

The shell makes the skill model-agnostic and concurrency-correct. The body makes the skill cheap to evolve.

Implemented skills (markdown today, two-layer post-cli):
- `/done` — session shutdown. Stores observations missed during the session, generates session_summary in chitta, writes `docs/handoff.md`. Currently has a hardcoded `~/.claude/projects/...` transcript path; this becomes injected by the shell.
- `/reflect` — between-session maintenance. Pulls observations from chitta, groups by topic, synthesizes mental models. Currently does an N+1 search loop; should batch or upfront-load mental models.

---

## session lifecycle

### boot

CLAUDE.md loads. Tool Group ACL is bound by manas-cli (or the harness, when manas-cli isn't yet ground truth) to either `code`/`none` (minimal) or `full` (rich).

Minimal: health check, that's it.
Rich: read handoff, query chitta for context, surface sangha inbox, load mental models.

### run

Agent works on user tasks. During the session:
- Observations stored proactively (CLAUDE.md soft rule; load-bearing for /reflect input).
- Perception layers queried as needed (sutra for code, smriti for files, kosha for documents — once it ships).
- Chitta queried for context.

### shutdown — /done

1. (Future: shell) Claim sangha `handoff` lock via manas-cli.
2. (Body) Review session for missed observations.
3. (Body) Generate session summary.
4. (Future: shell) Write `docs/handoff.md`.
5. (Shell) Release sangha `handoff` lock; release transcript pointer.

### maintenance — /reflect

1. Shell claims sangha `reflect:user` lock.
2. Shell pulls un-consolidated observations from chitta (batch).
3. Shell pulls active mental models from chitta (batch — fix N+1).
4. Body groups observations by topic, synthesizes new/updated mental models.
5. Shell writes models, marks observations `consolidated_into: <model_id>`, releases lock.

---

## design principles for new components

These extend the chitta principles in `chitta/docs/principles.md` and apply system-wide. Consolidated source: `docs/principles.md`.

1. **Single responsibility.** One contract per subsystem. Don't make chitta a file indexer. Don't make smriti store decisions.
2. **Content-addressed over path-addressed.** Identity should survive moves and renames.
3. **Agent-native interface.** Token-efficient envelopes, semantic queries, structured responses. Not human CLI output reformatted for agents.
4. **No implicit state.** Every query includes its scope (profile, root, workspace). No "current directory" maintained server-side.
5. **Self-hosted and inspectable.** All data local. All indexes rebuildable. The human can understand what the system knows without going through an agent.
6. **Hard vs soft contracts named.** When you write a contract, say which it is. If hard, point at the enforcement. If soft, point at the fallback.
7. **Default-deny on read paths.** Allowlists, not denylists, for filesystem and document access.
8. **Freshness on every read.** `as_of` + `is_stale`. Per-operation response tier.

---

## open questions

- **Soft-delete in chitta.** Wire `invalidated_at` (planned in handoffs) into next migration and update `delete_memory` accordingly.
- **External refs schema.** Typed `external_refs` JSONB column on chitta memories — shape shared with yojana `context_refs` (see § cross-tier identity). Substrate gating item; lands before yojana ships and before darshana.
- **Mental-model retirement.** `metadata.retired_at` + `retirement_reason`. `search_memories` excludes retired by default.
- **Provenance/derivations.** Track which observations a mental model was synthesized from, in which session, with which prompt.
- **Observation eviction.** What happens to observations consolidated into a mental model? To old un-consolidated observations? At what density does summarization kick in?
- **Cost-model enforcement.** When does mcpjungle gate calls by budget? Today it's documentation only.
- **Cross-machine smriti / sangha.** Out of scope until real demand.
- **Yojana DB location.** Per-user (`~/.yojana/<slug>.db`) or per-repo (`<repo>/.yojana/index.db`). Lean per-user.
- **Darshana split.** Whether darshana ships as a single project or as two (interactive view + precomputed report).

---

## references

- Subsystem-specific docs: `chitta/docs/`, `smriti/docs/`, `sutra/docs/`, `sangha/docs/`, `kosha/docs/`, `yojana/docs/`.
- Roadmap: `docs/roadmap.md`.
- Principles: `docs/principles.md`.
- Active todo: `docs/todo.md`.
- Architecture review: `docs/arch-review-2026-05-03.md`.
- Binding-layer sketch: `manas-cli/docs/manas-binding-sketch.md`.
- Freshness envelopes: `manas-cli/docs/freshness-envelopes.md`.
