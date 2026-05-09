# manas hub design

Status: draft
Date: 2026-05-06
Context: drops mcpjungle dependency, promotes manas-cli to the composed-tool MCP server described in `manas-architecture.md` section "manas-cli — ops surface."

---

## motivation

mcpjungle is a third-party Go MCP gateway. It proxies and namespaces tools from multiple upstream servers. What manas actually needs is not a proxy but an **orchestrator** — something that can implement `wake_up` by calling chitta and yojana internally and returning a merged result. mcpjungle can't do that; it just forwards.

The cost of keeping mcpjungle:
- Go binary in a Rust ecosystem, Docker overhead, its own database.
- Can't implement composed tools (wake_up, ingest, wrap_up).
- Tool Group ACL is the only hard-contract feature it provides, and we aren't using it yet.

The architecture doc already says manas-cli is the compound tool host. This design makes that real.

---

## topology

### before (mcpjungle)

```
Claude Code ──stdio──► sutra
             ──stdio──► smriti
             ──http───► mcpjungle ──► chitta (3100)
                                  ──► yojana (4200)
                                  ──► sangha (3200)
```

### after (manas hub)

```
Claude Code ──stdio──► manas serve  (composed tools: wake_up, ingest)
             ──stdio──► sutra       (code intelligence, per-project)
             ──stdio──► smriti      (filesystem perception)
             ──http───► chitta      (individual memory tools, 3100)
             ──http───► yojana      (individual task tools, 4200)

hooks ────────http───► chitta      (ingest endpoint, 3100)
```

Each service keeps its own MCP interface for individual tools. `manas serve`
only provides composed operations that span services. No proxying, no
namespacing, no double-hop latency on the common path.

sutra and smriti stay stdio because they're per-project/per-session. chitta
and yojana stay HTTP because they're long-running services with persistent
state.

---

## `manas serve`

New subcommand on the existing `manas` binary. Runs as a stdio MCP server
that Claude Code connects to directly.

### tools

#### `manas_wake_up`

Session-start context injection. Fans out to chitta + yojana, returns a
merged, token-budgeted preamble.

```
Input:
  project: string        — project name or path
  profile: string        — chitta profile (default: "chitta")
  max_tokens: int        — token budget for the preamble (default: 1500)

Internally:
  1. chitta search_memories(profile, query=project, k=20,
       memory_types=["decision", "observation", "mental_model"])
     — biased toward high-signal types, recency-weighted
  2. yojana query(project, states=["in_progress", "blocked", "ready"])
     — open tasks + blockers
  3. Merge, rank by relevance, truncate to token budget

Output:
  preamble: string       — formatted context block
  sources:               — what contributed
    memories: int
    tasks: int
  truncated: bool
```

The preamble format:

```
## memory context
- [decision] chose postgres over sqlite for concurrency (2026-04-26)
- [observation] BGE-M3 sparse vectors improve retrieval by 12% (2026-05-01)

## open tasks
- YJN-14 [in_progress] implement RRF sparse leg
- YJN-17 [blocked] waiting on chitta migration 0006
```

#### `manas_ingest`

Accept raw text for background extraction into chitta. Called by hooks, not
by the agent directly.

```
Input:
  text: string           — raw tool output, transcript chunk, etc.
  project: string        — project context for topic assignment
  profile: string        — chitta profile (default: "chitta")
  source: string         — where this came from ("hook:post", "hook:compact", etc.)

Internally:
  POST to chitta's ingest endpoint (see below)
  Chitta queues for background extraction

Output:
  accepted: bool
  queue_depth: int       — how many items waiting for extraction
```

### config

Extend `ManasConfig` with direct service URLs:

```rust
pub struct ManasConfig {
    pub manas_dir: PathBuf,
    pub chitta_url: String,    // default: http://127.0.0.1:3100
    pub yojana_url: String,    // default: http://127.0.0.1:4200
}
```

Drop `mcpjungle_url`. Drop `sangha_url` (deferred until real use case).

---

## chitta: ingest endpoint

New HTTP endpoint on chitta's existing HTTP server. Not an MCP tool — this
is a fire-and-forget write path for hooks.

```
POST /ingest
Content-Type: application/json

{
  "text": "...",
  "project": "my-project",
  "profile": "chitta",
  "source": "hook:post",
  "max_importance": "medium"
}

Response: 202 Accepted
{
  "queued": true,
  "queue_id": "uuid"
}
```

### extraction pipeline (background worker)

Runs in a tokio task, reads from an in-process queue (mpsc channel, not an
external message broker). Steps:

1. **Split** — break text into sentence-sized chunks. Handle URLs, file
   paths, version numbers, code fences. Simpler than ICM's 2000-line
   version — start with newline + period-after-space splitting, add
   refinements as needed.

2. **Classify** — score each chunk against anchor embeddings using BGE-M3
   (already loaded for chitta's search path). Anchors are short phrases
   representing memory types:
   - "a technical decision was made" → decision
   - "the user prefers or wants" → preference/observation
   - "an error occurred and was resolved" → observation
   - "a constraint or requirement was identified" → observation
   This replaces ICM's keyword scoring with semantic scoring, which is
   language-agnostic (BGE-M3 covers 100+ languages).

3. **Filter** — drop chunks below a similarity threshold. Drop LLM
   narration ("Let me check...", "I'll now read..."). Drop chunks that are
   too similar to recently ingested content (dedup window).

4. **Store** — call the existing `store_memory` internal path (not via MCP)
   with appropriate tags, memory_type, and importance. Cap importance at
   `max_importance` (hooks pass "medium" to prevent untrusted content from
   self-promoting to critical).

### principles alignment

- **P1 (verbatim is sacred):** the extracted chunk is stored as-is. No
  rewriting, no summarization.
- **P3 (write fast, enrich lazily):** ingest returns 202 immediately.
  Extraction runs in background. Never blocks a response.
- **P6 (idempotent writes):** each extracted chunk gets an idempotency key
  derived from `hash(text_chunk + project + source)`. Re-ingesting the same
  hook output is a no-op.
- **P9 (no write-time extraction until it wins a benchmark):** this is the
  exception that earns its way in. The benchmark is practical: does
  auto-extraction improve session-start context quality vs agent-only
  storage? Measure before v0.1.0 ships.

---

## hooks

Three hooks, matching ICM's layer model. All are thin shell scripts that
POST to chitta's ingest endpoint.

### hook 0: PostToolUse

Fires after every tool call. Sends tool output to ingest.

```bash
#!/bin/bash
# .claude/hooks/chitta-post.sh
# Fires on PostToolUse, sends tool output to chitta ingest

TOOL_NAME="$1"
OUTPUT=$(cat)

# Skip noisy tools
case "$TOOL_NAME" in
  sutra_map|sutra_outline|sutra_grep|smriti_scan) exit 0 ;;
esac

# Skip small outputs (likely not interesting)
if [ ${#OUTPUT} -lt 100 ]; then exit 0; fi

PROJECT=$(basename "$(pwd)")

curl -s -X POST http://127.0.0.1:3100/ingest \
  -H "Content-Type: application/json" \
  -d "$(jq -n \
    --arg text "$OUTPUT" \
    --arg project "$PROJECT" \
    --arg source "hook:post:$TOOL_NAME" \
    '{text: $text, project: $project, profile: "chitta", source: $source, max_importance: "medium"}'
  )" > /dev/null 2>&1 &
```

### hook 1: Compact (PreCompact / NotificationSubtype)

Fires before context compression. Sends the about-to-be-compressed
transcript to ingest so knowledge isn't lost.

```bash
#!/bin/bash
# .claude/hooks/chitta-compact.sh
TRANSCRIPT=$(cat)
PROJECT=$(basename "$(pwd)")

curl -s -X POST http://127.0.0.1:3100/ingest \
  -H "Content-Type: application/json" \
  -d "$(jq -n \
    --arg text "$TRANSCRIPT" \
    --arg project "$PROJECT" \
    --arg source "hook:compact" \
    '{text: $text, project: $project, profile: "chitta", source: $source, max_importance: "medium"}'
  )" > /dev/null 2>&1 &
```

### hook 2: SessionStart

Fires at session start. Calls `manas_wake_up` (or directly hits chitta +
yojana) and injects context.

This hook is the one place where the agent doesn't need to "know" to search
— context arrives automatically.

---

## what's deferred

- **Tool Group ACL.** Without mcpjungle, there's no hard enforcement of
  minimal vs rich boot. For now, all sessions are rich. ACL can be added to
  `manas serve` later if needed — it controls which tools it exposes based
  on a boot-mode flag.
- **Sangha integration.** Session coordination is deferred until there's a
  real multi-agent use case.
- **`manas_wrap_up` tool.** Session-end composed tool (store summary to
  chitta, update tasks in yojana). The `/done` skill handles this today via
  agent cooperation. Convert to a composed tool when the skill's soft
  contract proves unreliable.
- **Proxy mode.** `manas serve` does not proxy individual chitta/yojana
  tools. If the number of MCP servers becomes a problem, add optional
  proxying later. Five servers (manas, sutra, smriti, chitta, yojana) is
  manageable.

---

## implementation order

1. **chitta ingest endpoint** — HTTP endpoint + background extraction worker.
   This is useful immediately, even without hooks (can be tested via curl).
2. **Hooks** — PostToolUse and Compact hooks that POST to ingest.
3. **`manas serve`** — MCP server with `manas_wake_up`.
4. **Refactor manas-cli** — drop mcpjungle references, update config, update
   `warm` and `done` to use direct service URLs.
5. **Benchmark** — measure wake_up context quality and auto-extraction
   signal-to-noise vs current agent-only storage.

---

## references

- `docs/manas-architecture.md` — overall architecture (manas-cli as compound
  tool host is described there).
- `chitta/docs/icm-steal-list.md` — comparison with ICM, what to adopt.
- `chitta/docs/principles.md` — chitta's foundational principles (extraction
  must align with P1, P3, P6, P9).
