# Lessons ledger

Routing table of record for vidhi-reflect. Every accepted theme maps to exactly
one enforcement mechanism; every row carries the yojana task IDs that evidence
it. Tier key: (a) sutra constraint · (b) sutra convention · (c) lessons store ·
(d) project CLAUDE.md · (e) playbook doc · (f) remediation tasks · (g) vidhi
skill delta.

Rows **L1–L12** were routed 2026-06-11 and live in the archived ledger
(`.handoffs/2026-06-17-ledger.md`, archived during the lessons-store migration,
sutra/164). They remain in force; recurrences are logged below, not renumbered.

## Recurrences against archived rows (2026-07-02 global pass)

| Row | Theme | New evidence | Action taken |
|---|---|---|---|
| L1 | SQLite write discipline | sutra/103, sutra/141, sutra/144, smriti/31 | re-cited lesson `019ed6cd-3ec9` (refreshes drifted anchor hashes) |
| L2 | Correctness-gating state must be durable | sutra/219, sutra/220, smriti/24, smriti/31, panda/2 | re-cited `019ed6cd-472d`. Recurring post-extraction — mostly in code predating the lesson; watch one more pass before escalating tier |
| L3 | Silent-empty is a failure mode | sutra/147, sutra/143, panini/2, panini/4, kosha/29, smriti/24, vidya/39, arjuna/quiver/10, swe-dashboard/7 | re-cited `019ed6cd-4e71`; heaviest recurrence in corpus → **escalated with playbook** `fail-loud-discipline.md` (L14) |
| L4 | MCP/rmcp server discipline | yojana/32, yojana/33, yojana/37 (token economy), sutra/216 (docstring/schema drift) | re-cited `019ed6cd-56cb`; playbook extended with rule 8 (response token economy) |
| L5 | Adversarial review is a second design step | sutra/123, /152, /162, /179, /218, arjuna/quiver/5, /8, /10, swe-dashboard/7, /11, swisseph-rs/62, /64, /69, /70, panini/22, /24 | 15+ new instances incl. a task closed with uncommitted code (swisseph-rs/70) → **escalated**: vidhi-implement §6 adversarial review gate before close (mechanism was only in vidhi-review before) |
| L8 | SwissEph C-global state | arjuna/quiver/9 (dlopen path-dedup shared globals across isolates → silently wrong results), swe-dashboard/2, innerorbits/9 | **escalated** from family-scoped (e/d) to store-surfaced (c): lesson `019f2537-01b8` pointing at `swisseph-state-discipline.md` |
| L9 | Refactor contract drift (was "promote if it recurs elsewhere") | sutra/123, sutra/135 | re-cited `019ed6cd-5ce9`. Still sutra-only — not promoted |

## New rows (2026-07-02 global pass)

| Row | Theme | Evidence | Tier | Mechanism | Status | Date |
|---|---|---|---|---|---|---|
| L13 | Instrument-first debugging for dual-implementation divergence (adopting ad-hoc stored lesson into ledger) | swisseph-rs/34, /35; cited: /72, /83, /86 | (c) | lesson `019f04e2` + `docs/golden-testing.md` (swisseph-rs) | cited | 2026-07-02 |
| L14 | Fail-loud discipline: error≠empty, distinct failure states kept distinct, startup posture (external deps degrade, internal invariants refuse) | panini/2, /4, /13, kosha/29, smriti/24, /26, adityas/backend/10, /12, arjuna/quiver/10, swe-dashboard/7 | (e) | `fail-loud-discipline.md`; L3's lesson points at it | written | 2026-07-02 |
| L15 | Prose ref-doc summaries insufficient for bit-exact porting (adopting ad-hoc stored lesson) | swisseph-rs/61, /64, /75, /79, /87 | (c) | lesson `019f1ff8` | cited | 2026-07-02 |
| L16 | Test as the real principal, not implementation-shaped fixtures (superuser conns masked GRANT gaps ×3; RS256 fixtures vs live ES256, reintroduced once; coarse gates passed by category-blind tests) | adityas/38, adityas/backend/16, /20, /21, adityas/15, panini/22–24, swisseph-rs/62, /64 | (c) | lesson `019f2536-eb1d` | stored | 2026-07-02 |
| L17 | Second fix of the same bug class ⇒ extract shared helper + regression test (tid_acc sentinel re-fixed ×4) | swisseph-rs/65, /66, /69, /81, sutra/123, /135 | (c) | lesson `019f2536-f4ea` | stored | 2026-07-02 |
| L18 | Docker egress is IPv4-default even on IPv6 hosts | adityas/backend/9, /14 | (c) | lesson `019f2537-0a5d` | stored | 2026-07-02 |
| L19 | Reverse-proxy client IP: peer IP is the proxy; XFF spoofable unless proxy overwrites | adityas/backend/10, adityas/15 | (c) | lesson `019f2537-154d` | stored | 2026-07-02 |
| L20 | Byte-index/window arithmetic panics on edge-sized input | kosha/19, panini/3 | (c) | lesson `019f2537-2053` | stored | 2026-07-02 |
| L21 | Comment-only invariants → encode in types/schema | smriti/27, kosha/19, swisseph-rs/17 | (c) | lesson `019f2537-2be4` | stored | 2026-07-02 |
| L22 | Test infrastructure deserves production scrutiny (golden generators, count literals) | swisseph-rs/41, /72, /78, /92, /97, sutra/217 | (c) | lesson `019f2537-36ad` | stored | 2026-07-02 |
| L23 | Baseline-diff a red suite instead of asserting "tests pass" (positive practice preserved) | swe-dashboard/5–14 | (c) | lesson `019f2537-3f93` | stored | 2026-07-02 |
| L24 | Backlogs rot after landmark architecture decisions; re-validate descriptions at execution start | swisseph-rs/4–14, vidhi/7 | (g) | vidhi-plan §1 re-validation step | written | 2026-07-02 |
| L25 | Watermarks: max completed_at of mined rows, never wall-clock | chitta/43 | (g) | vidhi-reflect §1 warning | written | 2026-07-02 |

## Deliberately not routed (2026-07-02 pass)

- Stale path references in persistent stores (manas/6, manas-harness/11) —
  mitigation already tracked as manas-cli/1; no new mechanism.
- Harness CLI config-isolation quirks (manas-harness/5, /8, /9) — knowledge
  lives in the adapter code itself.
- Sutra hub-spoke clustering topology lessons (sutra/196, /211–213) —
  project-specific, well-captured in its own task records.
- No (a)/(b) rows this pass: nothing graph-expressible or FCA-detectable
  emerged cleanly. The `.ok()`-swallowing pattern was considered for a (b)
  convention and rejected as too noisy to enforce mechanically; it lives under
  L3/L14.

## Store maintenance log

- **2026-07-02** (global pass): 0 pruned (store younger than decay window).
  5 verified lessons had drifted anchors; all resolved "still valid" via
  re-citation with workspace refresh. Deduped: archived `019f22fe` (goldens
  gitignored — explicitly superseded by `019f2303`); merged `019f1dc6` into
  `019f1dec` (swe_deltat_ex TIDAL_DEFAULT sentinel — anchors + citation moved,
  unique clause appended, duplicate archived).

## Capture-gap history

- **2026-07-02** (global pass, first run): ~35 bugs closed without root_cause,
  ~41 wontfix without rationale. Systemic: swe-dashboard/code-view (14/15 done
  tasks title-only), fletch-astro (bugs never categorized as bugs — fixes hide
  in enhancement execution_records). 15-item backfill triage presented and
  skipped by user (first skip; re-ask once at most, per skill). Close-time
  capture discipline (capture_discipline + yojana/40 CLI shorthand) is the
  forward fix; these are historical debt.
