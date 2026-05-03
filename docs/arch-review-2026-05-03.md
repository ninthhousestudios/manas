# manas — high-level architecture review

Date: 2026-05-03
Reviewer: Claude (Opus 4.7)
Inputs read: `manas-architecture.md`, `manas-binding-sketch.md`, `roadmap.md`, `freshness-envelopes.md`, `gemini.md`, repo layout, current subsystem status.

This is the high-level review the gemini.md critique was *supposed* to be but wasn't. Gemini's critique read like a code review wearing an architecture-review costume — it caught real bugs (hardcoded paths, schema/skill drift, lock lifecycle, N+1 in /reflect) but didn't engage the actual architecture. This doc tries to.

---

## what's working

Before tearing into things, the parts that are genuinely strong:

1. **The framing of "subsystem with a contract" is doing real work.** Each tier (chitta, smriti, sutra, kosha, sangha) has a one-sentence contract that you can hold someone to. That discipline alone is rare. Most projects at this stage have one giant blob that "does memory and search and indexing."

2. **`darshana before prajna` is exactly right.** Defer the knowledge graph until you can name the question naive joins fail at. This is the single best decision in the architecture and you should not let it slip when prajna becomes seductive again.

3. **Bi-temporal modeling in chitta** (event_time + record_time, invalidated_at, memory_contradictions) is the right shape for a system that wants to retract beliefs without amnesia. Most "agent memory" projects don't reach this for years.

4. **Content-addressed identity in smriti** (BLAKE3 hashes, not paths) is the only way the rest of the system survives the user moving files around. Don't ever let path-as-identity creep back in under "convenience."

5. **Two boot modes (minimal + rich)** is a real insight. Most agent systems force-load context whether you want it or not, which silently biases blind work like code reviews.

These are not throw-away compliments. The architecture has spine. The critique below is harsher because it has somewhere to land.

---

## the central tension

> *"Subsystems don't call each other. The agent orchestrates all interactions."* — manas-architecture.md, rule 1

This is the most consequential design decision in the system, and it's the source of most of its open problems. Pull on it and a lot of things move.

What this principle buys:
- Subsystems are independently deployable, testable, swappable.
- No hidden coupling. Every interaction is visible in the LLM's transcript.
- Failure of one subsystem can't cascade through synchronous calls into another.

What this principle costs:
- **The LLM becomes the concurrency manager** (gemini's #3 — and gemini was right).
- **The LLM becomes the join planner** (gemini's #8, and the entire reason darshana exists).
- **Every cross-tier operation costs tokens and inference time**, paid in latency and dollars per call.
- **Every cross-tier operation can fail in non-deterministic ways** the system can't observe — the LLM "forgets" step 3, hallucinates a value, drops a lock release.

The roadmap already concedes the principle in three places without naming the concession:

1. **darshana** is a join layer — i.e. an admission that the agent doing joins isn't good enough.
2. **sideband daemon (manas-cli phase 4.6)** for "smriti→chitta path-move notifications" is literally subsystem-to-subsystem IPC, just routed through a daemon you own.
3. **mcpjungle** as the gateway is the place compound tools will eventually live.

So in practice the principle is "subsystems don't call each other, **except** when they do, in which case the call goes through a thing manas owns." That's a fine principle. But it should be stated that way. The current framing reads as absolute and then erodes by exception.

**Recommendation.** Reword rule 1: *"Subsystems don't call each other directly. Cross-tier coordination flows through one of two named seams: (a) the agent (default), or (b) the manas-cli sideband (when the operation is deterministic, frequent, or must not depend on LLM cooperation)."* Then make the sideband a first-class subsystem in the architecture doc, not a bullet under phase 4. This is the design decision; treat it as one.

---

## the kernel that isn't a kernel

`CLAUDE.md` is described as "kernel config." It's not. A kernel enforces boundaries; CLAUDE.md is a suggestion the LLM will mostly follow. The OS metaphor invites you to reason about CLAUDE.md as if it had teeth, and it doesn't.

This matters because several pieces of the design quietly assume CLAUDE.md is enforcing things:

- "The agent learns how to use each subsystem from CLAUDE.md" — the agent learns from CLAUDE.md *if it loads, parses, and complies with* CLAUDE.md, all of which are probabilistic.
- The boot sequence is described as "the agent does X, then Y" — but the agent will sometimes skip X, do Y first, or invent Z. There's no kernel panic when it does.
- The proactive-observation rule lives in CLAUDE.md. It works *most of the time*, but you have no way to measure compliance.

The fix isn't to delete the metaphor — it's useful. The fix is to be explicit about which guarantees the system actually holds and which are best-effort:

| Guarantee type | Where it's enforced |
|---|---|
| Hard (cannot be violated) | Subsystem code. Schema constraints. mcpjungle ACL. CLI lock lifecycles. |
| Soft (LLM cooperation required) | CLAUDE.md rules. Skill markdown. Observation discipline. |

Anything in the "hard" column gets to assume the contract holds. Anything in the "soft" column needs a fallback for when the LLM doesn't cooperate. The architecture currently doesn't make this distinction, so it sometimes treats soft contracts as hard ones (the lock lifecycle is the canonical example).

---

## identity, and why it's the real binding problem

The binding-layer sketch worries about *concept* identity across tiers. It should worry first about *referential* identity, which is a strictly easier problem the system already has and hasn't solved.

Five identity systems coexist:

| Tier | Identity |
|---|---|
| smriti | BLAKE3 content hash |
| sutra/qartez | qualified symbol name (path:symbol) |
| chitta | UUID + freeform `metadata` JSONB + tag strings |
| kosha | book + page tuple |
| sangha | connection-bound session UUID |

The cross-tier joins darshana wants are:

- "memories about this file" → chitta JSONB string-matched against smriti path
- "decisions that touched this code" → chitta JSONB string-matched against sutra path
- "what's inside this PDF" → smriti hash matched against kosha hash

Notice the pattern: every join from chitta to anything else is a **JSONB string match**. That's not a join, it's grep-with-extra-steps. It will:

- Miss when the path was renamed (smriti tracks the move; the chitta string doesn't update).
- Miss when the metadata was written casually (`"file": "thing.rs"` vs `"path": "/full/path/thing.rs"`).
- False-positive on substrings.
- Be impossible to validate without running the join.

Before darshana ships, chitta needs a first-class **external reference** column. Something like:

```
external_refs: jsonb  -- [{type: "smriti:hash", value: "...", as_of: ...}, ...]
```

with a typed schema enforced by the API, and an index. This is small. It is much smaller than darshana itself. And without it, darshana is rendering a graph whose edges are *guesses*, not references.

This is the architectural change that would make Gemini's #5 (use `memory_contradictions` instead of tag-based supersession) feel small by comparison. **Get the references right or the binding layer is built on sand.**

---

## freshness envelopes are honest but insufficient

The freshness-envelopes principle is correct in spirit. Servers should be honest about their age. But the principle as written outsources the response to the caller, and the caller is the LLM, and the LLM is bad at this (Gemini's #4 was right, even if its proposed fix was hand-wavy).

Three tiers of response to staleness exist. The principle should pick which goes where, not silently default everything to tier 1.

| Tier | Behavior on `is_stale=true` |
|---|---|
| 1. Announce | Return the stale data with a flag. Caller decides. |
| 2. Refuse | Return an error and require the caller to trigger a refresh. |
| 3. Self-heal | Refresh in-band before returning. |

For each subsystem, ask: which tier?

- **chitta** is never stale by definition — fine.
- **sangha** state is real-time — fine.
- **sutra/qartez**: should probably be tier 2 or 3 for `read`-shaped operations (you read a function whose file changed; returning the old function with a flag is dangerous). Tier 1 is fine for `map`/`grep` (overview operations are tolerant of staleness).
- **smriti** for `read`: tier 2 (refuse + tell user/agent to scan). For `find`/`map`: tier 1 is fine.

The principle doc should specify per-operation, not per-subsystem. Also: **if a tool returns is_stale=true, it should not also return content the LLM might anchor on**. Send the staleness signal *instead of* the content, not alongside it. This makes the in-context-anchoring failure mode structurally impossible.

---

## what the model-agnosticism debate is actually about

Roadmap principle 10 is annotated with Josh's disagreement: he wants harness-agnosticism, the principle says CC-first. The annotation has been there since whenever, and the system continues to bake in CC assumptions. This is a smell.

The real question isn't "model-agnostic vs CC-first." It's: **where do skills live?**

Today: skills are markdown in `~/.claude/commands-archive/` (or wherever), loaded by the harness, executed by the LLM reading prose instructions and calling MCP tools. This is CC-shaped because:

- The skill *is* a prompt that depends on a particular harness's loading model.
- Skill steps are LLM instructions, not code, so they can fail/skip/loop in ways code can't.
- Lock lifecycles, transcript paths, and several other things are CC-specific environment.

Three coherent positions exist. Pick one.

1. **Stay CC-first.** Delete the principle 10 annotation, accept that skills are markdown, accept that retargeting another harness is a port not a config change. Cheapest. Honest.

2. **Skills become Rust in manas-cli.** A skill is a Rust function that orchestrates LLM calls (via whatever harness adapter), claims sangha locks, reads transcripts via an injected path, calls chitta/smriti/sutra. The LLM is invoked for *reasoning* (synthesize observations into a model) but not for *workflow* (claim lock, read file, write file, release lock). This is what gemini's #3 was actually pointing at. It's invasive. It's the right move if model-agnosticism is non-negotiable.

3. **Two-layer skills.** A skill has a Rust shell (lock lifecycle, file IO, environment) and an LLM body (the reasoning). The shell is harness-agnostic; the body is a prompt that any reasonably capable model can execute. This is probably the actual answer.

Whichever you pick, the current state ("CC-first, but I disagree, but I haven't changed it") accumulates technical debt against a decision that won't stick. It's worth a focused session to resolve.

---

## what's missing entirely from the architecture

These are not bugs. They are absences I noticed by reading every doc and finding nothing.

### 1. cost model

The architecture has zero mention of token economics. With four tiers all queryable on every turn, plus a binding layer planned, an unbounded "agent orchestrates" model is going to blow up context windows on real workloads. Today this is invisible because sessions are short and the system is small. In six months it won't be.

You need at least:
- A budget concept on read calls (chitta has `max_tokens`; extend to all subsystems).
- A cost label on each subsystem read (cheap/medium/expensive).
- A doc that says what the agent should do when budget is exhausted.

Without this, the system silently degrades into "LLM ran out of context, made things up."

### 2. failure semantics

"Degrade gracefully" is listed as principle 4 of component interaction and then never specified. What actually happens when:

- chitta is down during /reflect? (the skill cannot read observations or write models — abort? skip? queue?)
- smriti is mid-scan when sutra reads a file that just got moved? (race window — what does sutra return?)
- sangha lock TTL expires mid-`/reflect` because the LLM stalled on something?
- the manas-cli sideband daemon is down when smriti detects a move?

Each of these has a "right answer" but the architecture doc doesn't pick one. They will be picked ad-hoc during implementation, which means they'll be picked inconsistently.

### 3. provenance / epistemic chain of custody

Mental models in chitta are generated by an LLM from observations also generated by an LLM. The `memory_contradictions` table tracks supersession, but nothing tracks **derivation**: "this mental model was synthesized from observations [a, b, c] in session [X] using prompt [Y]."

This matters more than it sounds. When a mental model turns out to be wrong, you want to be able to ask: "what observations led to this, and are they actually wrong, or did the synthesis go bad?" Without provenance you can only retire models, not learn from them.

A `derivations` table — model_id, [observation_ids], session_id, skill_name, prompt_hash — would make /reflect epistemically auditable. It's also useful raw material for the eventual prajna pipeline.

### 4. observation eviction

Mental models have a retirement protocol. Observations don't. Today there are dozens. In a year there will be tens of thousands. The N+1 in /reflect (gemini's #8) becomes lethal when the table is large; even batch_search_memories will degrade.

You need a story for:
- Observations consolidated into a mental model — keep but mark `consolidated_into: <model_id>`. Excluded from /reflect's working set.
- Old un-consolidated observations — periodically demoted/archived/summarized.
- Observation density per topic — at some point the right move is "we have 200 observations about X, summarize them into 1 then drop the originals."

This is a chitta-side concern but the architecture should commit to *some* answer before chitta v0.0.4 ships.

### 5. what the user can read directly

Principle 11 ("self-hosted and inspectable") is named but no doc says how. If the user wants to see all observations from yesterday without going through an agent, what do they do? `psql`? Is there a `chitta show` CLI? A web UI?

This isn't a feature request. It's a question about whether the system actually honors its own principle. Right now it doesn't, in any concrete way.

---

## the binding sketch — a sharper version

The darshana-before-prajna decision is right. But the sketch conflates two things that should be separated:

1. **A view.** Interactive, on-demand, queried per-user-action. `manas concept "Saturn"` returns the joined surface for that concept.
2. **A report.** Precomputed, periodic, consumed at session start. `MANAS_REPORT.md` shows god-concepts, surprising joins, suggested questions.

These have different cost profiles, different freshness requirements, different failure modes, and probably different implementations. The sketch treats them as two surfaces of the same project. They're not. The view depends on live joins; the report depends on a snapshot. You'd happily ship one without the other.

Suggestion: split darshana into **darshana-view** (interactive joins) and **darshana-report** (precomputed). Build the report first — it's smaller, has clearer success criteria, and a periodic process that runs nightly is much easier to validate than an interactive surface that needs to render in <100ms.

Also: the moment-of-use bar ("user opens it >1x/week") is too soft. If you're going to enforce graduation criteria you need a measurement plan, and there isn't one. Either decide how you're going to measure usage from day one, or replace the metric with something observable (e.g., "MANAS_REPORT.md is read by the agent in N% of rich boots over a month").

---

## the missing experiment before darshana

Before building darshana, two cheap experiments would derisk the whole binding effort. They are weeks of work each. Neither is in the roadmap.

### Experiment 1: how clean are the chitta references?

Audit every chitta memory's `metadata` JSONB. Of the ones that mention a file path, what fraction:
- Resolve to a real file today?
- Resolve to a file smriti has indexed?
- Survived the last three weeks of file moves?

If the answer is "30% resolve, 10% survived a move," then naive joins won't work even for the easy cases. That tells you the `external_refs` column needs to land before darshana, not after.

### Experiment 2: how often do sessions need cross-tier queries?

Scan `.sessions/*.jsonl` transcripts for the last month. Count: how many sessions made tool calls to two or more tiers about the same subject? If the answer is "almost never," the binding layer's audience doesn't exist yet. Build it later, or build it smaller.

Both are one-shot scripts. Run them before phase 4 starts.

---

## the bookkeeping: principles fragmentation

There are now three principle lists in three docs:

- `chitta/docs/principles.md` — 11 principles, chitta-specific.
- `manas-cli/docs/manas-architecture.md` — 5 design principles for new components.
- `manas-cli/docs/roadmap.md` — 11 principles "from opus 4.7 review, accepted."

These overlap. They contradict in places (principle 10 in roadmap is annotated as disagreed-with). They're going to drift.

Promote a single `docs/principles.md` at the manas root that owns the cross-cutting principles. Subsystem-specific principles stay in their subsystem's doc. The roadmap should reference, not duplicate.

---

## summary — what would I do next, in order

1. **Resolve principle 10.** One session. Pick CC-first or commit to harness-agnostic. The annotation is debt.
2. **Run the two experiments above.** A weekend each. They will tell you whether to build `external_refs` before darshana, and whether to build darshana at all.
3. **Add `external_refs` to chitta.** Small schema change. Big payoff. Prerequisite for credible joins.
4. **Move skill workflow shells to manas-cli (Rust).** Lock lifecycles, transcript paths, file IO. LLM is invoked only for reasoning. This is the deepest of gemini's points and the most invasive fix.
5. **Specify failure semantics per cross-tier operation.** A short table in manas-architecture.md. What happens when X is down and Y is called.
6. **Cost model + budget concept.** Before phase 3 (mcpjungle), so the gateway can enforce.
7. **Principles consolidation.** A single source. Cite from elsewhere.
8. **Per-operation freshness response tier.** Tier 1 vs tier 2 vs tier 3 specified explicitly.
9. **Provenance for mental models.** `derivations` table. Lands with chitta v0.0.4.
10. **Observation eviction story.** Land before chitta has 10k observations, not after.

Items 1, 3, 5, 6 are architectural decisions — cheap to make now, expensive to retrofit. The rest can land incrementally.

---

## what I might be wrong about

- **Skills-in-Rust** (#4 above) might be premature. If you actually never adopt another harness, the markdown skills are simpler. The honest version of this question is "how confident am I that I'll want gemini/opencode parity in the next 12 months?" If the answer is <60%, stay markdown.
- **The cost model** might not matter at single-user scale. It will matter the moment you put another agent (autonomous, scheduled, or another human) into the system. Today that's hypothetical.
- **External refs** might be solvable with conventions instead of schema (always use `path` key, always store full path). Conventions are cheap until they aren't. Schema is enforced.
- **Splitting darshana into view + report** might be over-engineering. If the report turns out to be a side-effect of building the view, fine. But starting from "build both as one project" tends to ship neither.

This review is opinionated. Push back where it deserves push-back.
