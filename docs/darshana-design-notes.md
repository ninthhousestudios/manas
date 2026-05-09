# darshana — cross-tier analytical joins

Status: decided (2026-05-07)
Date: 2026-05-03 (notes), 2026-05-07 (decision)
Origin: extracted from a riff on a vibes-as-framework Reddit post about "Co-Relational Field Emergence" — bullets that, stripped of mysticism, named real engineering problems for the cross-tier join layer.

## decision: darshana is a feature area within manas-cli, not a separate subsystem

Darshana is a set of cross-tier analytical compound tools hosted by `manas serve`. It is not its own daemon or MCP server. Rationale:

- Darshana owns no data — it's pure cross-tier joins.
- By principle 9, cross-tier composition lives in manas-cli. Giving darshana its own server would require it to call into chitta, sutra, smriti, yojana — exactly the subsystem-to-subsystem coupling the architecture prohibits.
- Tools are prefixed `darshana_*` in MCP, distinguishing them from operational tools (`manas_health`, etc.).

**The boundary:** darshana tools are "give me understanding across tiers" (analytical joins). Other manas serve tools are "manage the machinery" (health, warm, passthrough). The darshana design principles (freshness envelopes, absence-as-result, token budgets, provenance) apply to darshana tools, not operational ones.

**Primary consumers:** agents, not humans. 91% of manas sessions already cross 2+ tiers (E2 experiment, 2026-05-07). Agents currently do a poor-man's darshana manually — sequential calls to chitta, sutra, yojana at session start. Darshana replaces that fan-out with joined tools.

**Build order:**
1. `darshana_impact` — cross-tier blast radius ("file X changed → which decisions/tasks/citations are stale?")
2. `darshana_orphans` — gap detection across tiers (broken refs, missing coverage)
3. `darshana_context` — joined session-start view (replaces manual boot fan-out)
4. `darshana_report` — precomputed summary (nightly or on-demand)

**Gating experiments (completed):**
- E1 (manas/6): 61% of chitta path refs resolve to real files. 39% breakage from historical repo moves (nhs/, ogham). Sideband daemon would prevent future breakage.
- E2 (manas/7): 91% of sessions touch 2+ tiers, 71% touch 3+. Most common combo: chitta+sangha+sutra+yojana. Cross-tier querying is the norm.

## design notes

Notes-to-future-self: things easy to forget when building, that will hurt to bolt on later.

---

## 1. joined freshness is its own envelope

Each tier already returns `as_of` and `is_stale`. Darshana's view spans tiers, so it needs a **joined envelope**:

```
{
  as_of: min(source.as_of for source in tiers_touched),
  is_stale: any(source.is_stale for source in tiers_touched),
  per_tier: { chitta: ..., smriti: ..., sutra: ..., kosha: ... },
  reconciliation_lag: now - last_join_pass_for_this_subject
}
```

A joined node is only as fresh as its stalest source. The "fresh" sense the agent gets from a darshana view is the *worst* of its inputs, not the average. Surface it that way.

`reconciliation_lag` is darshana's own freshness — how long since the join was last computed for this subject. It's separate from any source's freshness.

## 2. cross-tier impact is real (and is the killer query)

Sutra has `sutra_impact` — blast radius within code. Cross-tier impact is the equivalent across the federation:

> "If file X changes, which chitta decisions become potentially obsolete? Which yojana tasks get invalidated? Which kosha citations break? Which sutra symbols need re-review?"

This is `darshana_impact` and it's the single most valuable cross-tier query. Build it before pretty graph rendering. It's also the natural place to catch the "stale chitta decision references a moved file" failure mode.

## 3. absence is a first-class result

The view should *render* gaps, not hide them. Examples worth surfacing:

- chitta has decisions referencing a path smriti no longer indexes — **orphaned reference**
- sutra symbol has no observations in chitta about it — **silent code** (may or may not deserve attention)
- kosha citation points to a book smriti can't find — **broken citation**
- yojana task references a chitta memory that's been retired — **stale context_ref**

Don't filter these out as "no result." Return them as typed gap nodes. Half the value of the joined view is *what's missing*. The Reddit post called this "absence as presence"; we'd call it `darshana_orphans` or similar.

## 4. token budget across the join

Per-tier `max_tokens` is solved. The join blows up context if every tier's worst-case is summed. Darshana queries take a `max_tokens` that is the **total** budget, allocated across sub-queries by darshana's planner:

- cheap: chitta-only or smriti-only
- medium: two-tier join (chitta ↔ smriti)
- expensive: three-or-more-tier join, full graph rendering

Mark every darshana endpoint with its cost tier. Refuse expensive queries when the caller's budget can't cover them, rather than degrading silently.

## 5. provenance per node

Every node in a darshana result carries:

```
{
  tier: "chitta" | "smriti" | "sutra" | "kosha" | "yojana",
  id:   <native id in that tier>,
  as_of: <timestamp from that tier>,
  via:  [<edges traversed to reach this node>]
}
```

No anonymous joined facts. The agent should always be able to drill back to the source tier. This is also what makes darshana *honest* about what it knows vs what it inferred — which is the discipline graphify earned its keep through (`EXTRACTED | INFERRED | AMBIGUOUS` per edge).

## 6. convergence is a signal

`sutra_hotspots` finds files churning in code. Darshana's analog: subjects (concepts, paths, hashes, symbols) that **multiple sessions or skills** independently land on within a window. Three sessions in two weeks all touching the same chitta-smriti-sutra triangle = that triangle is hot.

This is the natural thing for `darshana-report` (the precomputed nightly report) to surface. Don't try to invent hotness; let it emerge from session-touch counts and let darshana count.

## 7. the view must be observable to itself

The moment-of-use bar from the original sketch was too soft (>1x/week, vibes). Bake measurement in from day one:

- every darshana endpoint logs `read_at` per subject, per session
- `darshana_health` reports: reads/day, unique-subjects/week, fraction of rich-boots that read the report
- if reads-per-day trends to zero over a month, darshana is failing its own use bar — **shelf it explicitly**, don't let it drift

This is the same instrumentation discipline manas applies to chitta and sutra. It is *not* surveillance; it is "did this thing earn its keep."

## 8. /reflect over the joined view

Today `/reflect` consolidates chitta observations into mental models. Once darshana exists, the natural extension:

> "Across the last month, decisions about subject Y cluster around files in directory Z, with N% of those files having changed since the decision was made."

This is reflection over the *joined* graph, not over chitta alone. It's the place mental-model retirement gets sharper — a mental model whose source observations are now orphaned (rule 3) is a strong retirement candidate.

This is harder than per-tier reflection. It's also more valuable. Don't try to do it in `/reflect` v1 — let `/reflect` over chitta stabilize first, *then* extend.

## 9. the report and the view are separate products

From the arch review: `darshana-report` (precomputed, nightly, read at rich boot) and `darshana-view` (interactive, `manas concept "X"`) have different cost profiles, freshness requirements, and failure modes. Don't try to ship them as one project. The report should ship first — it has clearer success criteria.

## 10. external_refs is the substrate

Reminder from the arch review and roadmap phase 0.2: chitta's `external_refs` typed column lands **before** any darshana work. Without it, every cross-tier join from chitta is a JSONB string-match. With it, the joins are typed lookups with explicit `as_of`. Darshana built on string-match will be wrong in subtle, intermittent ways and will never quite earn trust.

If darshana ships and `external_refs` doesn't, you've built the wrong thing. Don't let phase ordering slip on this one.

---

## what the riff named that we're *not* keeping

For posterity — these came from the Reddit post and were rejected:

- "Co-Relational Field Emergence" — has no operation. There is no field; there is a graph of typed nodes.
- "Background Hum → Empathy → Nurture → Intuition → Recognition" — five words trending warmer with no transition function. No state machine fits this.
- "Participatory Metaphysics" — buddhi without engineering. Discardable.
- "Reflexive Emergence By Reflective Resonance" — that's just `/reflect`. Adopt the boring name.

The riff is preserved in the session transcript; the operational kernels are above.

---

## graduation criteria — MET (2026-05-07)

E1 and E2 both completed. E2 decisively validates the premise (91% cross-tier sessions). E1 shows path infrastructure needs work (61% resolution) but the breakage is historical, not systemic. Decision: proceed with darshana. External_refs backfill and sideband daemon address the E1 weakness over time.
