# Lessons ledger

Routing table of record for vidhi-reflect. Every accepted theme maps to exactly
one enforcement mechanism; every row carries the yojana task ids that evidence
it. A lesson with no mechanism is a blog post; a mechanism with no provenance
is folklore. Maintained by vidhi-reflect passes — rows are appended or
explicitly amended, never regenerated.

## Watermarks

| Scope | Last pass | Max completed_at mined |
|---|---|---|
| global | 2026-06-11 | 1781202790596 (2026-06-11T18:33:10Z) |

## Rows

| ID | Theme | Evidence | Tier | Mechanism | Status | Pass |
|---|---|---|---|---|---|---|
| L1 | SQLite write discipline: untransacted multi-statement replaces, stale long-lived FTS5 readers, cross-process read-modify-write with only per-process mutex | smriti/31, sutra/90, sutra/103, sutra/125, sutra/140, sutra/141, sutra/21, yojana/23 | (e)+(c) | `docs/lessons/sqlite-write-discipline.md` + pointer entry in manas-instructions `<engineering_lessons>` | live | 2026-06-11 |
| L2 | Correctness-gating state must be durable: in-memory flags lost on restart poison indexes; surviving Arc clones serve stale state; PID-alive ≠ socket-connectable; in-memory maps invisible cross-process | sutra/21, sutra/140, sutra/v1/30, panda/2, vidya/39 | (c) | manas-instructions `<engineering_lessons>` entry | live | 2026-06-11 |
| L3 | Silent-empty is a failure mode: extraction/refresh paths returning None/empty treated as "nothing here" — dropped symbols, zero call refs, `unwrap_or_default` preserving stale data, dropped literals, coarse serialization hiding divergence | sutra/38, sutra/119, sutra/126, sutra/67, sutra/103, vidya/39, fletch-astro/13 | (c) | manas-instructions `<engineering_lessons>` entry | live | 2026-06-11 |
| L4 | MCP/rmcp server gotchas: keep_alive default kills idle sessions, 401 without body/content-type misdiagnosed, `serde_json::Value` params produce any-type schemas clients stringify, notification status codes, SSE streams block SIGTERM | manas/22, chitta/9, chitta/46, manas-harness/7, panini/7 | (e) | `docs/lessons/mcp-server-discipline.md` + pointer entry in manas-instructions | live | 2026-06-11 |
| L5 | Adversarial review is a second design step: every reviewed wave across four projects surfaced high-severity findings implementation missed; twice the landed fix was itself wrong | sutra/21, sutra/19, sutra/46, sutra/62, sutra/67, sutra/103, sutra/133–140, chitta/40, chitta/44, yojana/22, yojana/23, yojana/26, vidya/24 | (g) | vidhi-review: "adversarial pass is load-bearing" section | live | 2026-06-11 |
| L6 | "Done" with pending work: tasks closed with unmerged branch, undeployed service, missing `.so`, incomplete verification wave — silent scope drift at close-out | yojana/32, yojana/33, justifier/1, swisseph.dart/2, aion/6 | (g) | capture_discipline (manas-instructions): close-out states merge/deploy status or files the follow-up | live | 2026-06-11 |
| L7 | Tests pin invariants, not seeded defaults: absolute counts of seed data and blanket suppressions break on scaffolding churn or silently absorb regressions | aion/30, fletch-astro/16 | (g) | vidhi-tdd checklist item | live | 2026-06-11 |
| L8 | SwissEph C-global state + frame discipline: globals drift across await points / Android resume; sidereal-vs-tropical and ecliptic-vs-equatorial confusion produced wrong padas and ayana bala; cross-engine sweeps need fine-grained factor serialization | innerorbits/9, swe-dashboard/2, fletch-astro/4, fletch-astro/5, fletch-astro/9, fletch-astro/13, fletch-astro/14, fletch-astro/16 | (e/d) | `docs/lessons/swisseph-state-discipline.md`, pointers in astrology repos' CLAUDE.md — family-scoped, not global | live | 2026-06-11 |
| L9 | Refactor contract drift: consolidation silently changed output semantics (violation counts post-waiver-partition, lost "unavailable" sentinels, freshness snapshot timing) | sutra/133, sutra/137, sutra/139 | (d) | sutra CLAUDE.md invariant note. Single-project so far — promote if it recurs elsewhere | live | 2026-06-11 |
| L10 | FTS adds nothing over dense+sparse retrieval: considered and benchmark-rejected twice (+0pp on top of BGE-M3 dense+sparse) | chitta/11, chitta/research/1 | ledger-only | negative knowledge — don't relitigate without new evidence | recorded | 2026-06-11 |
| L11 | Confirmation: pre-mortem catches plan errors before they become code ("no engine changes needed" was false; wrong suffix format; wrong trigger set and ordering) | panini/10, panini/13, panini/22 | ledger-only | confirms vidhi-premortem value; no change needed | recorded | 2026-06-11 |
| L12 | Confirmation: the cross-project SQLite theme was predicted from human memory before mining — reflect exists to make that noticing systematic | yojana/36 | ledger-only | — | recorded | 2026-06-11 |

## Maintenance notes

- A tier-(c) lesson that keeps recurring is not working — promote it to a more
  mechanical tier ((a)/(b)/(f)), don't write it louder.
- The `<engineering_lessons>` section in manas-instructions has a hard budget
  (~10 entries); adding over budget evicts the weakest entry to a playbook.
- Same graph-expressible theme recurring across ≥2 projects' rules.toml →
  file the global-rules feature on sutra (the escalation criterion from
  yojana/36).
- Capture-gap baseline at first pass (pre-discipline): 39/49 closed bugs
  without root_cause, 35/48 wontfix without rationale, 63 terminal tasks
  uncategorized. Judge yojana/38's gate against closures after 2026-06-11.
